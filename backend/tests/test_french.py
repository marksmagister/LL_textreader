"""The French adapter against the real model. Skipped if it isn't downloaded."""

import pytest

from ll_textreader.importers.plain_text import clean
from ll_textreader.nlp.languages import get_adapter

pytest.importorskip("fr_core_news_md", reason="run scripts/setup-models.sh fr")

TEXT = "Il marchait le long du quai. Les portes des maisons étaient fermées."


@pytest.fixture(scope="module")
def tokens():
    return get_adapter("fr").analyse(clean(TEXT))


def by_surface(tokens, surface):
    return next(t for t in tokens if t.surface == surface)


def test_offsets_index_into_the_text(tokens):
    body = clean(TEXT)
    for t in tokens:
        assert body[t.char_start : t.char_end] == t.surface


def test_inflected_forms_reduce_to_one_lemma(tokens):
    assert by_surface(tokens, "marchait").lemma == "marcher"
    assert by_surface(tokens, "étaient").lemma == "être"
    assert by_surface(tokens, "maisons").lemma == "maison"


def test_pos_is_tagged_so_homographs_can_differ(tokens):
    porte = by_surface(tokens, "portes")
    assert porte.pos == "NOUN" and porte.lemma == "porte"
    assert by_surface(tokens, "marchait").pos == "VERB"


def test_punctuation_is_not_a_lexical_token(tokens):
    assert by_surface(tokens, ".").lemma is None


def test_elision_is_split():
    """l'eau is two tokens; the status of `eau` must not be tangled with the article."""
    parts = get_adapter("fr").analyse("Il regardait le reflet dans l'eau.")
    assert [t.surface for t in parts if t.surface in ("l'", "eau")] == ["l'", "eau"]


def test_pipeline_id_is_stamped():
    assert get_adapter("fr").pipeline_id.startswith("spacy/fr_core_news_md@")


def test_morphology_is_kept(tokens):
    """The tagger computes this anyway; it is what explains the surface form."""
    m = by_surface(tokens, "marchait").morph
    assert "Tense=Imp" in m and "Person=3" in m and "Number=Sing" in m
    assert "Number=Plur" in by_surface(tokens, "maisons").morph
    assert by_surface(tokens, ".").morph == ""
