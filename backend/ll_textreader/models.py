"""Types shared between the pipeline, the DB and the API.

Mirrored by frontend/src/types.ts — keep the two in step.
"""

from typing import Literal

from pydantic import BaseModel, Field

# blue / yellow / lighter / plain. See docs/data-model.md.
TokenState = Literal["new", "learning", "novel-form", "known"]

NEW, LEARNING, KNOWN, IGNORED = 0, 1, 5, -1


class AnalysedToken(BaseModel):
    """What an adapter produces and what goes into the `token` table verbatim."""

    idx: int
    surface: str
    norm: str
    lemma: str | None = None  # None = not a lexical token (punctuation, digits)
    pos: str | None = None
    char_start: int
    char_end: int
    sent_id: int
    confidence: float = 1.0


class ReaderToken(BaseModel):
    """A token as the reader sees it: the pipeline's output joined with your lexicon."""

    idx: int
    surface: str
    lemma: str | None
    pos: str | None
    char_start: int
    char_end: int
    state: TokenState


class LessonSummary(BaseModel):
    id: int
    lang: str
    title: str
    source: str | None
    pipeline_id: str
    imported_at: str
    n_tokens: int
    n_words: int
    last_token: int = 0  # where you stopped; 0 = not started


class LessonDetail(LessonSummary):
    """One page of a lesson.

    Pages are derived from the token stream at read time, not stored, so position
    is a token index and stays valid if PAGE_TOKENS ever changes.
    """

    page: int
    n_pages: int
    body: str  # this page's slice of the original text. Spans overlay it; never rebuilt.
    body_offset: int  # where the slice starts, so token offsets stay absolute
    tokens: list[ReaderToken]


class ImportRequest(BaseModel):
    text: str = Field(min_length=1)
    title: str | None = None  # defaults to the first line of the text

    lang: str = "fr"
    source: str | None = None


class TermUpdate(BaseModel):
    lang: str
    lemma: str
    pos: str = ""
    status: int = Field(ge=-1, le=5)
    note: str | None = None
    surface: str | None = None  # the form you met it in; recorded in form_seen
    context: str | None = None


class FinishRequest(BaseModel):
    page: int = 0
    # The pressure valve (CLAUDE.md rule 8): everything still blue on this page
    # becomes known.
    mark_rest_known: bool = False


def state_for(lemma: str | None, status: int | None, form_seen: bool) -> TokenState:
    """The render rule, in one place. See docs/data-model.md."""
    if lemma is None:
        return "known"  # punctuation, digits: nothing to learn, render plain
    if status is None or status == NEW:
        return "new"
    if status == IGNORED:
        return "known"
    if status >= KNOWN:
        return "known" if form_seen else "novel-form"
    return "learning"
