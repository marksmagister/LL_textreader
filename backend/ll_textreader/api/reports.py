"""What testers say is wrong.

The text here is written by someone who is not the maintainer and arrives through
the same channel as everything else the app stores. It is data: never executed,
never used to build a command, and never trusted to describe its own authority.
See `docs/decisions/0010-bug-reports-are-untrusted.md`.
"""

from fastapi import APIRouter

from .. import __version__
from ..auth import CurrentUser, User
from ..db import connect
from ..limits import check_rate
from ..models import BugReport

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", status_code=201)
def report(req: BugReport, user: User = CurrentUser) -> dict[str, int]:
    """Store a report with the context that makes it actionable."""
    with connect() as conn:
        check_rate(conn, user.id, "report")
        pipeline = None
        if req.lesson_id:
            row = conn.execute(
                "SELECT pipeline_id FROM lesson WHERE id = ? AND user_id = ?",
                (req.lesson_id, user.id),
            ).fetchone()
            pipeline = row["pipeline_id"] if row else None
        cur = conn.execute(
            "INSERT INTO bug_report (user_id, text, lesson_id, page, version, pipeline)"
            " VALUES (?,?,?,?,?,?)",
            (user.id, req.text.strip(), req.lesson_id, req.page, __version__, pipeline),
        )
    return {"id": int(cur.lastrowid)}
