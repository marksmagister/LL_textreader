"""What one account is allowed to cost.

Open signup means the people using this are no longer people the maintainer
chose, so every action that costs real money or real time needs a ceiling. Not
because anyone is expected to attack it — because an unbounded thing on a two-vCPU
box with 128 GB of disk is one bored script away from being everyone's problem.

Two kinds of ceiling, and they answer different questions:

- a **rate**: how often, per hour. Stops a script hammering the tagger or the
  translator, or making the box fetch a thousand URLs.
- a **cap**: how much, ever. Stops one account quietly filling the disk.

Deliberately plain. Fixed hourly windows rather than a sliding log, so state is
one small row per account per action per hour instead of one row per request. The
known cost of that choice: someone timing a burst across a window boundary can
briefly get through twice the limit. For keeping a bot from ruining the box that
is entirely good enough, and a sliding window is several times the code.

The numbers are constants here rather than settings. `CLAUDE.md` is explicit —
no config key until something real needs to differ — and nothing does yet. They
are set where a real reader will never meet them: importing forty texts in an
hour is not reading, it is loading a library.
"""

from __future__ import annotations

import sqlite3

from fastapi import HTTPException

# action -> how many times an hour. See the module docstring for the reasoning.
PER_HOUR = {
    # Runs the tagger over the whole text. The expensive one.
    "import": 40,
    # Makes *the server* fetch a URL somebody typed. Costs our IP reputation as
    # well as our time, so it is the tightest of the three.
    "fetch": 30,
    # Loads a 300MB model on first use and is slow every time after.
    "translate": 60,
    # A text field open to anyone signed in (0010).
    "report": 20,
    # The core loop: one per word judged. A long session is a few hundred, so
    # this is set well above the most anyone could read and still be reading.
    "term": 3000,
    # One per page turn, plus the odd repeat.
    "finish": 600,
}

# Absolute ceilings per account.
MAX_LESSONS = 500  # ≈ 27 MB at the measured 53.5 kB a lesson (0016)
MAX_TEXT_CHARS = 2_000_000  # one very long book, and about 30s in the tagger


class Overused(HTTPException):
    """429. Says which action and roughly when to come back."""

    def __init__(self, action: str, limit: int) -> None:
        super().__init__(
            429,
            f"too many {action} requests — the limit is {limit} an hour."
            " Wait for the hour to turn and try again.",
        )


def check_rate(conn: sqlite3.Connection, user_id: int, action: str) -> None:
    """Count this request against the account's hourly allowance, or refuse it.

    Counts first and refuses second, deliberately: a refused request has still
    cost us the work of handling it, so a caller hammering the endpoint should
    not get a free reset by being refused.
    """
    limit = PER_HOUR[action]
    used = conn.execute(
        """
        INSERT INTO rate_limit (user_id, action, window, n)
        VALUES (?, ?, strftime('%Y-%m-%dT%H', 'now'), 1)
        ON CONFLICT(user_id, action, window) DO UPDATE SET n = n + 1
        RETURNING n
        """,
        (user_id, action),
    ).fetchone()[0]
    # Committed immediately, and this line is load-bearing. `with connect()`
    # rolls back when the block raises, so refusing a request used to undo the
    # very increment that refused it: the counter sat at 1 however many times you
    # were turned away, and hammering the endpoint was free. The same applies to
    # a request that fails later for its own reasons — an attempt that cost us
    # work counts, whether or not it produced anything.
    conn.commit()
    if used > limit:
        raise Overused(action, limit)


def sweep_rates(conn: sqlite3.Connection) -> int:
    """Drop windows that have passed. Nothing reads them and they only accumulate."""
    cur = conn.execute(
        "DELETE FROM rate_limit WHERE window < strftime('%Y-%m-%dT%H', 'now', '-2 hours')"
    )
    return cur.rowcount


def check_lesson_cap(conn: sqlite3.Connection, user_id: int) -> None:
    """Is there room for another lesson in this account?"""
    n = conn.execute("SELECT COUNT(*) FROM lesson WHERE user_id = ?", (user_id,)).fetchone()[0]
    if n >= MAX_LESSONS:
        raise HTTPException(
            409,
            f"this account already holds {n} lessons, which is the limit."
            " Delete some, or export and start fresh.",
        )


def check_text_size(text: str) -> None:
    """Refuse a text before the tagger spends a minute on it."""
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(
            413,
            f"that text is {len(text):,} characters and the limit is"
            f" {MAX_TEXT_CHARS:,}. Import it in parts.",
        )
