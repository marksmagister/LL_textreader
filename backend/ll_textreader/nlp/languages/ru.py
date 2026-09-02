"""Russian: spaCy, POS-tagged lemmas.

Runs at import, never at render (CLAUDE.md rule 1).

Measured before it was trusted, the way French was — sixteen sentences of A2-B1
Russian, in `tests/test_russian.py`, and the numbers are in
`docs/decisions/0021-russian-and-italian-measured.md`. The prediction in 0012 was
that aspect would be the risk; it scored 11/11 and case 12/12. The two things
that were actually wrong are the rules below.
"""

from functools import cached_property

from ...models import AnalysedToken

MODEL = "ru_core_news_md"

# Bumped when the rules below change, so pipeline_id tells you which stored token
# streams are stale and need reprocessing (CLAUDE.md rule 6).
RULES = 1

# ------------------------------------------------------------------ person
#
# ru_core_news_md writes Person=First/Second/Third where every other model in the
# project writes Person=1/2/3. Nothing is wrong with either, but the reader has
# one table for all languages, so a Russian verb would have shown no person at
# all — silently, which is the worst way for it to fail.
PERSON = {"First": "1", "Second": "2", "Third": "3"}

# --------------------------------------------------------------- pronouns
#
# The oblique personal pronouns come back unlemmatised: `меня`, `мне` and `мной`
# are their own lemmas, so `я` splits into four vocabulary entries and the most
# frequent words in the language are the ones the lexicon counts worst. (The
# model does lemmatise them when it reads them as possessive determiners —
# `Его книга` gives `он` — so this is a gap rather than a disagreement.)
#
# Mapping them onto the nominative is what makes the design work here: mark `я`
# known and `меня` becomes a *novel form* — you know the word, not this shape of
# it — which is exactly the distinction CLAUDE.md calls the point of the whole
# thing. These are closed-class facts of Russian, not a guess about a model's
# confidence, so rule 7 does not apply.
#
# Masculine and neuter share their oblique forms, and UD resolves them onto `он`;
# this follows that rather than inventing a convention.
PRONOUN_LEMMAS = {
    "меня": "я", "мне": "я", "мной": "я", "мною": "я",
    "тебя": "ты", "тебе": "ты", "тобой": "ты", "тобою": "ты",
    "его": "он", "него": "он", "ему": "он", "нему": "он", "нём": "он", "нем": "он",
    "её": "она", "неё": "она", "ее": "она", "нее": "она",
    "ей": "она", "ней": "она", "ею": "она", "нею": "она",
    "нас": "мы", "нам": "мы", "нами": "мы",
    "вас": "вы", "вам": "вы", "вами": "вы",
    "их": "они", "них": "они", "ими": "они", "ними": "они",
    "себе": "себя", "собой": "себя", "собою": "себя",
}  # fmt: skip

# `им` and `ним` are он in the singular and они in the plural. The tagger's
# Number scored 11/12 on the measurement, and it is the only thing that can tell
# them apart, so it is what decides.
PRONOUNS_BY_NUMBER = {
    "им": {"Sing": "он", "Plur": "они"},
    "ним": {"Sing": "он", "Plur": "они"},
}


def refine_morph(morph: str) -> str:
    """Person=Third -> Person=3, and nothing else. The rest measured clean."""
    if "Person=" not in morph:
        return morph
    feats = dict(p.split("=", 1) for p in morph.split("|") if "=" in p)
    feats["Person"] = PERSON.get(feats["Person"], feats["Person"])
    return "|".join(f"{k}={v}" for k, v in sorted(feats.items()))


def pronoun_lemma(norm: str, morph: str) -> str | None:
    """The nominative this oblique pronoun belongs to, or None if it isn't one."""
    if norm in PRONOUNS_BY_NUMBER:
        feats = dict(p.split("=", 1) for p in morph.split("|") if "=" in p)
        # No Number, no answer: guessing which of two words this is would be
        # worse than leaving the form to stand for itself (CLAUDE.md rule 7).
        return PRONOUNS_BY_NUMBER[norm].get(feats.get("Number", ""))
    return PRONOUN_LEMMAS.get(norm)


class RussianAdapter:
    lang = "ru"

    @cached_property
    def _nlp(self):
        import spacy

        return spacy.load(MODEL, exclude=["ner"])  # entities cost time, buy nothing here

    @property
    def pipeline_id(self) -> str:
        return f"spacy/{MODEL}@{self._nlp.meta['version']}+rules{RULES}"

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
                morph = refine_morph(str(tok.morph))
                # Fall back to the surface form where the tagger admits defeat
                # (CLAUDE.md rule 7). spaCy gives no per-token score, so POS "X"
                # is the only honest signal there is.
                if pos == "X":
                    lemma, pos = norm, "X"
                elif pos == "PRON":
                    lemma = pronoun_lemma(norm, morph) or lemma
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


def adapter() -> RussianAdapter:
    return RussianAdapter()
