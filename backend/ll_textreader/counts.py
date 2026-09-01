"""How much of each lesson you can already read, kept on the lesson row.

Computing this live meant joining every token of every lesson against the lexicon
each time the library was opened: 8ms at fifteen lessons, 283ms at five hundred,
1.2s at two thousand, and growing with everything you ever import.

So it is stored. The rule that keeps it honest: **recompute, never adjust.** No
arithmetic on deltas, no reasoning about what a change implies — the affected
lessons are counted again from scratch. Wrong-but-cheap arithmetic is how cached
counts drift, and a drifted count is worse than a slow one.

What makes that affordable is that almost no write can change these numbers. A
word only moves the counts when it crosses between new, learning and known; the
level rising 1→2→3 on a page turn does not, and that is most writes.
"""

import sqlite3

from .models import IGNORED, KNOWN, NEW


# Which bucket the library counts a word in. Ignored words read as known, since
# you can read past them.
def bucket(status: int | None) -> str:
    if status is None or status == NEW:
        return "n_new"
    if status == IGNORED or status >= KNOWN:
        return "n_known"
    return "n_learning"


_RECOUNT = """
UPDATE lesson SET
    n_tokens = COALESCE((SELECT COUNT(*) FROM token WHERE lesson_id = lesson.id), 0),
    n_words = COALESCE((SELECT COUNT(lemma) FROM token WHERE lesson_id = lesson.id), 0),
    n_new = COALESCE((SELECT SUM(t.lemma IS NOT NULL AND (s.status IS NULL OR s.status = 0))
        FROM token t
        LEFT JOIN lemma_override o ON o.user_id = lesson.user_id AND o.lang = lesson.lang
                                  AND o.surface = t.norm
        LEFT JOIN lemma_status s ON s.user_id = lesson.user_id AND s.lang = lesson.lang
                                AND s.lemma = COALESCE(o.to_lemma, t.lemma)
                                AND s.pos = COALESCE(o.to_pos, t.pos)
        WHERE t.lesson_id = lesson.id), 0),
    n_learning = COALESCE((SELECT SUM(t.lemma IS NOT NULL AND s.status BETWEEN 1 AND 4)
        FROM token t
        LEFT JOIN lemma_override o ON o.user_id = lesson.user_id AND o.lang = lesson.lang
                                  AND o.surface = t.norm
        LEFT JOIN lemma_status s ON s.user_id = lesson.user_id AND s.lang = lesson.lang
                                AND s.lemma = COALESCE(o.to_lemma, t.lemma)
                                AND s.pos = COALESCE(o.to_pos, t.pos)
        WHERE t.lesson_id = lesson.id), 0),
    n_known = COALESCE((SELECT SUM(t.lemma IS NOT NULL AND (s.status >= 5 OR s.status = -1))
        FROM token t
        LEFT JOIN lemma_override o ON o.user_id = lesson.user_id AND o.lang = lesson.lang
                                  AND o.surface = t.norm
        LEFT JOIN lemma_status s ON s.user_id = lesson.user_id AND s.lang = lesson.lang
                                AND s.lemma = COALESCE(o.to_lemma, t.lemma)
                                AND s.pos = COALESCE(o.to_pos, t.pos)
        WHERE t.lesson_id = lesson.id), 0)
WHERE lesson.id IN ({where})
"""


def refresh(conn: sqlite3.Connection, lesson_ids: list[int]) -> None:
    """Recount these lessons."""
    if not lesson_ids:
        return
    marks = ",".join("?" * len(lesson_ids))
    conn.execute(_RECOUNT.format(where=marks), lesson_ids)


def refresh_for_words(
    conn: sqlite3.Connection, user_id: int, lang: str, words: list[tuple[str, str]]
) -> None:
    """Recount every lesson containing any of these (lemma, pos) pairs.

    A word appears in a handful of lessons, so this is small — and it is the only
    thing that has to happen when a word changes bucket.
    """
    if not words:
        return
    ids: set[int] = set()
    for lemma, pos in words:
        ids.update(
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT t.lesson_id FROM token t JOIN lesson l ON l.id = t.lesson_id"
                " WHERE l.user_id = ? AND l.lang = ? AND t.lemma = ? AND t.pos = ?",
                (user_id, lang, lemma, pos),
            )
        )
        # An override can point a surface at this lemma from a lesson where the
        # pipeline said something else, so those lessons count too.
        ids.update(
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT t.lesson_id FROM token t"
                " JOIN lesson l ON l.id = t.lesson_id"
                " JOIN lemma_override o ON o.user_id = l.user_id AND o.lang = l.lang"
                "   AND o.surface = t.norm"
                " WHERE l.user_id = ? AND l.lang = ? AND o.to_lemma = ? AND o.to_pos = ?",
                (user_id, lang, lemma, pos),
            )
        )
    refresh(conn, sorted(ids))


def refresh_all(conn: sqlite3.Connection, user_id: int | None = None) -> int:
    """Recount everything. For repair, and after anything that moved tokens."""
    rows = conn.execute(
        "SELECT id FROM lesson" + (" WHERE user_id = ?" if user_id else ""),
        (user_id,) if user_id else (),
    ).fetchall()
    refresh(conn, [r[0] for r in rows])
    return len(rows)


def _main() -> None:
    """`python -m ll_textreader.counts` — recount everything.

    For after a migration, or if the numbers are ever doubted. Recomputing the
    whole library is the same work the library used to do on every visit.
    """
    from .db import connect, init_db

    init_db()
    with connect() as conn:
        n = refresh_all(conn)
        conn.commit()
    print(f"recounted {n} lessons")


if __name__ == "__main__":
    _main()
