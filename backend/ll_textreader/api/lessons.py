"""Lessons: import one, list them, read one, finish one."""

import sqlite3

from fastapi import APIRouter, HTTPException

from ..db import USER_ID, connect
from ..importers.plain_text import import_text
from ..models import (
    FinishRequest,
    ImportRequest,
    LessonDetail,
    LessonSummary,
    ReaderToken,
    state_for,
)
from ..nlp.languages import UnknownLanguage

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

# Roughly a screenful of prose. Pages break between sentences, so this is a
# target, not a limit — a page overshoots rather than cutting a sentence.
PAGE_TOKENS = 150


def _pages(conn: sqlite3.Connection, lesson_id: int) -> list[tuple[int, int]]:
    """Token ranges, one per page, packed greedily and broken between sentences.

    Derived, not stored: reading position is a token index, so changing PAGE_TOKENS
    reflows the book without losing anyone's place.
    """
    sents = conn.execute(
        "SELECT MIN(idx) AS lo, MAX(idx) AS hi, COUNT(*) AS n FROM token"
        " WHERE lesson_id = ? GROUP BY sent_id ORDER BY sent_id",
        (lesson_id,),
    ).fetchall()
    pages: list[tuple[int, int]] = []
    run = 0
    for s in sents:
        if not pages or run + s["n"] > PAGE_TOKENS:
            pages.append((s["lo"], s["hi"]))
            run = s["n"]
        else:
            pages[-1] = (pages[-1][0], s["hi"])
            run += s["n"]
    return pages or [(0, 0)]


def _resume(pages: list[tuple[int, int]], last_token: int) -> int:
    """The first page you haven't finished."""
    return next((i for i, (_, hi) in enumerate(pages) if hi > last_token), len(pages) - 1)


# n_words counts lexical tokens only; COUNT(col) skips NULL lemmas.
_SUMMARY = """
SELECT l.id, l.lang, l.title, l.source, l.pipeline_id, l.imported_at, l.body,
       COUNT(t.idx) AS n_tokens, COUNT(t.lemma) AS n_words,
       COALESCE(p.last_token, 0) AS last_token,
       COALESCE(p.completed, 0) AS completed
FROM lesson l
LEFT JOIN token t ON t.lesson_id = l.id
LEFT JOIN reading_progress p ON p.lesson_id = l.id AND p.user_id = l.user_id
WHERE l.user_id = ?
"""

# The whole product: the stored token stream joined against your lexicon.
# Overrides win over the pipeline (CLAUDE.md rule 5).
_TOKENS = """
SELECT t.idx, t.surface, t.char_start, t.char_end, t.sent_id,
       COALESCE(o.to_lemma, t.lemma) AS lemma,
       COALESCE(o.to_pos, t.pos)     AS pos,
       s.status,
       f.surface IS NOT NULL         AS form_seen
FROM token t
LEFT JOIN lemma_override o
       ON o.user_id = ? AND o.lang = ? AND o.surface = t.norm
LEFT JOIN lemma_status s
       ON s.user_id = ? AND s.lang = ?
      AND s.lemma = COALESCE(o.to_lemma, t.lemma)
      AND s.pos   = COALESCE(o.to_pos, t.pos)
LEFT JOIN form_seen f
       ON f.user_id = ? AND f.lang = ?
      AND f.lemma = COALESCE(o.to_lemma, t.lemma)
      AND f.pos   = COALESCE(o.to_pos, t.pos)
      AND f.surface = t.norm
WHERE t.lesson_id = ? AND t.idx BETWEEN ? AND ?
ORDER BY t.idx
"""


def _lesson_row(conn: sqlite3.Connection, lesson_id: int) -> sqlite3.Row:
    row = conn.execute(f"{_SUMMARY} AND l.id = ? GROUP BY l.id", (USER_ID, lesson_id)).fetchone()
    if row is None or row["id"] is None:
        raise HTTPException(404, "no such lesson")
    return row


@router.post("", response_model=LessonSummary, status_code=201)
def create_lesson(req: ImportRequest) -> LessonSummary:
    """Import plain text. Tokenising and lemmatising happen here, once."""
    with connect() as conn:
        try:
            lesson_id = import_text(
                conn,
                user_id=USER_ID,
                lang=req.lang,
                text=req.text,
                title=req.title,
                source=req.source,
            )
        except UnknownLanguage:
            raise HTTPException(400, f"no adapter for language {req.lang!r}") from None
        except OSError as exc:  # spaCy model not downloaded
            raise HTTPException(503, f"language model unavailable: {exc}") from None
        row = _lesson_row(conn, lesson_id)
    return LessonSummary(**{k: row[k] for k in LessonSummary.model_fields})


@router.get("", response_model=list[LessonSummary])
def list_lessons() -> list[LessonSummary]:
    with connect() as conn:
        rows = conn.execute(
            f"{_SUMMARY} GROUP BY l.id ORDER BY l.imported_at DESC, l.id DESC", (USER_ID,)
        ).fetchall()
    return [LessonSummary(**{k: r[k] for k in LessonSummary.model_fields}) for r in rows]


