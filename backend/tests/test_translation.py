"""Sentence translation: cached, on demand, and absent without the extra."""

import pytest

from ll_textreader import translate
from ll_textreader.api import lessons

TEXT = "Le chat dort. La pluie tombe. Le train part."


class StubTranslator:
    """Stands in for a 450MB model. Counts calls, so caching can be asserted."""

    name = "stub/fr-en"
    calls = 0

    def translate(self, sentences):
        StubTranslator.calls += 1
        return [f"<{s}>" for s in sentences]


@pytest.fixture
def stub(monkeypatch):
    StubTranslator.calls = 0
    monkeypatch.setitem(translate._cache, ("fr", "en"), StubTranslator())
    return StubTranslator


def make(client, text=TEXT):
    return client.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]


def test_a_page_gets_one_translation_per_sentence(client, stub):
    lesson = make(client)
    out = client.get(f"/api/lessons/{lesson}/translation").json()
    assert len(out) == 3
    assert out["0"].startswith("<Le chat dort")


def test_translations_are_kept_not_recomputed(client, stub):
    """The toggle has to be instant the second time."""
    lesson = make(client)
    client.get(f"/api/lessons/{lesson}/translation")
    assert stub.calls == 1
    client.get(f"/api/lessons/{lesson}/translation")
    client.get(f"/api/lessons/{lesson}/translation")
    assert stub.calls == 1


def test_only_the_page_you_are_on_is_translated(client, stub, monkeypatch):
    """A book should not translate itself the moment you flip the switch."""
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 5)
    lesson = make(client)
    first = client.get(f"/api/lessons/{lesson}/translation?page=0").json()
    assert len(first) < 3

    second = client.get(f"/api/lessons/{lesson}/translation?page=1").json()
    assert set(first) & set(second) == set()  # different sentences, no overlap


def test_sentences_are_sliced_from_the_body_not_rebuilt(client, stub):
    """CLAUDE.md rule 2 again: punctuation and spacing must survive."""
    lesson = make(client, "L'eau est froide. Il n'y a personne.")
    out = client.get(f"/api/lessons/{lesson}/translation").json()
    assert "L'eau est froide." in out["0"]
    assert "n'y a personne." in out["1"]


def test_without_the_optional_extra_it_is_unavailable_not_broken(client, monkeypatch):
    lesson = make(client)
    monkeypatch.delitem(translate._cache, ("fr", "en"), raising=False)

    def missing(*a, **k):
        raise translate.Unavailable("uv sync --extra translate")

    monkeypatch.setattr(translate, "get_translator", missing)
    assert client.get(f"/api/lessons/{lesson}/translation").status_code == 503


def test_an_unknown_pair_is_refused_rather_than_guessed(client):
    with pytest.raises(translate.Unavailable):
        translate.get_translator("fr", "de")
