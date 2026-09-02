"""Lessons: import one, list them, read one, finish one."""

import json
import sqlite3

from fastapi import APIRouter, HTTPException

from ..counts import refresh, refresh_for_words
from ..db import USER_ID, connect
from ..importers import from_url
from ..importers.from_url import BadUrl
from ..importers.plain_text import clean, import_text
from ..models import (
    CollectionRequest,
    FetchRequest,
    FinishRequest,
    ImportRequest,
    LessonDetail,
    LessonSummary,
    ReaderToken,
    state_for,
)
from ..nlp.languages import UnknownLanguage
from ..translate import Unavailable, glosses_for

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

# The fields that come from a row of _SUMMARY. undo_id/undo_n are set by an
# action, not stored, so they must not be looked for in the row.
DB_FIELDS = [f for f in LessonSummary.model_fields if not f.startswith("undo")]

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
       l.n_tokens, l.n_words,
       COALESCE(p.last_token, 0) AS last_token,
       COALESCE(p.completed, 0) AS completed,
       p.updated_at AS last_read,
       l.collection_id, l.position, c.title AS collection,
       -- how much of this lesson you can already read. Counted over tokens, not
       -- distinct lemmas, so it matches what the page looks like.
       l.n_new, l.n_learning, l.n_known
FROM lesson l
LEFT JOIN reading_progress p ON p.lesson_id = l.id AND p.user_id = l.user_id
LEFT JOIN collection c ON c.id = l.collection_id
WHERE l.user_id = ?
"""

# The whole product: the stored token stream joined against your lexicon.
# Overrides win over the pipeline (CLAUDE.md rule 5).
_TOKENS = """
SELECT t.idx, t.surface, t.char_start, t.char_end, t.sent_id, t.morph,
       COALESCE(o.to_lemma, t.lemma) AS lemma,
       COALESCE(o.to_pos, t.pos)     AS pos,
       s.status,
       f.surface IS NOT NULL         AS form_seen,
       o.surface IS NOT NULL         AS overridden
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
    row = conn.execute(f"{_SUMMARY} AND l.id = ?", (USER_ID, lesson_id)).fetchone()
    if row is None or row["id"] is None:
        raise HTTPException(404, "no such lesson")
    return row


@router.post("", response_model=LessonSummary, status_code=201)
def create_lesson(req: ImportRequest) -> LessonSummary:
    """Import plain text. Tokenising and lemmatising happen here, once."""
    text, title, source = req.text, req.title, req.source
    if not clean(text):
        # min_length on the field passes whitespace; cleaning is what decides
        raise HTTPException(400, "no text to import")
    with connect() as conn:
        try:
            lesson_id = import_text(
                conn,
                user_id=USER_ID,
                lang=req.lang,
                text=text,
                title=title,
                source=source,
            )
        except UnknownLanguage:
            raise HTTPException(400, f"no adapter for language {req.lang!r}") from None
        except OSError as exc:  # spaCy model not downloaded
            raise HTTPException(503, f"language model unavailable: {exc}") from None
        refresh(conn, [lesson_id])
        row = _lesson_row(conn, lesson_id)
    return LessonSummary(**{k: row[k] for k in DB_FIELDS})


@router.get("", response_model=list[LessonSummary])
def list_lessons() -> list[LessonSummary]:
    with connect() as conn:
        rows = conn.execute(
            f"{_SUMMARY} ORDER BY l.imported_at DESC, l.id DESC", (USER_ID,)
        ).fetchall()
    return [LessonSummary(**{k: r[k] for k in DB_FIELDS}) for r in rows]


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
        **{k: row[k] for k in DB_FIELDS},
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
                morph=t["morph"],
                overridden=bool(t["overridden"]),
                state=state_for(t["lemma"], t["status"], bool(t["form_seen"])),
            )
            for t in tokens
        ],
    )


@router.post("/fetch")
def fetch_url(req: FetchRequest) -> dict[str, str]:
    """Pull the article text out of a web page, without importing anything.

    Deliberately not part of importing: extraction gets formatting wrong often
    enough that you want to see it, and fix it, before it becomes a lesson.
    """
    try:
        text, title = from_url.fetch(req.url)
    except BadUrl as exc:
        raise HTTPException(400, str(exc)) from None
    if not clean(text):
        raise HTTPException(400, "nothing that looks like an article on that page")
    return {"text": text, "title": title or "", "source": req.url}


@router.get("/{lesson_id}/translation")
def translation(lesson_id: int, page: int | None = None) -> dict[int, str]:
    """English for each sentence on a page, keyed by sent_id.

    Translated on first request and kept, so the toggle is instant afterwards and
    an import never pays for a feature that is off by default.
    """
    with connect() as conn:
        row = _lesson_row(conn, lesson_id)
        pages = _pages(conn, lesson_id)
        page = _resume(pages, row["last_token"]) if page is None else page
        lo, hi = pages[max(0, min(page, len(pages) - 1))]
        try:
            return glosses_for(conn, lesson_id, row["lang"], lo, hi)
        except Unavailable as exc:
            raise HTTPException(503, f"translation unavailable: {exc}") from None


