"""Signing in and out.

Four endpoints, and the only ones in the app that work without a session.
"""

import secrets

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from .. import google
from ..auth import (
    COOKIE,
    CurrentUser,
    User,
    close_session,
    create_user,
    open_session,
    optional_user,
    room_for_another,
    user_for_google,
)
from ..config import settings
from ..db import connect
from ..starters import give_starters

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Carries the CSRF state and the PKCE verifier between /start and /callback.
# A cookie rather than a table: the value only has to survive one redirect, and
# it is compared against what Google hands back rather than trusted on its own,
# so there is nothing to sign and no row to clean up.
FLOW = "ll_oauth"
FLOW_SECONDS = 600


def _set_cookie(response: Response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        # Lax, not Strict: the return from Google is a cross-site navigation
        # into this app, and Strict would drop the cookie exactly there.
        samesite="lax",
        path="/",
    )


@router.get("/me")
def me(request: Request) -> dict:
    """Who is signed in, if anyone. The only endpoint the front end may call blind.

    Answers 200 with a null user rather than 401, because "nobody is signed in"
    is a normal answer to this question and not an error.
    """
    user = optional_user(request)
    with connect() as conn:
        space = room_for_another(conn)
    return {
        "user": None
        if user is None
        else {"id": user.id, "name": user.name, "email": user.email, "picture": user.picture},
        "google": settings.google_configured,
        "signup": space,
        "languages": settings.language_list,
    }


@router.get("/google/start")
def start(lang: str = "fr") -> RedirectResponse:
    """Send the browser to Google. `lang` is what they chose to learn."""
    if not settings.google_configured:
        raise HTTPException(503, "google sign-in is not configured on this server")
    if lang not in settings.language_list:
        raise HTTPException(400, f"not a language this server has: {lang!r}")

    state = secrets.token_urlsafe(24)
    verifier = google.make_verifier()
    response = RedirectResponse(google.authorize_url(state, verifier), status_code=302)
    _set_cookie(response, FLOW, f"{state}:{verifier}:{lang}", FLOW_SECONDS)
    return response


def _fail(message: str) -> RedirectResponse:
    """Back to the front page, with something it can show.

    A redirect rather than a JSON error because this endpoint is reached by the
    browser navigating, not by fetch — a 400 here would show the reader a bare
    error page with no way back.
    """
    response = RedirectResponse(f"/?error={message}", status_code=302)
    response.delete_cookie(FLOW, path="/")
    return response


@router.get("/google/callback")
def callback(request: Request, code: str = "", state: str = "", error: str = ""):
    """Google sends the reader back here."""
    if error:
        # They pressed cancel on the consent screen. Not a fault.
        return _fail("cancelled")

    flow = request.cookies.get(FLOW, "")
    expected, _, rest = flow.partition(":")
    verifier, _, lang = rest.partition(":")
    # compare_digest is not needed: this is our own cookie against our own
    # parameter, and an attacker who could read either has already won.
    if not expected or not state or state != expected:
        # Either the cookie expired while they sat on the consent screen, or
        # somebody else built this URL and handed it to them.
        return _fail("expired")
    if not code:
        return _fail("nocode")

    try:
        identity = google.exchange(code, verifier)
    except google.GoogleError:
        return _fail("google")

    with connect() as conn:
        user = user_for_google(conn, identity.sub)
        if user is None:
            if not room_for_another(conn):
                return _fail("full")
            user = create_user(
                conn,
                sub=identity.sub,
                name=identity.name,
                email=identity.email,
                picture=identity.picture,
            )
            conn.execute(
                "UPDATE user SET lang = ? WHERE id = ?",
                (lang if lang in settings.language_list else "fr", user.id),
            )
            # Nobody should meet an empty library on their first visit.
            give_starters(conn, user.id, lang or "fr")
        token = open_session(conn, user.id)

    response = RedirectResponse("/", status_code=302)
    _set_cookie(response, COOKIE, token, settings.session_days * 86400)
    response.delete_cookie(FLOW, path="/")
    return response


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, user: User = CurrentUser) -> None:
    """Sign out. Deletes the row, so it ends everywhere rather than just here."""
    token = request.cookies.get(COOKIE)
    if token:
        with connect() as conn:
            close_session(conn, token)
    response.delete_cookie(COOKIE, path="/")
