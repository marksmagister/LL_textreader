"""Italian: measured, and shipped with its weak spots written down.

Italian is the control in 0012 — the language where the novel-form state should
feel least necessary, so that Russian either earns it or does not. It gets the
same measurement Russian and French got, and unlike them it gets no rules: what
it is bad at cannot be fixed from the form with certainty, so the honest answer
is the surface form and the `o` override. See decision 0021.
"""

import pytest

from ll_textreader.importers.plain_text import clean
from ll_textreader.nlp.languages import get_adapter

pytest.importorskip("it_core_news_md", reason="run scripts/setup-models.sh it")

TEXT = "Le ragazze parlavano delle vacanze. Ieri ho mangiato una pizza con i miei amici."


@pytest.fixture(scope="module")
def tokens():
    return get_adapter("it").analyse(clean(TEXT))


def by_surface(tokens, surface):
    return next(t for t in tokens if t.surface == surface)


def test_offsets_index_into_the_text(tokens):
    body = clean(TEXT)
    for t in tokens:
        assert body[t.char_start : t.char_end] == t.surface


def test_inflected_forms_reduce_to_one_lemma(tokens):
    assert by_surface(tokens, "parlavano").lemma == "parlare"
    assert by_surface(tokens, "mangiato").lemma == "mangiare"
    assert by_surface(tokens, "ragazze").lemma == "ragazza"
    assert by_surface(tokens, "amici").lemma == "amico"


def test_pos_is_tagged_so_homographs_can_differ(tokens):
    assert by_surface(tokens, "ragazze").pos == "NOUN"
    assert by_surface(tokens, "parlavano").pos == "VERB"


def test_punctuation_is_not_a_lexical_token(tokens):
    assert by_surface(tokens, ".").lemma is None


def test_morphology_is_kept(tokens):
    m = by_surface(tokens, "parlavano").morph
    assert "Tense=Imp" in m and "Number=Plur" in m
    assert "Person=3" in m  # 1/2/3, the way French writes it — unlike Russian


def test_pipeline_id_is_stamped():
    assert get_adapter("it").pipeline_id.startswith("spacy/it_core_news_md@")


def test_a_contraction_keeps_its_multi_word_lemma(tokens):
    """`delle` is di + le, and the model says so: the lemma is the two words.

    Left as it comes. It is a function word, it is truthful, and inventing a
    single-word lemma for it would be a decision about Italian rather than a
    correction — see 0021.
    """
    assert by_surface(tokens, "delle").lemma == "di il"


# The same shape as the Russian table: scored, not asserted one by one, because
# the model gets three of these wrong and the point is to know which.
CASES: list[tuple[str, dict[str, tuple[str, str, dict[str, str]]]]] = [
    ("Mi chiamo Marco.", {"chiamo": ("chiamare", "VERB", {"Person": "1", "Number": "Sing"})}),
    ("Io abito a Roma da tre anni.", {"abito": ("abitare", "VERB", {"Person": "1"})}),
    ("Tu parli molto bene.", {"parli": ("parlare", "VERB", {"Person": "2"})}),
    ("Lei lavora in un ufficio.", {"lavora": ("lavorare", "VERB", {"Person": "3"})}),
    ("Noi mangiamo insieme.", {"mangiamo": ("mangiare", "VERB", {"Number": "Plur"})}),
    ("Ieri ho mangiato una pizza.", {"mangiato": ("mangiare", "VERB", {"VerbForm": "Part"})}),
    (
        "Le ragazze parlavano delle vacanze.",
        {
            "parlavano": ("parlare", "VERB", {"Tense": "Imp", "Number": "Plur"}),
            "ragazze": ("ragazza", "NOUN", {"Gender": "Fem", "Number": "Plur"}),
        },
    ),
    ("Domani andremo al mare.", {"andremo": ("andare", "VERB", {"Tense": "Fut"})}),
    ("Vorrei un caffè.", {"Vorrei": ("volere", "VERB", {"Mood": "Cnd", "Person": "1"})}),
    ("Se avessi tempo, verrei.", {"verrei": ("venire", "VERB", {"Mood": "Cnd"})}),
    ("I bambini sono felici.", {"felici": ("felice", "ADJ", {"Number": "Plur"})}),
    ("Questa casa è molto grande.", {"casa": ("casa", "NOUN", {"Gender": "Fem"})}),
    ("Ho comprato due libri nuovi.", {"libri": ("libro", "NOUN", {"Number": "Plur"})}),
    ("Lui non capisce niente.", {"capisce": ("capire", "VERB", {"Person": "3"})}),
    ("Siamo arrivati alle otto.", {"arrivati": ("arrivare", "VERB", {"VerbForm": "Part"})}),
    ("Devo andare a casa adesso.", {"Devo": ("dovere", "AUX", {"Person": "1"})}),
]

# Measured September 2026 against it_core_news_md 3.8.0, over 17 targets. The
# lemma misses are `chiamo`, `andremo` (`andre`) and `verrei` (`velere`) — a
# first-person singular and two invented future/conditional stems.
FLOOR = {"lemma": 14, "pos": 17, "Person": 6, "Number": 5, "Tense": 2}


def test_the_measurement_holds():
    adapter = get_adapter("it")
    score: dict[str, int] = {}

    def hit(key: str, ok: bool) -> None:
        score[key] = score.get(key, 0) + int(ok)

    for text, targets in CASES:
        got = {t.surface: t for t in adapter.analyse(text)}
        for surface, (lemma, pos, feats) in targets.items():
            tok = got[surface]
            hit("lemma", tok.lemma == lemma)
            hit("pos", tok.pos == pos)
            have = dict(p.split("=", 1) for p in tok.morph.split("|") if "=" in p)
            for k, v in feats.items():
                hit(k, have.get(k) == v)

    worse = {k: (score.get(k, 0), floor) for k, floor in FLOOR.items() if score.get(k, 0) < floor}
    assert not worse, f"got (score, floor): {worse}"