@router.delete("/{lesson_id}", status_code=204)
def delete_lesson(lesson_id: int) -> None:
    with connect() as conn:
        _lesson_row(conn, lesson_id)
        conn.execute("DELETE FROM lesson WHERE id = ? AND user_id = ?", (lesson_id, USER_ID))


@router.put("/{lesson_id}/collection", response_model=LessonSummary)
def set_collection(lesson_id: int, req: CollectionRequest) -> LessonSummary:
    """Put a lesson in a collection, creating it if the name is new.

    By name rather than by id: there is no screen for managing collections and
    there should not need to be one — typing the same name twice is how you put
    two things together.
    """
    with connect() as conn:
        row = _lesson_row(conn, lesson_id)
        name = (req.name or "").strip()
        if not name:
            conn.execute(
                "UPDATE lesson SET collection_id = NULL, position = 0 WHERE id = ?", (lesson_id,)
            )
        else:
            conn.execute(
                "INSERT OR IGNORE INTO collection (user_id, lang, title) VALUES (?,?,?)",
                (USER_ID, row["lang"], name),
            )
            cid = conn.execute(
                "SELECT id FROM collection WHERE user_id=? AND lang=? AND title=?",
                (USER_ID, row["lang"], name),
            ).fetchone()["id"]
            # Appended, so the order is the order things were added unless the
            # importer says otherwise.
            nxt = conn.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 FROM lesson WHERE collection_id = ?", (cid,)
            ).fetchone()[0]
            conn.execute(
                "UPDATE lesson SET collection_id = ?, position = ? WHERE id = ?",
                (cid, nxt, lesson_id),
            )
        # A collection nobody is in should not linger in the suggestions.
        conn.execute(
            "DELETE FROM collection WHERE id NOT IN"
            " (SELECT collection_id FROM lesson WHERE collection_id IS NOT NULL)"
        )
        row = _lesson_row(conn, lesson_id)
    return LessonSummary(**{k: row[k] for k in DB_FIELDS})


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

        # Every word on this page, as the *lexicon* sees it: an override wins over
        # the pipeline (CLAUDE.md rule 5). Defined once and used by everything
        # below — when only some of these statements resolved overrides, marking a
        # page known wrote to the pipeline's lemma while the undo log recorded the
        # override's, so undo deleted a row it had never created and left the word
        # known for ever.
        page_words = """
            SELECT DISTINCT COALESCE(o.to_lemma, t.lemma) AS lemma,
                            COALESCE(o.to_pos, t.pos)     AS pos
            FROM token t
            LEFT JOIN lemma_override o
                   ON o.user_id = ? AND o.lang = ? AND o.surface = t.norm
            WHERE t.lesson_id = ? AND t.idx BETWEEN ? AND ? AND t.lemma IS NOT NULL
        """
        args = (USER_ID, lang, lesson_id, lo, hi)

        undo_id, doomed = None, []
        if req.mark_rest_known:
            # Record what the blue words were before, so a misclick is recoverable.
            # These are exactly the rows the statement below will change.
            doomed = conn.execute(
                f"""
                SELECT w.lemma, w.pos, s.status
                FROM ({page_words}) w
                LEFT JOIN lemma_status s
                       ON s.user_id = ? AND s.lang = ?
                      AND s.lemma = w.lemma AND s.pos = w.pos
                WHERE s.status IS NULL OR s.status IN (0, 4)
                """,
                (*args, USER_ID, lang),
            ).fetchall()
            if doomed:
                undo_id = conn.execute(
                    "INSERT INTO bulk_undo (user_id, lang, lesson_id, kind, n, before)"
                    " VALUES (?,?,?,'mark_page_known',?,?)",
                    (
                        USER_ID,
                        lang,
                        lesson_id,
                        len(doomed),
                        json.dumps([[r["lemma"], r["pos"], r["status"]] for r in doomed]),
                    ),
                ).lastrowid
            # The words that want something from you: never judged (no row or 0),
            # and those the app has been asking about (4). Pressing this button is
            # the answer to that question — the app still never promotes a word by
            # itself. A word you are actively learning (1-3) is a decision you made
            # and stays; ignored (-1) and known (5) are left alone.
            conn.execute(
                f"""
                INSERT INTO lemma_status (user_id, lang, lemma, pos, status)
                -- WHERE true so the parser reads ON CONFLICT as the upsert
                -- clause rather than a join condition on the SELECT.
                SELECT ?, ?, lemma, pos, 5 FROM ({page_words}) WHERE true
                ON CONFLICT(user_id, lang, lemma, pos) DO UPDATE
                    SET status = 5, updated_at = datetime('now')
                    WHERE lemma_status.status IN (0, 4)
                """,
                (USER_ID, lang, *args),
            )
        # A word you are learning rises one level for each page you finish that
        # contains it — an observation, not a self-assessment (decision 0008).
        # A page it has already been credited for does not count again: turning
        # the same page twice is not a second encounter, and neither is the page
        # you were on when you flagged the word.
        conn.execute(
            f"""
            UPDATE lemma_status SET status = status + 1, updated_at = datetime('now')
            WHERE user_id = ? AND lang = ? AND status BETWEEN 1 AND 3
              AND (lemma, pos) IN (
                  {page_words}
                  EXCEPT
                  SELECT lemma, pos FROM exposure
                  WHERE user_id = ? AND lang = ? AND lesson_id = ? AND page = ?
              )
            """,
            (USER_ID, lang, *args, USER_ID, lang, lesson_id, page),
        )
        conn.execute(
            f"""
            INSERT OR IGNORE INTO exposure (user_id, lang, lemma, pos, lesson_id, page)
            SELECT ?, ?, lemma, pos, ?, ? FROM ({page_words})
            """,
            (USER_ID, lang, lesson_id, page, *args),
        )
        # Every form of a word you have an opinion about has now been met, so it
        # stops being highlighted as novel next time — and `form_seen.count` is
        # what the vocabulary page shows as "seen 6×" (decision 0008).
        #
        # Any word you have judged, not only the known ones: a word you are
        # learning is met on a page just as much, and counting only the known ones
        # left that number frozen at however many times you had clicked it. Words
        # you have *not* judged are still left out, because recording their forms
        # here would erase the novel-form highlight before you had read them.
        conn.execute(
            """
            INSERT INTO form_seen (user_id, lang, lemma, pos, surface, "count")
            SELECT ?, ?, COALESCE(o.to_lemma, t.lemma), COALESCE(o.to_pos, t.pos),
                   t.norm, COUNT(*)
            FROM token t
            LEFT JOIN lemma_override o
                   ON o.user_id = ? AND o.lang = ? AND o.surface = t.norm
            JOIN lemma_status s
              ON s.user_id = ? AND s.lang = ?
             AND s.lemma = COALESCE(o.to_lemma, t.lemma)
             AND s.pos   = COALESCE(o.to_pos, t.pos)
            WHERE t.lesson_id = ? AND t.idx BETWEEN ? AND ?
              AND t.lemma IS NOT NULL AND s.status BETWEEN 1 AND 5
            GROUP BY COALESCE(o.to_lemma, t.lemma), COALESCE(o.to_pos, t.pos), t.norm
            ON CONFLICT(user_id, lang, lemma, pos, surface) DO UPDATE
                SET "count" = form_seen."count" + excluded."count"
            """,
            (USER_ID, lang, USER_ID, lang, USER_ID, lang, lesson_id, lo, hi),
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
        # Marking a page known moves words between buckets; the level bumps above
        # do not, since 1→2→3 stays inside "learning".
        if req.mark_rest_known and doomed:
            refresh_for_words(conn, USER_ID, lang, [(d["lemma"], d["pos"]) for d in doomed])
        row = _lesson_row(conn, lesson_id)
    summary = LessonSummary(**{k: row[k] for k in DB_FIELDS})
    summary.undo_id = undo_id
    summary.undo_n = len(doomed)
    return summary


@router.post("/undo/{undo_id}", status_code=204)
def undo_bulk(undo_id: int) -> None:
    """Put back the words a bulk action changed.

    Words that had no status before are deleted rather than set to 0, so undoing
    leaves the lexicon exactly as it was rather than littering it with zeroes.
    """
    with connect() as conn:
        row = conn.execute(
            "SELECT lang, before, undone FROM bulk_undo WHERE id = ? AND user_id = ?",
            (undo_id, USER_ID),
        ).fetchone()
        if row is None:
            raise HTTPException(404, "no such action")
        if row["undone"]:
            raise HTTPException(409, "already undone")
        for lemma, pos, prev in json.loads(row["before"]):
            if prev is None:
                conn.execute(
                    "DELETE FROM lemma_status WHERE user_id=? AND lang=? AND lemma=? AND pos=?",
                    (USER_ID, row["lang"], lemma, pos),
                )
            else:
                conn.execute(
                    "UPDATE lemma_status SET status=?, updated_at=datetime('now')"
                    " WHERE user_id=? AND lang=? AND lemma=? AND pos=?",
                    (prev, USER_ID, row["lang"], lemma, pos),
                )
        conn.execute("UPDATE bulk_undo SET undone = 1 WHERE id = ?", (undo_id,))
        refresh_for_words(
            conn, USER_ID, row["lang"], [(w, p) for w, p, _ in json.loads(row["before"])]
        )
