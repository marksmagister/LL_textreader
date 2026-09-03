"""Take it with you, and leave.

docs/decisions/0013 argues that an account on someone else's server is the
weakest form of ownership there is, and that what actually makes reading history
yours is a copy of it on your own machine in a format that outlives this project.
These two endpoints are that argument in code, and they are why they were built
before sign-in rather than after: Google sign-in has no recovery story of its own,
so losing an account has to be survivable.
"""

import io
import json
import re
import zipfile

from fastapi import APIRouter, Response

from ..auth import CurrentUser, User
from ..db import connect
from ..export import as_json, collect

router = APIRouter(prefix="/api/account", tags=["account"])

# Every table holding something a reader owns, children first so that nothing is
# left pointing at a row that has gone. Written out rather than derived from the
# schema: a table added later should have to be added here deliberately, and a
# test counts rows across the whole database to catch it if it is not.
#
# `lesson` cascades to token, exposure, reading_progress and sentence_gloss, but
# the first two are deleted explicitly anyway — they are keyed on the user as
# well, and a row of theirs could outlive a lesson somebody else owns.
OWNED = [
    "exposure",
    "reading_progress",
    "form_seen",
    "lemma_status",
    "lemma_override",
    "bulk_undo",
    "bug_report",
    "lesson",
    "collection",
    "session",
]


def _safe(name: str, fallback: str) -> str:
    """A filename that cannot escape the archive or upset a filesystem."""
    cleaned = re.sub(r"[^\w\s.-]", "", name, flags=re.UNICODE).strip().strip(".")
    return (cleaned or fallback)[:80]


@router.get("/export")
def export_everything(user: User = CurrentUser) -> Response:
    """Everything you have put in, as one zip.

    The lexicon is the irreplaceable half — the texts you could find again, the
    six months of judgements about them you could not — so it goes in as JSON per
    language rather than only as the Anki export, which is lossy on purpose.
    """
    buffer = io.BytesIO()
    with connect() as conn:
        lessons = conn.execute(
            "SELECT id, lang, title, source, body, imported_at FROM lesson"
            " WHERE user_id = ? ORDER BY id",
            (user.id,),
        ).fetchall()
        langs = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT lang FROM lemma_status WHERE user_id = ?", (user.id,)
            )
        ]
        lexicons = {lang: collect(conn, user.id, lang) for lang in langs}

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for row in lessons:
            name = _safe(row["title"], f"lesson-{row['id']}")
            # The id keeps two lessons with the same title apart.
            z.writestr(f"lessons/{row['lang']}/{row['id']:04d}-{name}.txt", row["body"])
        for lang, entries in lexicons.items():
            z.writestr(f"lexicon-{lang}.json", as_json(entries, lang))
        z.writestr(
            "README.txt",
            "Everything LL_textreader holds for this account.\n\n"
            "lessons/    the texts you imported, as you imported them\n"
            "lexicon-*.json  every word you have a status for, the shapes of it\n"
            "            you have met, your notes, and where you first met it\n\n"
            "The lexicon is the part that cannot be reconstructed.\n",
        )
        z.writestr(
            "account.json",
            json.dumps(
                {"name": user.name, "email": user.email, "lessons": len(lessons)},
                ensure_ascii=False,
                indent=2,
            ),
        )

    return Response(
        buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="ll_textreader-export.zip"'},
    )


@router.delete("", status_code=204)
def delete_account(user: User = CurrentUser, response: Response = None) -> Response:
    """Leave, and actually be gone.

    Rows, not a flag. Explicit DELETEs rather than rebuilding ten tables to add
    ON DELETE CASCADE — SQLite cannot add a constraint to a table that exists, and
    ten statements you can read beat a migration you cannot.
    """
    with connect() as conn:
        for table in OWNED:
            conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user.id,))
        conn.execute("DELETE FROM user WHERE id = ?", (user.id,))
    out = Response(status_code=204)
    out.delete_cookie("ll_session", path="/")
    return out
