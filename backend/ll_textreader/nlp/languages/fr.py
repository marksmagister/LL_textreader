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

# Bumped when the rules below change, so pipeline_id tells you which stored token
# streams are stale and need reprocessing (CLAUDE.md rule 6). 2 added the pronoun
# and sentence-initial rules below, which change lemmas rather than only morph.
# 3 fixed the second of those: it tested the first *token* of the sentence, and
# French dialogue opens on an em dash, so it missed every line of speech — which
# is exactly where imperatives live.
RULES = 3

# --------------------------------------------------------------- verb tense
#
# fr_core_news_md's morphologizer is good at gender and number and unreliable at
# tense and mood: measured over common forms it scored 8/16 and never once
# produced a conditional, reading `chanterais` as a present. Telling a learner
# that a conditional is a present is worse than saying nothing (rule 7).
#
# French endings are uniform across all verbs — only the stem varies — and the
# future and conditional are always built on a stem ending in -r (the infinitive
# for -er/-ir verbs, the infinitive minus -e for -re verbs). So a form can be
# classified against its own lemma with certainty, which is what the rules below
# do. Where they are silent the model's answer is used only where it is
# trustworthy; otherwise no tense is shown at all.

FUTURE_ENDINGS = ("ai", "as", "a", "ons", "ez", "ont")
# -ions/-iez are conditional on an -r stem, but elsewhere also present subjunctive
CONDITIONAL_ENDINGS = ("ais", "ait", "ions", "iez", "aient")
IMPERFECT_ENDINGS = ("ais", "ait", "aient")
# an ending that could belong to a tense other than the present
CONTESTED_ENDINGS = ("ais", "ait", "aient", "ions", "iez", "ai", "as", "ons", "ez", "ont")


def tense_from_form(surface: str, lemma: str) -> tuple[str, str] | None:
    """(Mood, Tense) when the ending settles it; None when it doesn't."""
    s, lem = surface.casefold(), lemma.casefold()
    stem = lem[:-1] if lem.endswith("re") else lem  # prendre -> prendr
    if s.startswith(stem) and len(s) > len(stem):
        suffix = s[len(stem) :]
        if suffix in CONDITIONAL_ENDINGS:
            return ("Cnd", "Pres")
        if suffix in FUTURE_ENDINGS:
            return ("Ind", "Fut")
    # Not built on the infinitive stem, so -ais/-ait/-aient is the imperfect —
    # unless it is an irregular conditional (serais, aurais), which also ends -rais.
    if s.endswith(IMPERFECT_ENDINGS) and not s.endswith(("rais", "rait", "raient")):
        return ("Ind", "Imp")
    return None


def refine_morph(surface: str, lemma: str, morph: str) -> str:
    """Correct the tagger's tense where the form decides it, and drop it where
    neither the rules nor the model can be trusted."""
    feats = dict(p.split("=", 1) for p in morph.split("|") if "=" in p)
    if feats.get("VerbForm") == "Part" or "Mood" not in feats:
        return morph  # participles and non-verbs are tagged reliably

    decided = tense_from_form(surface, lemma)
    if decided:
        feats["Mood"], feats["Tense"] = decided
    elif feats.get("Mood") == "Ind" and (
        feats.get("Tense") != "Fut" and surface.casefold().endswith(CONTESTED_ENDINGS)
    ):
        # the model collapses futures, conditionals and imperfects into the
        # present; where the ending shows it could be one of those, say nothing
        feats.pop("Mood", None)
        feats.pop("Tense", None)
    return "|".join(f"{k}={v}" for k, v in sorted(feats.items()))


class FrenchAdapter:
    lang = "fr"

    def __init__(self) -> None:
        self._alone_cache: dict[str, tuple[str, str] | None] = {}

    @cached_property
    def _nlp(self):
        import spacy

        return spacy.load(MODEL, exclude=["ner"])  # entities cost time, buy nothing here

    @property
    def pipeline_id(self) -> str:
        return f"spacy/{MODEL}@{self._nlp.meta['version']}+rules{RULES}"

    def _alone(self, word: str) -> tuple[str, str] | None:
        """Read one lowercase word out of context. A verb reading here beats
        PROPN at the start of a sentence; anything else is left alone.

        Cached: a page opens with a handful of these at most, and the same
        openers recur.
        """
        if word in self._alone_cache:
            return self._alone_cache[word]
        doc = self._nlp(word)
        got = None
        if len(doc) == 1 and doc[0].pos_ in ("VERB", "AUX"):
            got = (doc[0].lemma_.casefold(), doc[0].pos_)
        self._alone_cache[word] = got
        return got

    def analyse(self, text: str) -> list[AnalysedToken]:
        doc = self._nlp(text)
        # The first *word* of each sentence, not the first token: French dialogue
        # opens "— Tenez, voilà…", so the dash is the token and the capitalised
        # verb after it is what needs re-reading.
        sent_of, openers = {}, set()
        for sent_id, sent in enumerate(doc.sents):
            for tok in sent:
                sent_of[tok.i] = sent_id
            first = next((t for t in sent if any(c.isalpha() for c in t.text)), None)
            if first is not None:
                openers.add(first.i)

        out: list[AnalysedToken] = []
        for i, tok in enumerate(doc):
            if tok.is_space:
                continue
            norm = tok.text.casefold()
            lexical = any(c.isalpha() for c in tok.text)
            lemma, pos, morph = None, None, ""
            if lexical:
                lemma, pos = tok.lemma_.casefold(), tok.pos_
                # e.g. "Mood=Ind|Number=Sing|Person=3|Tense=Imp" for marchait —
                # already computed, and it is what explains the surface form.
                morph = refine_morph(tok.text, lemma, str(tok.morph))
                # Fall back to the surface form where the tagger admits defeat
                # (CLAUDE.md rule 7). spaCy gives no per-token score, so POS "X"
                # is the only honest signal there is; a wrong lemma is worse
                # than no lemma, because the failures are rare enough to confuse.
                if pos == "X":
                    lemma, pos = norm, "X"
                # UD collapses the third-person pronouns onto one lemma, so
                # `Elle` comes back as `lui` — and `lui` itself comes back as
                # `luire`, the verb, while still tagged PRON. Neither is usable
                # as vocabulary. Pronouns are closed-class and the form is the
                # thing you learn, so the form is the lemma.
                elif pos == "PRON":
                    lemma = norm
                # A capitalised word opening a sentence gets read as a name:
                # `Tenez, voici…` came back PROPN with the lemma `tenez`, while
                # `vous tenez` in the same text gave `tenir`. Read the lowercase
                # form on its own and take it only if it turns out to be a verb —
                # a real name does not ("Marc" alone is still no verb), so this
                # cannot quietly demote one.
                elif pos == "PROPN" and tok.i in openers:
                    guess = self._alone(norm)
                    if guess is not None:
                        lemma, pos = guess
                        morph = refine_morph(tok.text, lemma, "")
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


def adapter() -> FrenchAdapter:
    return FrenchAdapter()
