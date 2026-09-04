"""Russian and Italian: the plain-spaCy adapters. The heavy checks need the
models; this pins the wiring that does not."""

import pytest

from ll_textreader.nlp.languages import UnknownLanguage, get_adapter
from ll_textreader.nlp.languages._spacy import SpacyAdapter


def test_ru_and_it_resolve_to_spacy_adapters():
    for lang, model in (("ru", "ru_core_news_md"), ("it", "it_core_news_md")):
        adapter = get_adapter(lang)
        assert isinstance(adapter, SpacyAdapter)
        assert adapter.lang == lang
        assert adapter.MODEL == model


def test_unknown_language_still_raises():
    with pytest.raises(UnknownLanguage):
        get_adapter("xx")


@pytest.mark.parametrize("lang", ["ru", "it"])
def test_analyse_against_the_real_model(lang):
    spacy = pytest.importorskip(
        {"ru": "ru_core_news_md", "it": "it_core_news_md"}[lang],
        reason=f"run scripts/setup-models.sh {lang}",
    )
    del spacy
    text = "Она читает книгу." if lang == "ru" else "Lei legge un libro."
    tokens = get_adapter(lang).analyse(text)
    # Offsets index straight into the text (CLAUDE.md rule 2).
    for t in tokens:
        assert text[t.char_start : t.char_end] == t.surface
    # A lexical token got a lemma; punctuation did not.
    assert any(t.lemma and t.pos for t in tokens)
    assert any(t.lemma is None for t in tokens)
