"""Exporting the lexicon.

The vocabulary is the part of this database that cannot be reconstructed: the
lessons are replaceable and the glosses are a re-download. It should never be
hostage to one schema version, or to SQLite.

Three formats. `anki` is the point of the exercise — spaced repetition is
deliberately not built here (decision 0005), and Anki is a better scheduler than
this project would write, so the job is to hand it good cards.
"""

import csv
import io
import json
import sqlite3
from html import escape

from .models import IGNORED, KNOWN, NEW, REVIEW

GLOSSES_PER_CARD = 3

# Anki 2.1.55+ reads these, so a file imports with the right note type, deck and
# field mapping instead of a dialog full of guesses.
ANKI_HEADER = [
    "#separator:tab",
    "#html:true",
    "#notetype:Basic",
    "#deck:LL_textreader",
    "#columns:Front\tBack\tTags",
    "#tags column:3",
]

_ROWS = """
SELECT s.lemma, s.pos, s.status, s.note, s.context, s.created_at, s.updated_at,
       group_concat(DISTINCT f.surface) AS forms
FROM lemma_status s
LEFT JOIN form_seen f
       ON f.user_id = s.user_id AND f.lang = s.lang
      AND f.lemma = s.lemma AND f.pos = s.pos
WHERE s.user_id = ? AND s.lang = ?
GROUP BY s.lemma, s.pos
ORDER BY s.lemma, s.pos
"""

# Glosses come as their own query and are cut down in Python.
#
# They used to be a scalar subquery over a nested SELECT ... LIMIT, correlated on
# the outer row's lemma and pos. SQLite does not allow a FROM-clause subquery to
# see the outer query, so that raised "no such column: s.pos" — but only on some
# SQLite versions, which meant it passed locally and took the whole export out on
# the deployment box. One join and a loop cannot do that.
_GLOSSES = """
SELECT s.lemma, s.pos, h.gloss
FROM lemma_status s
JOIN hint h ON h.lang = s.lang AND h.lemma = s.lemma
WHERE s.user_id = ? AND s.lang = ?
ORDER BY s.lemma, s.pos, (h.pos = s.pos) DESC, h.rank
"""


def _glosses(conn: sqlite3.Connection, user_id: int, lang: str) -> dict[tuple[str, str], list[str]]:
    """Up to GLOSSES_PER_CARD senses per word, the ones matching its POS first."""
    out: dict[tuple[str, str], list[str]] = {}
    for r in conn.execute(_GLOSSES, (user_id, lang)):
        got = out.setdefault((r["lemma"], r["pos"]), [])
        if len(got) < GLOSSES_PER_CARD:
            got.append(r["gloss"])
    return out


def bucket(status: int) -> str:
    if status == IGNORED:
        return "ignored"
    if status == NEW:
        return "new"
    if status >= KNOWN:
        return "known"
    return "review" if status >= REVIEW else "learning"


def collect(
    conn: sqlite3.Connection,
    user_id: int,
    lang: str,
    status: str | None = None,
    q: str | None = None,
    keys: set[str] | None = None,
) -> list[dict]:
    """The lexicon, filtered. `keys` are "lemma:pos" pairs picked in the UI."""
    glosses = _glosses(conn, user_id, lang)
    out = []
    for r in conn.execute(_ROWS, (user_id, lang)):
        entry = {
            "lemma": r["lemma"],
            "pos": r["pos"],
            "status": r["status"],
            "bucket": bucket(r["status"]),
            "note": r["note"],
            "context": r["context"],
            "forms": sorted(set((r["forms"] or "").split(",")) - {""}),
            "glosses": glosses.get((r["lemma"], r["pos"]), []),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        if keys is not None and f"{entry['lemma']}:{entry['pos']}" not in keys:
            continue
        if status and entry["bucket"] != status:
            continue
        if q and not entry["lemma"].startswith(q.casefold()):
            continue
        out.append(entry)
    return out


def _field(text: str) -> str:
    """One TSV cell. Tabs and newlines would break the row, so they never survive."""
    return escape(text or "").replace("\t", " ").replace("\r", "").replace("\n", "<br>")


def as_anki(entries: list[dict], lang: str) -> str:
    """Tab-separated notes: Front, Back, Tags.

    Anki's Basic note type deduplicates on the first field, so a lemma that
    appears under two parts of speech gets them disambiguated — otherwise
    `porte` the door would silently overwrite `porter` the verb's form.
    """
    seen: dict[str, int] = {}
    for e in entries:
        seen[e["lemma"]] = seen.get(e["lemma"], 0) + 1

    # Joined by hand rather than with csv.writer: _field has already removed
    # every tab and newline, so there is nothing left to quote or escape, and
    # Anki reads these files as plain tab-separated.
    rows = []
    for e in entries:
        front = e["lemma"] if seen[e["lemma"]] == 1 else f"{e['lemma']} ({e['pos'].lower()})"
        back = []
        if e["note"]:
            back.append(f"<b>{_field(e['note'])}</b>")
        back += [_field(g) for g in e["glosses"]]
        if e["context"]:
            back.append(f"<i>{_field(e['context'])}</i>")
        if e["forms"]:
            back.append(f"<small>forms seen: {_field(', '.join(e['forms']))}</small>")
        tags = " ".join(["ll_textreader", lang, e["pos"].lower() or "x", e["bucket"]])
        rows.append("\t".join([_field(front), "<br>".join(back) or _field(front), tags]))
    return "\n".join([*ANKI_HEADER, *rows]) + "\n"


def as_csv(entries: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(
        ["lemma", "pos", "status", "bucket", "note", "context", "forms", "glosses", "updated_at"]
    )
    for e in entries:
        writer.writerow(
            [
                e["lemma"],
                e["pos"],
                e["status"],
                e["bucket"],
                e["note"] or "",
                e["context"] or "",
                "; ".join(e["forms"]),
                "; ".join(e["glosses"]),
                e["updated_at"],
            ]
        )
    return out.getvalue()


def as_json(entries: list[dict], lang: str) -> str:
    """Full fidelity, so a future importer has everything it needs."""
    return json.dumps(
        {"lang": lang, "count": len(entries), "entries": entries}, ensure_ascii=False, indent=2
    )
