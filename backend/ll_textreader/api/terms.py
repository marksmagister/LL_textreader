"""The lexicon: your status for one word."""

from fastapi import APIRouter

from ..db import USER_ID, connect
from ..models import KNOWN, OverrideRequest, TermUpdate, TokenState, state_for

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
        if req.lesson_id is not None and req.page is not None:
            # You met it here — that is why you are judging it. Crediting this
            # page again when you turn it would count one encounter as two.
            conn.execute(
                """
                INSERT OR IGNORE INTO exposure
                    (user_id, lang, lemma, pos, lesson_id, page)
                VALUES (?,?,?,?,?,?)
                """,
                (USER_ID, req.lang, req.lemma, req.pos, req.lesson_id, req.page),
            )
        seen = req.status < KNOWN or bool(req.surface)

    state: TokenState = state_for(req.lemma, req.status, seen)
    return {"lemma": req.lemma, "pos": req.pos, "status": req.status, "state": state}


@router.put("/override", response_model=dict[str, str])
def set_override(req: OverrideRequest) -> dict[str, str]:
    """Detach a surface form from the lemma the pipeline gave it.

    Without this, one bad model decision is unfixable and the colouring stops
    being trusted — which is the whole reason the table exists.
    """
    surface = req.surface.casefold()
    to_lemma = (req.to_lemma or surface).casefold()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO lemma_override (user_id, lang, surface, from_lemma, to_lemma, to_pos)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(user_id, lang, surface) DO UPDATE SET
                from_lemma = excluded.from_lemma,
                to_lemma = excluded.to_lemma,
                to_pos = excluded.to_pos,
                created_at = datetime('now')
            """,
            (USER_ID, req.lang, surface, req.from_lemma, to_lemma, req.to_pos),
        )
    return {"surface": surface, "lemma": to_lemma, "pos": req.to_pos}


@router.delete("/override", status_code=204)
def clear_override(lang: str, surface: str) -> None:
    """Undo an override — the pipeline's answer applies again."""
    with connect() as conn:
        conn.execute(
            "DELETE FROM lemma_override WHERE user_id = ? AND lang = ? AND surface = ?",
            (USER_ID, lang, surface.casefold()),
        )
