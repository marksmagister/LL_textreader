"""Plain text -> a lesson and its token stream.

The only place lessons are written. Lemmatisation happens here, once, and the
result is stored; opening a lesson is then a DB join and nothing else.
"""

import sqlite3
import unicodedata

from ..counts import refresh
from ..models import AnalysedToken
from ..nlp.languages import get_adapter

TITLE_MAX = 80


def clean(text: str) -> str:
    """Normalise just enough that offsets are stable. This becomes `lesson.body`."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")
    # NFC so that composed and decomposed accents can't produce different offsets
    # for the same-looking French text.
    return unicodedata.normalize("NFC", text).strip()


def derive_title(body: str) -> str:
    first = next((ln.strip() for ln in body.splitlines() if ln.strip()), "Untitled")
    return first if len(first) <= TITLE_MAX else first[: TITLE_MAX - 1].rstrip() + "…"


def with_title(body: str, title: str | None) -> str:
    """Put the title into the text, unless it is already the first line.

    A title is text you are reading: it should be coloured, clickable, and count
    toward what you know. When you paste an article the headline is part of what
    you paste and this does nothing; it only matters when the title arrived
    separately, from the title box or a filename or a web page's <title>.
    """
    if not title:
        return body
    first = body.lstrip().split("\n", 1)[0].strip()
    return body if first.casefold() == title.strip().casefold() else f"{title}\n\n{body}"


def import_text(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    lang: str,
    text: str,
    title: str | None = None,
    source: str | None = None,
) -> int:
    body = with_title(clean(text), title)
    adapter = get_adapter(lang)
    tokens: list[AnalysedToken] = adapter.analyse(body)

    cur = conn.execute(
        "INSERT INTO lesson (user_id, lang, title, source, body, pipeline_id) VALUES (?,?,?,?,?,?)",
        (user_id, lang, title or derive_title(body), source, body, adapter.pipeline_id),
    )
    lesson_id = int(cur.lastrowid)
    _insert_tokens(conn, lesson_id, tokens)
    return lesson_id


def _insert_tokens(conn: sqlite3.Connection, lesson_id: int, tokens: list[AnalysedToken]) -> None:
    conn.executemany(
        "INSERT INTO token (lesson_id, idx, surface, norm, lemma, pos,"
        " char_start, char_end, sent_id, morph)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                lesson_id,
                t.idx,
                t.surface,
                t.norm,
                t.lemma,
                t.pos,
                t.char_start,
                t.char_end,
                t.sent_id,
                t.morph,
            )
            for t in tokens
        ],
    )


def reprocess(conn: sqlite3.Connection, lesson_id: int, force: bool = False) -> bool:
    """Re-run the pipeline over a stored lesson. False if it was already current.

    The body is untouched, so the lexicon — which is keyed on lemma, not lesson —
    survives completely. What does move is token numbering, and with it anyone's
    saved place. So positions are converted to character offsets first and snapped
    back afterwards, which is the same trick an edit-and-re-import will need.
    """
    row = conn.execute(
        "SELECT lang, body, pipeline_id FROM lesson WHERE id = ?", (lesson_id,)
    ).fetchone()
    adapter = get_adapter(row["lang"])
    # `force` is for when the body changed rather than the pipeline — an edit, or
    # a title being folded into the text. The stamp is the same; the stream is not.
    if not force and row["pipeline_id"] == adapter.pipeline_id:
        return False

    where_they_were = {
        p["user_id"]: (
            conn.execute(
                "SELECT char_end FROM token WHERE lesson_id = ? AND idx = ?",
                (lesson_id, p["last_token"]),
            ).fetchone()
            or {"char_end": 0}
        )["char_end"]
        for p in conn.execute(
            "SELECT user_id, last_token FROM reading_progress WHERE lesson_id = ?",
            (lesson_id,),
        )
    }

    tokens = adapter.analyse(row["body"])
    conn.execute("DELETE FROM token WHERE lesson_id = ?", (lesson_id,))
    _insert_tokens(conn, lesson_id, tokens)
    conn.execute("UPDATE lesson SET pipeline_id = ? WHERE id = ?", (adapter.pipeline_id, lesson_id))
    # The tokens are all new, so the library's cached counts were computed over
    # rows that no longer exist.
    refresh(conn, [lesson_id])

    for user_id, offset in where_they_were.items():
        idx = next(
            (t.idx for t in tokens if t.char_end >= offset),
            tokens[-1].idx if tokens else 0,
        )
        conn.execute(
            "UPDATE reading_progress SET last_token = ? WHERE lesson_id = ? AND user_id = ?",
            (idx, lesson_id, user_id),
        )
    return True


def stale(conn: sqlite3.Connection) -> list[int]:
    """Lessons whose token stream a model or rule change has left behind."""
    out = []
    for row in conn.execute("SELECT id, lang, pipeline_id FROM lesson ORDER BY id"):
        try:
            if row["pipeline_id"] != get_adapter(row["lang"]).pipeline_id:
                out.append(row["id"])
        except Exception:  # noqa: BLE001 - a language whose model isn't installed
            continue
    return out


def _main() -> None:
    """`python -m ll_textreader.importers.plain_text [--dry-run]`."""
    import sys

    from ..db import connect, init_db

    init_db()
    with connect() as conn:
        ids = stale(conn)
        if not ids:
            print("every lesson is current")
            return
        if "--dry-run" in sys.argv:
            print(f"{len(ids)} stale lesson(s): {ids}")
            return
        for lesson_id in ids:
            reprocess(conn, lesson_id)
            print(f"reprocessed lesson {lesson_id}")


if __name__ == "__main__":
    _main()
