"""Who is reading: sessions, invites, and the dependency every route hangs on.

Identity comes from Google (`google.py`); what lives here is everything that
stays true whoever issues it. That split is deliberate — invites decide *who gets
in*, which is a different question from how they prove who they are, and only the
second half would change if a password ever arrived alongside Google.

The one rule worth restating from docs/decisions/0013: there is no fallback user.
A route that forgets to depend on `current_user` gets no user at all rather than
silently reading user 1's vocabulary.
"""

from __future__ import annotations

import argparse
import secrets
import sqlite3
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

from .config import settings
from .db import connect, init_db

COOKIE = "ll_session"

# Everything a route needs to know about who is asking. Deliberately not the
# database row: routes want an id, and passing the row around invites someone to
# start reading `google_sub` in a query.
@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str | None
    picture: str | None


def _row_to_user(row: sqlite3.Row) -> User:
    return User(id=row["id"], name=row["name"], email=row["email"], picture=row["picture"])


# ---------------------------------------------------------------- sessions


def open_session(conn: sqlite3.Connection, user_id: int) -> str:
    """Start a session and return its token. The caller sets the cookie."""
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO session (token, user_id) VALUES (?,?)", (token, user_id))
    return token


def close_session(conn: sqlite3.Connection, token: str) -> None:
    """Sign out. Deleting the row is what makes this real rather than decorative."""
    conn.execute("DELETE FROM session WHERE token = ?", (token,))


def user_for_session(conn: sqlite3.Connection, token: str) -> User | None:
    """The signed-in user, or None if the token is unknown or has gone stale.

    Expiry is checked in SQL rather than by sweeping on a timer: a swept-but-not-
    yet-run session would still authenticate, and there is no schedule to get
    wrong. The sweep still happens, opportunistically, to stop the table growing.
    """
    row = conn.execute(
        """
        SELECT u.id, u.name, u.email, u.picture
        FROM session s JOIN user u ON u.id = s.user_id
        WHERE s.token = ? AND s.seen_at > datetime('now', ?)
        """,
        (token, f"-{settings.session_days} days"),
    ).fetchone()
    if row is None:
        return None
    conn.execute("UPDATE session SET seen_at = datetime('now') WHERE token = ?", (token,))
    return _row_to_user(row)


def sweep_sessions(conn: sqlite3.Connection) -> int:
    """Delete sessions nobody has used in a long time."""
    cur = conn.execute(
        "DELETE FROM session WHERE seen_at <= datetime('now', ?)",
        (f"-{settings.session_days} days",),
    )
    return cur.rowcount


# ---------------------------------------------------------------- the dependency


def current_user(request: Request) -> User:
    """Every route that touches user data depends on this. 401 if nobody is in.

    The connection is opened and closed here rather than shared with the route:
    one extra open per request against a local SQLite file is not a cost worth a
    request-scoped connection, and the routes each manage their own transaction.
    """
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "not signed in")
    with connect() as conn:
        user = user_for_session(conn, token)
    if user is None:
        raise HTTPException(401, "not signed in")
    return user


# The annotation routes actually write. `user: CurrentUser` reads better than
# repeating Depends() sixteen times, and it is one name to change if the
# dependency ever needs arguments.
CurrentUser = Depends(current_user)


def optional_user(request: Request) -> User | None:
    """For the two places that must answer whether or not anyone is signed in."""
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    with connect() as conn:
        return user_for_session(conn, token)


# ---------------------------------------------------------------- users


def user_for_google(conn: sqlite3.Connection, sub: str) -> User | None:
    row = conn.execute(
        "SELECT id, name, email, picture FROM user WHERE google_sub = ?", (sub,)
    ).fetchone()
    return _row_to_user(row) if row else None


def create_user(
    conn: sqlite3.Connection, *, sub: str, name: str, email: str | None, picture: str | None
) -> User:
    cur = conn.execute(
        "INSERT INTO user (name, google_sub, email, picture) VALUES (?,?,?,?)",
        (name or email or "reader", sub, email, picture),
    )
    return User(id=int(cur.lastrowid), name=name, email=email, picture=picture)


def count_users(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM user").fetchone()[0])


# ---------------------------------------------------------------- the command


def room_for_another(conn: sqlite3.Connection) -> bool:
    """Is there space under the cap? Signing up is refused when there is not.

    Existing readers are unaffected — this gates creation, never sign-in, so
    filling up cannot lock out the people already using it.
    """
    if settings.signup != "open":
        return False
    return count_users(conn) < settings.max_users


# ---------------------------------------------------------------- the command


def _main() -> None:
    """`python -m ll_textreader.auth users` — who has an account, and since when."""
    parser = argparse.ArgumentParser(prog="ll_textreader.auth")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("users", help="list accounts")
    sub.add_parser("sweep", help="delete long-unused sessions")
    args = parser.parse_args()

    init_db()
    with connect() as conn:
        if args.cmd == "sweep":
            print(f"deleted {sweep_sessions(conn)} stale sessions")
            conn.commit()
            return
        rows = conn.execute(
            "SELECT id, name, email, created_at FROM user ORDER BY id"
        ).fetchall()
        if not rows:
            print("no accounts yet")
        for r in rows:
            print(f"{r['id']:>3}  {r['name']:<24} {r['email'] or '':<32} {r['created_at']}")
        print(f"\n{len(rows)} of {settings.max_users} places used")


if __name__ == "__main__":
    _main()
