"""The texts a language starts with.

An empty library is a bad first page: there is nothing to read, and nothing to
show what the colours are for. So each language ships a few short texts written
for the purpose — not excerpts, because this repo ships no third-party text
(NOTICE) — and one press puts them in your library.

They are files rather than rows, for the reason in `decisions/0006`: text belongs
in files, the lexicon belongs in SQLite. One file per lesson, first line is the
title, and the folder it sits in is the collection it lands in:

    starters/<lang>/<collection>/NN-slug.txt

The number orders them, and it is the only thing the filename is for — the title
comes out of the text.
"""

import sqlite3
from pathlib import Path

from .importers.plain_text import import_text

DIR = Path(__file__).with_name("starters")


def available(lang: str) -> list[tuple[str, str, str]]:
    """(collection, title, body) for each starter text, in reading order."""
    out = []
    for folder in sorted(p for p in (DIR / lang).glob("*") if p.is_dir()):
        for path in sorted(folder.glob("*.txt")):
            body = path.read_text(encoding="utf-8").strip()
            title = body.split("\n", 1)[0].strip()
            out.append((folder.name, title, body))
    return out


def missing(conn: sqlite3.Connection, user_id: int, lang: str) -> list[tuple[str, str, str]]:
    """The starters you don't already have.

    By title, so deleting one and pressing again brings it back, and pressing
    twice does nothing. A lesson you imported yourself that happens to share a
    title counts as having it — that is the right answer for a button whose whole
    job is not to make duplicates.
    """
    have = {
        r["title"]
        for r in conn.execute(
            "SELECT title FROM lesson WHERE user_id = ? AND lang = ?", (user_id, lang)
        )
    }
    return [s for s in available(lang) if s[1] not in have]


def install(conn: sqlite3.Connection, user_id: int, lang: str) -> list[int]:
    """Import the missing starters, as ordinary lessons in a collection.

    Ordinary on purpose: they go through the same importer, the same pipeline and
    the same tables as anything you paste, so there is no second kind of lesson
    to reason about and deleting one is just deleting a lesson.
    """
    done = []
    for collection, title, body in missing(conn, user_id, lang):
        lesson_id = import_text(conn, user_id=user_id, lang=lang, text=body, title=title)
        conn.execute(
            "INSERT OR IGNORE INTO collection (user_id, lang, title) VALUES (?,?,?)",
            (user_id, lang, collection),
        )
        cid = conn.execute(
            "SELECT id FROM collection WHERE user_id=? AND lang=? AND title=?",
            (user_id, lang, collection),
        ).fetchone()["id"]
        position = conn.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 FROM lesson WHERE collection_id = ?", (cid,)
        ).fetchone()[0]
        conn.execute(
            "UPDATE lesson SET collection_id = ?, position = ? WHERE id = ?",
            (cid, position, lesson_id),
        )
        done.append(lesson_id)
    return done
