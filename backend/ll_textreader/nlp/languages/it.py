"""Italian: spaCy, POS-tagged lemmas.

Runs at import, never at render (CLAUDE.md rule 1).

No rules, deliberately. Italian was measured alongside Russian
(`tests/test_italian.py`, `docs/decisions/0021-russian-and-italian-measured.md`)
and it has two real weaknesses — first-person singular `-o` forms, and invented
future/conditional stems — but neither can be corrected *with certainty* from the
form the way French tense can, and a confident wrong lemma is worse than none
(CLAUDE.md rule 7). Where the lemmatiser gives up it already returns the surface
form, which is the honest answer; the rest is what the `o` override is for.
"""

from functools import cached_property

from ...models import AnalysedToken

MODEL = "it_core_news_md"


class ItalianAdapter:
    lang = "it"

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
            lemma, pos, morph = None, None, ""
            if lexical:
                lemma, pos = tok.lemma_.casefold(), tok.pos_
                morph = str(tok.morph)
                # Fall back to the surface form where the tagger admits defeat
                # (CLAUDE.md rule 7). spaCy gives no per-token score, so POS "X"
                # is the only honest signal there is.
                if pos == "X":
                    lemma, pos = norm, "X"
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


def adapter() -> ItalianAdapter:
    return ItalianAdapter()
