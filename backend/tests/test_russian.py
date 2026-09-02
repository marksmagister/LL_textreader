"""Russian: the rules, and the measurement they came out of.

0012 said to measure the morphology before trusting it, the way French was
measured, and to expect case to be reasonable and aspect to be the risk. The
opposite happened — aspect 11/11, case 12/12 — and what was actually broken was
person and the oblique pronouns. Both now have rules; this is what keeps them
honest when the model is next upgraded.

The scores below are floors, not targets. A model upgrade that raises them is
welcome and should raise the floor with it; one that lowers them is a decision
to make, not a test to delete.
"""

import pytest

from ll_textreader.importers.plain_text import clean
from ll_textreader.nlp.languages import get_adapter
from ll_textreader.nlp.languages.ru import pronoun_lemma, refine_morph

# ---------------------------------------------------------------- pure rules
# No model needed: these are the two things the measurement found wrong.


@pytest.mark.parametrize(
    "morph,expected",
    [
        ("Mood=Ind|Number=Sing|Person=First|Tense=Pres", "Person=1"),
        ("Mood=Ind|Number=Sing|Person=Second|Tense=Pres", "Person=2"),
        ("Mood=Ind|Number=Sing|Person=Third|Tense=Pres", "Person=3"),
    ],
)
def test_person_is_written_the_way_every_other_language_writes_it(morph, expected):
    """Person=Third would have shown nothing at all: the reader has one table."""
    assert expected in refine_morph(morph)


def test_features_that_measured_clean_are_left_alone():
    morph = "Animacy=Inan|Case=Loc|Gender=Masc|Number=Sing"
    assert refine_morph(morph) == morph


@pytest.mark.parametrize(
    "surface,expected",
    [
        ("меня", "я"),
        ("мне", "я"),
        ("тебя", "ты"),
        ("его", "он"),
        ("ему", "он"),
        ("неё", "она"),
        ("нас", "мы"),
        ("вам", "вы"),
        ("них", "они"),
        ("себе", "себя"),
    ],
)
def test_oblique_pronouns_reduce_to_the_nominative(surface, expected):
    """So marking `я` known leaves `меня` dashed — a shape you have not met —
    rather than a second word you have never seen."""
    assert pronoun_lemma(surface, "") == expected


def test_number_settles_the_two_ambiguous_forms():
    assert pronoun_lemma("им", "Case=Ins|Number=Sing") == "он"
    assert pronoun_lemma("им", "Case=Dat|Number=Plur") == "они"


def test_an_ambiguous_form_with_no_number_is_left_alone():
    """Guessing which of two words this is would be worse than not lemmatising."""
    assert pronoun_lemma("им", "") is None


def test_a_word_that_is_not_a_pronoun_is_not_touched():
    assert pronoun_lemma("книга", "") is None


# ------------------------------------------------------------ the real model

pytest.importorskip("ru_core_news_md", reason="run scripts/setup-models.sh ru")

TEXT = "Вчера я прочитал интересную книгу о старом городе. Мне она очень понравилась."


@pytest.fixture(scope="module")
def tokens():
    return get_adapter("ru").analyse(clean(TEXT))


def by_surface(tokens, surface):
    return next(t for t in tokens if t.surface == surface)


def test_offsets_index_into_the_text(tokens):
    body = clean(TEXT)
    for t in tokens:
        assert body[t.char_start : t.char_end] == t.surface


def test_inflected_forms_reduce_to_one_lemma(tokens):
    assert by_surface(tokens, "прочитал").lemma == "прочитать"
    assert by_surface(tokens, "книгу").lemma == "книга"
    assert by_surface(tokens, "городе").lemma == "город"


def test_the_pronoun_rule_reaches_the_pipeline(tokens):
    assert by_surface(tokens, "Мне").lemma == "я"


def test_person_reaches_the_pipeline():
    """The rule is useless if it only exists in a unit test."""
    got = get_adapter("ru").analyse("Я пишу письмо.")
    assert "Person=1" in next(t for t in got if t.surface == "пишу").morph


def test_pipeline_id_is_stamped(tokens):
    assert get_adapter("ru").pipeline_id.startswith("spacy/ru_core_news_md@")
    assert "+rules" in get_adapter("ru").pipeline_id


