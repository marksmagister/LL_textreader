"""Your lexicon, as a list: what you know, and which shapes of it you've met."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..auth import CurrentUser, User
from ..db import connect
from ..export import as_anki, as_csv, as_json, collect
from ..models import IGNORED, KNOWN, NEW, Vocab, VocabEntry

router = APIRouter(prefix="/api/vocab", tags=["vocab"])

SEP = "\x1f"  # unit separator: can't occur in a French surface form

_ROWS = f"""
SELECT s.lemma, s.pos, s.status, s.note, s.context, s.updated_at,
       group_concat(f.surface, '{SEP}') AS forms,
       COALESCE(SUM(f."count"), 0) AS met,
       -- When you last actually met it. `exposure` records every page you
       -- finished that contained the word, whatever its status, so this is a
       -- truer "last seen" than updated_at, which only moves when it changes.
       (SELECT MAX(e.seen_at) FROM exposure e
         WHERE e.user_id = s.user_id AND e.lang = s.lang
           AND e.lemma = s.lemma AND e.pos = s.pos) AS last_seen
FROM lemma_status s
LEFT JOIN form_seen f
       ON f.user_id = s.user_id AND f.lang = s.lang
      AND f.lemma = s.lemma AND f.pos = s.pos
WHERE s.user_id = ? AND s.lang = ?
GROUP BY s.lemma, s.pos
"""


# The second is the point of the feature: words you were learning that then
# quietly stopped appearing, which nothing else in the app would ever show you.
SORTS = {
    "recent": lambda e: (e.last_seen or "", e.lemma),
    "stale": lambda e: (e.last_seen or "", e.lemma),
    "alpha": lambda e: (e.lemma, e.pos),
    "forms": lambda e: (-len(e.forms), e.lemma),
}
DESCENDING = {"recent", "forms"}


def _bucket(status: int) -> str:
    if status == IGNORED:
        return "ignored"
    if status == NEW:
        return "new"
    return "known" if status >= KNOWN else "learning"


@router.get("", response_model=Vocab)
def list_vocab(
    lang: str = "fr",
    status: str | None = None,
    q: str | None = None,
    sort: str = "recent",
    user: User = CurrentUser,
) -> Vocab:
    """Every word you have a status for.

    `status` filters to one bucket (new/learning/known/ignored); `q` matches the
    start of a lemma. Counts are over the whole lexicon, not the filtered view —
    otherwise the totals move every time you type in the search box.

    `sort` is one of recent, stale, alpha, forms. `stale` is the useful one:
    oldest first, so words you were learning and have not met since rise to the
    top. Nothing else in the app would ever surface those.
    """
    if sort not in SORTS:
        raise HTTPException(400, f"sort must be one of {', '.join(SORTS)}")
    with connect() as conn:
        rows = conn.execute(_ROWS, (user.id, lang)).fetchall()

    by_status: dict[str, int] = {}
    entries: list[VocabEntry] = []
    for r in rows:
        bucket = _bucket(r["status"])
        by_status[bucket] = by_status.get(bucket, 0) + 1
        if status and bucket != status:
            continue
        if q and not r["lemma"].startswith(q.casefold()):
            continue
        entries.append(
            VocabEntry(
                lemma=r["lemma"],
                pos=r["pos"],
                status=r["status"],
                note=r["note"],
                context=r["context"],
                updated_at=r["updated_at"],
                forms=sorted(set((r["forms"] or "").split(SEP)) - {""}),
                met=r["met"],
                last_seen=r["last_seen"],
            )
        )
    entries.sort(key=SORTS[sort], reverse=sort in DESCENDING)
    return Vocab(total=len(rows), by_status=by_status, entries=entries)


FORMATS = {
    "anki": ("text/tab-separated-values", "tsv"),
    "csv": ("text/csv", "csv"),
    "json": ("application/json", "json"),
}


@router.get("/export")
def export(
    lang: str = "fr",
    format: str = "anki",
    status: str | None = None,
    q: str | None = None,
    keys: str | None = None,
    user: User = CurrentUser,
) -> Response:
    """Download the lexicon, or a chosen part of it.

    `status` narrows to one bucket, `q` to a prefix, and `keys` to an explicit
    list of "lemma:pos" pairs ticked in the vocabulary list. They compose, so
    "the learning words I selected" is one request.
    """
    if format not in FORMATS:
        raise HTTPException(400, f"format must be one of {', '.join(FORMATS)}")
    media_type, suffix = FORMATS[format]
    picked = set(filter(None, (keys or "").split(","))) or None

    with connect() as conn:
        entries = collect(conn, user.id, lang, status=status, q=q, keys=picked)

    body = (
        as_anki(entries, lang)
        if format == "anki"
        else as_csv(entries)
        if format == "csv"
        else as_json(entries, lang)
    )
    name = f"ll_textreader-{lang}-{status or 'all'}.{suffix}"
    return Response(
        body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
