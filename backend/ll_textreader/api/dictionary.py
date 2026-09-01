"""Dictionary lookup: what a word means."""

from fastapi import APIRouter

from ..db import connect
from ..dictionary import lookup

router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])


@router.get("")
def define(lang: str, lemma: str, pos: str | None = None) -> list[dict]:
    with connect() as conn:
        return lookup(conn, lang, lemma, pos)
