"""The Google half of signing in. Authorization code flow, exchanged server-side.

Small on purpose, and the two things it does *not* do are the interesting ones.

**No JWT library, and no signature check.** Signature verification exists for ID
tokens that reach you through a browser, where anybody could have written them.
Ours arrives in the body of a TLS response from Google's token endpoint, to a
request we made, authenticated with our own client secret — the channel is the
proof, and Google documents this exemption for exactly this flow. What we do
check is `aud`, so a token minted for a different application cannot be replayed
at us. That removes a dependency, a JWKS cache, and every key-rotation bug.

**No HTTP library.** Thirty lines of urllib against one endpoint, matching what
importers/from_url.py already decided for the same reason.

If this ever has to work without reaching Google at sign-in time, local
verification against the JWKS is the swap, and it is the only thing that changes.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .config import settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# openid/email/profile are Google's *non-sensitive* scopes, which is what lets
# this app publish to production without going through verification. Adding
# anything else to this list changes that, and is not a small decision.
SCOPES = "openid email profile"

TIMEOUT = 15


class GoogleError(Exception):
    """Google refused, or answered with something unusable."""


@dataclass(frozen=True)
class Identity:
    sub: str
    email: str | None
    name: str
    picture: str | None


def make_verifier() -> str:
    """PKCE code verifier: a high-entropy string we keep and Google never sees."""
    return secrets.token_urlsafe(48)


def challenge_for(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def authorize_url(state: str, verifier: str) -> str:
    """Where to send the browser."""
    query = urllib.parse.urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "state": state,
            "code_challenge": challenge_for(verifier),
            "code_challenge_method": "S256",
            # Ask for an account each time rather than silently reusing whichever
            # one the browser is already signed into. On a shared machine the
            # silent version signs you in as somebody else's Google account.
            "prompt": "select_account",
        }
    )
    return f"{AUTH_URL}?{query}"


def _claims(id_token: str) -> dict:
    """The payload of a JWT, without verifying its signature. See the module docstring."""
    parts = id_token.split(".")
    if len(parts) != 3:
        raise GoogleError("malformed id_token")
    payload = parts[1]
    # base64url without padding, which is how JWTs are written.
    payload += "=" * (-len(payload) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoogleError(f"unreadable id_token: {exc}") from None


def _post(url: str, fields: dict[str, str]) -> dict:
    data = urllib.parse.urlencode(fields).encode("ascii")
    req = urllib.request.Request(  # noqa: S310 — a constant https URL, not user input
        url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:  # noqa: S310
            return json.loads(resp.read(1 << 20))
    except urllib.error.HTTPError as exc:
        # Google puts the actual reason in the body, and it is the difference
        # between "your clock is wrong" and "that redirect URI is not registered".
        detail = exc.read(4096).decode("utf-8", "replace")
        raise GoogleError(f"google said {exc.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GoogleError(f"could not reach google: {exc}") from None
    except json.JSONDecodeError as exc:
        raise GoogleError(f"google answered with something that is not JSON: {exc}") from None


def exchange(code: str, verifier: str) -> Identity:
    """Trade the one-time code for an identity."""
    if not settings.google_configured:
        raise GoogleError("google sign-in is not configured on this server")
    payload = _post(
        TOKEN_URL,
        {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": verifier,
        },
    )
    token = payload.get("id_token")
    if not token:
        raise GoogleError("no id_token in google's answer")
    claims = _claims(token)

    # The one check that matters: a token minted for another application must not
    # be usable here. Everything else about the token is guaranteed by the fact
    # that it came back over TLS from the request we just made.
    if claims.get("aud") != settings.google_client_id:
        raise GoogleError("that token was issued for a different application")
    sub = claims.get("sub")
    if not sub:
        raise GoogleError("no subject in google's answer")

    # An unverified address is one Google has not proved belongs to the person.
    # We never key on the address, so this is not load-bearing for security — but
    # storing one that might belong to someone else would be a lie in the UI.
    email = claims.get("email") if claims.get("email_verified") else None
    return Identity(
        sub=str(sub),
        email=email,
        name=str(claims.get("name") or "").strip(),
        picture=claims.get("picture"),
    )
