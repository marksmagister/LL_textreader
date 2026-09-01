"""Plain text -> a lesson and its token stream.

The only place lessons are written. Lemmatisation happens here, once, and the
result is stored; opening a lesson is then a DB join and nothing else.
"""

import sqlite3
import unicodedata

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


def import_text(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    lang: str,
    text: str,
    title: str | None = None,
    source: str | None = None,
) -> int:
    body = clean(text)
    adapter = get_adapter(lang)
    tokens: list[AnalysedToken] = adapter.analyse(body)

    cur = conn.execute(
        "INSERT INTO lesson (user_id, lang, title, source, body, pipeline_id) VALUES (?,?,?,?,?,?)",
        (user_id, lang, title or derive_title(body), source, body, adapter.pipeline_id),
    )
    lesson_id = int(cur.lastrowid)
    conn.executemany(
        "INSERT INTO token (lesson_id, idx, surface, norm, lemma, pos,"
        " char_start, char_end, sent_id, morph, confidence)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
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
                t.confidence,
            )
            for t in tokens
        ],
    )
    return lesson_id
