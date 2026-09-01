"""Types shared between the pipeline, the DB and the API.

Mirrored by frontend/src/types.ts — keep the two in step.
"""

from typing import Literal

from pydantic import BaseModel, Field

# blue / yellow / dotted / lighter / plain. See docs/data-model.md.
TokenState = Literal["new", "learning", "review", "novel-form", "known"]

NEW, LEARNING, REVIEW, KNOWN, IGNORED = 0, 1, 4, 5, -1


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
    morph: str = ""  # UD features, e.g. "Number=Sing|Tense=Imp"
    confidence: float = 1.0


class ReaderToken(BaseModel):
    """A token as the reader sees it: the pipeline's output joined with your lexicon."""

    idx: int
    surface: str
    lemma: str | None
    pos: str | None
    char_start: int
    char_end: int
    sent_id: int  # for sentence-at-a-time keyboard navigation
    morph: str  # why this form looks different from the lemma
    overridden: bool  # the user has corrected the lemmatiser on this form
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
    completed: bool = False
    n_new: int = 0
    n_learning: int = 0
    n_known: int = 0
    # set only by a bulk action, so the reader can offer to put it back
    undo_id: int | None = None
    undo_n: int = 0


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


class OverrideRequest(BaseModel):
    """ "The lemmatiser is wrong about this word." CLAUDE.md rule 5.

    With no to_lemma, the surface form is detached and becomes its own entry —
    which is the common case: you don't want to retype the word, you want the
    reader to stop pretending it is something else.
    """

    lang: str
    surface: str
    from_lemma: str | None = None  # what the pipeline said, kept for audit
    to_lemma: str | None = None
    to_pos: str = "X"


class VocabEntry(BaseModel):
    lemma: str
    pos: str
    status: int
    note: str | None
    updated_at: str
    forms: list[str]  # the inflections you have actually met
    met: int  # times seen on a page you finished — what the level is counted from


class Vocab(BaseModel):
    total: int
    by_status: dict[str, int]
    entries: list[VocabEntry]


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
    # You have met this often enough that the app should stop guessing and ask.
    # Only you get to say a word is known (decision 0008).
    return "review" if status >= REVIEW else "learning"