def test_aspect_pairs_stay_different_words():
    """читать and прочитать are different vocabulary items — 0012, and the same
    argument as the Arabic root in CLAUDE.md rule 4."""
    got = get_adapter("ru").analyse("Я читал книгу. Я прочитал книгу.")
    assert by_surface(got, "читал").lemma == "читать"
    assert by_surface(got, "прочитал").lemma == "прочитать"


def test_yo_and_ye_are_not_folded():
    """всё and все are different words; folding them would merge them (0012)."""
    got = get_adapter("ru").analyse("Все пришли. Всё хорошо.")
    assert by_surface(got, "Все").norm != by_surface(got, "Всё").norm


# --------------------------------------------------------------- the table
#
# Sixteen sentences of A2-B1 Russian with the lemma, POS and features they
# actually are. Scored rather than asserted one by one, because three of them the
# model gets wrong and pretending otherwise would be the lie this table exists to
# prevent. What the failures are is in decision 0021.

CASES: list[tuple[str, dict[str, tuple[str, str, dict[str, str]]]]] = [
    ("Я живу в большом городе.", {"городе": ("город", "NOUN", {"Case": "Loc", "Number": "Sing"})}),
    ("У меня нет свободного времени.", {"времени": ("время", "NOUN", {"Case": "Gen"})}),
    (
        "Мы говорили о новых книгах.",
        {
            "книгах": ("книга", "NOUN", {"Case": "Loc", "Number": "Plur"}),
            "новых": ("новый", "ADJ", {"Case": "Loc", "Number": "Plur"}),
        },
    ),
    (
        "Она написала письмо брату.",
        {
            "брату": ("брат", "NOUN", {"Case": "Dat", "Number": "Sing"}),
            "написала": ("написать", "VERB", {"Aspect": "Perf", "Tense": "Past", "Gender": "Fem"}),
        },
    ),
    ("Он идёт в парк с другом.", {"другом": ("друг", "NOUN", {"Case": "Ins"})}),
    (
        "Я вижу большую собаку.",
        {
            "собаку": ("собака", "NOUN", {"Case": "Acc", "Number": "Sing"}),
            "большую": ("большой", "ADJ", {"Case": "Acc"}),
        },
    ),
    ("Вчера я читал интересную книгу.", {"читал": ("читать", "VERB", {"Aspect": "Imp"})}),
    ("Вчера я прочитал эту книгу.", {"прочитал": ("прочитать", "VERB", {"Aspect": "Perf"})}),
    (
        "Завтра я напишу письмо.",
        {"напишу": ("написать", "VERB", {"Aspect": "Perf", "Tense": "Fut", "Person": "1"})},
    ),
    ("Завтра я буду читать книгу.", {"читать": ("читать", "VERB", {"VerbForm": "Inf"})}),
    (
        "Он часто пишет письма.",
        {"пишет": ("писать", "VERB", {"Tense": "Pres", "Person": "3"})},
    ),
    (
        "Скажите, пожалуйста, где находится метро.",
        {"Скажите": ("сказать", "VERB", {"Aspect": "Perf", "Mood": "Imp"})},
    ),
    (
        "Эта книга была написана известным писателем.",
        {
            "написана": ("написать", "VERB", {"Aspect": "Perf", "Voice": "Pass"}),
            "писателем": ("писатель", "NOUN", {"Case": "Ins", "Number": "Sing"}),
        },
    ),
    (
        "Он занимается спортом каждый день.",
        {
            "занимается": ("заниматься", "VERB", {"Aspect": "Imp", "Tense": "Pres"}),
            "спортом": ("спорт", "NOUN", {"Case": "Ins"}),
        },
    ),
    (
        "Дети играли во дворе.",
        {
            "играли": ("играть", "VERB", {"Aspect": "Imp", "Tense": "Past", "Number": "Plur"}),
            "дворе": ("двор", "NOUN", {"Case": "Loc"}),
        },
    ),
    ("Я его давно не видел.", {"видел": ("видеть", "VERB", {"Aspect": "Imp", "Tense": "Past"})}),
]

# Measured September 2026 against ru_core_news_md 3.8.0, over 22 targets. Case
# and aspect are perfect; the two lemma misses are `другом` (read as a pronoun)
# and `большую` (given the comparative `больший`), and they are what the `o`
# override exists for.
FLOOR = {"lemma": 20, "pos": 21, "Aspect": 9, "Case": 11, "Tense": 6, "Person": 2}


def test_the_measurement_holds():
    adapter = get_adapter("ru")
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
