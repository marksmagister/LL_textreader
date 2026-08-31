"""French: spaCy, POS-tagged lemmas.

Runs at import, never at render (CLAUDE.md rule 1).
"""

from functools import cached_property

from ...models import AnalysedToken

# _md, not _lg: the difference between them is static word vectors, which nothing
# here uses. Lemmas and POS tags are the same and it is 45MB instead of 545MB.
# Switching model is this constant; pipeline_id then tells you which lessons are
# stale and need reprocessing (CLAUDE.md rule 6).
MODEL = "fr_core_news_md"

# Below this, trust the surface form instead of the lemma (CLAUDE.md rule 7).
# A wrong lemma is worse than no lemma, because the failures are rare enough to
# be confusing. spaCy gives no per-token score, so the only honest signal is the
# tagger admitting it doesn't know: POS "X".
MIN_CONFIDENCE = 0.5


class FrenchAdapter:
    lang = "fr"

    @cached_property
    def _nlp(self):
        import spacy

        return spacy.load(MODEL, exclude=["ner"])  # entities cost time, buy nothing here

    @property
    def pipeline_id(self) -> str:
        return f"spacy/{MODEL}@{self._nlp.meta['version']}"

    def analyse(self, text: str) -> list[AnalysedToken]:
        doc = self._nlp(text)
        sent_of = {}
        for sent_id, sent in enumerate(doc.sents):
            for tok in sent:
                sent_of[tok.i] = sent_id

        out: list[AnalysedToken] = []
        for i, tok in enumerate(doc):
            if tok.is_space:
                continue
            norm = tok.text.casefold()
            lexical = any(c.isalpha() for c in tok.text)
            lemma, pos, confidence = None, None, 1.0
            if lexical:
                lemma, pos = tok.lemma_.casefold(), tok.pos_
                if pos == "X":
                    lemma, pos, confidence = norm, "X", 0.0
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
                    confidence=confidence,
                )
            )
        return out


def adapter() -> FrenchAdapter:
    return FrenchAdapter()
