"""The lessons a new reader starts with, so nobody meets an empty library.

Given once, at sign-up, in the language they chose. They are ordinary lessons
afterwards: theirs, editable, deletable. Nothing here re-runs or tops anyone up.

**Every starter must be text this project wrote.** `CLAUDE.md` draws the line at
hosting other people's copyrighted text, and `NOTICE` promises the repository
ships no third-party data — an excerpt from a novel or a news article in this
directory would break both, quietly, in a file nobody looks at twice. Original
prose only, however plain.

The second French text is doing a job beyond being readable: it deliberately
reuses the first one's vocabulary in shapes the reader has not met — `revenu`,
`dormait`, `prendra`, `ouvriront`. Open it after finishing the first and it is
already half-legible, with the unmet forms outlined rather than solid. That is
the argument for the whole lemma-keyed model, visible on a page nobody has
touched yet.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .counts import refresh
from .importers.plain_text import import_text
from .nlp.languages import UnknownLanguage

STARTERS = Path(__file__).with_name("starters")


def texts_for(lang: str) -> list[tuple[str, str]]:
    """(title, body) for each starter, in filename order. The title is line one."""
    folder = STARTERS / lang
    if not folder.is_dir():
        return []
    out = []
    for path in sorted(folder.glob("*.txt")):
        title, _, body = path.read_text(encoding="utf-8").partition("\n")
        if body.strip():
            out.append((title.strip(), body.strip()))
    return out


def give_starters(conn: sqlite3.Connection, user_id: int, lang: str) -> int:
    """Import the starter lessons for this reader. Returns how many landed.

    Never raises. A missing language model or a broken text file must not be the
    thing that stops somebody signing up — they would be left with no account and
    an error, when the honest outcome is an account and an empty library.
    """
    made = []
    for title, body in texts_for(lang):
        try:
            made.append(import_text(conn, user_id=user_id, lang=lang, text=body, title=title))
        except (UnknownLanguage, OSError, sqlite3.Error):
            continue
    refresh(conn, made)
    return len(made)
