"""A plain spaCy adapter: POS-tagged lemmas, offsets, sentence ids.

`fr.py` does not use this — French carries hand-written tense rules and a pile of
report fixes that make its `analyse` genuinely different. This is the shared body
for the languages that (for now) trust the model as it comes: Russian, Italian.
Bump `RULES` here if that stops being true and note which languages care.

Runs at import, never at render (CLAUDE.md rule 1). Char offsets are absolute
into the lesson body (rule 2). Low-confidence output falls back to the surface
form (rule 7): spaCy gives no per-token score, so POS ``X`` is the only signal.
"""

from functools import cached_property

from ...models import AnalysedToken

RULES = 1


class SpacyAdapter:
    """Subclass and set ``lang`` and ``MODEL``. Nothing else is required."""

    lang: str
    MODEL: str

    @cached_property
    def _nlp(self):
        import spacy

        return spacy.load(self.MODEL, exclude=["ner"])  # entities cost time, buy nothing

    @property
    def pipeline_id(self) -> str:
        return f"spacy/{self.MODEL}@{self._nlp.meta['version']}+base{RULES}"

    def analyse(self, text: str) -> list[AnalysedToken]:
        doc = self._nlp(text)

        sent_of: dict[int, int] = {}
        for sent_id, sent in enumerate(doc.sents):
            for tok in sent:
                sent_of[tok.i] = sent_id

        out: list[AnalysedToken] = []
        for i, tok in enumerate(doc):
            if tok.is_space:
                continue
            norm = tok.text.casefold()
            lemma: str | None = None
            pos: str | None = None
            morph = ""
            if any(c.isalpha() for c in tok.text):
                lemma, pos = tok.lemma_.casefold(), tok.pos_
                morph = str(tok.morph)
                if pos == "X":
                    # The tagger admitting defeat. A wrong lemma is a wrong entry
                    # in the lexicon, not just a wrong colour, so surface it.
                    lemma = norm
                elif pos == "PRON":
                    # Pronouns are closed-class and UD collapses them onto shared
                    # lemmas ("elle" -> "lui"). The form is the thing you learn.
                    lemma = norm
            out.append(
                AnalysedToken(
                    idx=len(out),
                    surface=tok.text,
                    norm=norm,
                    lemma=lemma,
                    pos=pos,
                    char_start=tok.idx,
                    char_end=tok.idx + len(tok.text),
                    sent_id=sent_of.get(i, 0),
                    morph=morph,
                )
            )
        return out