@router.get("/{lesson_id}", response_model=LessonDetail)
def read_lesson(lesson_id: int, page: int | None = None) -> LessonDetail:
    """One page, resuming where you stopped unless a page is named."""
    with connect() as conn:
        row = _lesson_row(conn, lesson_id)
        lang = row["lang"]
        pages = _pages(conn, lesson_id)
        page = _resume(pages, row["last_token"]) if page is None else page
        page = max(0, min(page, len(pages) - 1))
        lo, hi = pages[page]
        tokens = conn.execute(_TOKENS, (USER_ID, lang) * 3 + (lesson_id, lo, hi)).fetchall()

        # Slice from this page's first token to the next page's first, so the
        # whitespace and punctuation between them isn't dropped.
        start = tokens[0]["char_start"] if tokens else 0
        if page == 0:
            start = 0
        end = len(row["body"])
        if page + 1 < len(pages):
            nxt = conn.execute(
                "SELECT char_start FROM token WHERE lesson_id = ? AND idx = ?",
                (lesson_id, pages[page + 1][0]),
            ).fetchone()
            end = nxt["char_start"] if nxt else end

    return LessonDetail(
        **{k: row[k] for k in LessonSummary.model_fields},
        page=page,
        n_pages=len(pages),
        body=row["body"][start:end],
        body_offset=start,
        tokens=[
            ReaderToken(
                idx=t["idx"],
                surface=t["surface"],
                lemma=t["lemma"],
                pos=t["pos"],
                char_start=t["char_start"],
                char_end=t["char_end"],
                sent_id=t["sent_id"],
                state=state_for(t["lemma"], t["status"], bool(t["form_seen"])),
            )
            for t in tokens
        ],
    )


@router.delete("/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int) -> None:
    with connect() as conn:
        _lesson_row(conn, lesson_id)
        conn.execute("DELETE FROM lesson WHERE id = ? AND user_id = ?", (lesson_id, USER_ID))


@router.post("/{lesson_id}/finish", response_model=LessonSummary)
def finish_lesson(lesson_id: int, req: FinishRequest) -> LessonSummary:
    """You've read a page.

    Records which inflections you've now met on it, saves your place, and — with
    mark_rest_known — turns everything still blue on that page known. That is the
    pressure valve from CLAUDE.md rule 8: without it the reader is unusable above
    beginner level. Scoped to the page, so words you clear here are already known
    when you turn to the next one.
    """
    with connect() as conn:
        row = _lesson_row(conn, lesson_id)
        lang = row["lang"]
        pages = _pages(conn, lesson_id)
        page = max(0, min(req.page, len(pages) - 1))
        lo, hi = pages[page]

        if req.mark_rest_known:
            # Blue words only: those with no row, and those explicitly set back to
            # new. A word you are learning (1-4) stays learning — you decided that
            # about it, and this button must not quietly undo the decision. Ignored
            # (-1) and known (5) are likewise left alone.
            conn.execute(
                """
                INSERT INTO lemma_status (user_id, lang, lemma, pos, status)
                SELECT DISTINCT ?, ?, t.lemma, t.pos, 5 FROM token t
                WHERE t.lesson_id = ? AND t.idx BETWEEN ? AND ? AND t.lemma IS NOT NULL
                ON CONFLICT(user_id, lang, lemma, pos) DO UPDATE
                    SET status = 5, updated_at = datetime('now')
                    WHERE lemma_status.status = 0
                """,
                (USER_ID, lang, lesson_id, lo, hi),
            )
        # Every form of a word you know that appeared on this page has now been met,
        # so it stops being highlighted as novel next time.
        conn.execute(
            """
            INSERT INTO form_seen (user_id, lang, lemma, pos, surface, "count")
            SELECT ?, ?, t.lemma, t.pos, t.norm, COUNT(*)
            FROM token t JOIN lemma_status s
              ON s.user_id = ? AND s.lang = ? AND s.lemma = t.lemma AND s.pos = t.pos
            WHERE t.lesson_id = ? AND t.idx BETWEEN ? AND ?
              AND t.lemma IS NOT NULL AND s.status = 5
            GROUP BY t.lemma, t.pos, t.norm
            ON CONFLICT(user_id, lang, lemma, pos, surface) DO UPDATE
                SET "count" = form_seen."count" + excluded."count"
            """,
            (USER_ID, lang, USER_ID, lang, lesson_id, lo, hi),
        )
        # Save the place. Never move it backwards: rereading an early page
        # shouldn't lose the fact that you'd got to chapter nine.
        conn.execute(
            """
            INSERT INTO reading_progress (user_id, lesson_id, last_token, completed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, lesson_id) DO UPDATE
                SET last_token = MAX(reading_progress.last_token, excluded.last_token),
                    completed = MAX(reading_progress.completed, excluded.completed),
                    updated_at = datetime('now')
            """,
            (USER_ID, lesson_id, hi, int(page + 1 >= len(pages))),
        )
        row = _lesson_row(conn, lesson_id)
    return LessonSummary(**{k: row[k] for k in LessonSummary.model_fields})
