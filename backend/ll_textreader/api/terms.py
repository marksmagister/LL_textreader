"""The lexicon: your status for one word."""

from fastapi import APIRouter

from ..db import USER_ID, connect
from ..models import KNOWN, TermUpdate, TokenState, state_for

router = APIRouter(prefix="/api/terms", tags=["terms"])


@router.put("", response_model=dict[str, str | int | None])
def set_term(req: TermUpdate) -> dict[str, str | int | None]:
    """Set a word's status. Clicking a blue word lands here.

    The surface form you met it in is recorded too, so a word you know in a shape
    you've met renders plain, and in a shape you haven't renders lighter.
    """
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO lemma_status (user_id, lang, lemma, pos, status, note, context)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(user_id, lang, lemma, pos) DO UPDATE SET
                status = excluded.status,
                note = COALESCE(excluded.note, lemma_status.note),
                -- keep the sentence you first met it in
                context = COALESCE(lemma_status.context, excluded.context),
                updated_at = datetime('now')
            """,
            (USER_ID, req.lang, req.lemma, req.pos, req.status, req.note, req.context),
        )
        if req.surface:
            conn.execute(
                """
                INSERT INTO form_seen (user_id, lang, lemma, pos, surface)
                VALUES (?,?,?,?,?)
                ON CONFLICT(user_id, lang, lemma, pos, surface) DO UPDATE
                    SET "count" = form_seen."count" + 1
                """,
                (USER_ID, req.lang, req.lemma, req.pos, req.surface.casefold()),
            )
        seen = req.status < KNOWN or bool(req.surface)

    state: TokenState = state_for(req.lemma, req.status, seen)
    return {"lemma": req.lemma, "pos": req.pos, "status": req.status, "state": state}
