"""The texts a language starts with, and the library filtered by language."""

import pytest

from ll_textreader import starters
from ll_textreader.nlp import languages

from .conftest import StubAdapter


@pytest.fixture
def multilingual(client, monkeypatch):
    """The stub stands in for spaCy in every language; only `analyse` is used."""
    for lang in ("it", "ru"):
        monkeypatch.setitem(languages._cache, lang, StubAdapter())
    return client


def test_every_language_that_ships_starters_can_be_read(client):
    """A starter for a language with no adapter would be a button that 500s."""
    for lang in (p.name for p in starters.DIR.iterdir() if p.is_dir()):
        assert (starters.DIR / lang).exists()
        assert starters.available(lang), f"{lang} has a folder but no texts"


def test_the_title_is_the_first_line():
    got = starters.available("it")
    assert [title for _, title, _ in got] == [
        "Mi chiamo Elena",
        "Al bar",
        "La giornata di Elena",
    ]


def test_the_folder_is_the_collection():
    assert {collection for collection, _, _ in starters.available("it")} == {"Primi passi"}
    assert {collection for collection, _, _ in starters.available("ru")} == {"Первые шаги"}


def test_the_title_line_stays_in_the_body():
    """It is text you read, so it should be coloured and count — the same reason
    `with_title` puts a pasted title into the body."""
    _, title, body = starters.available("it")[0]
    assert body.startswith(title)


def test_an_unknown_language_has_none():
    assert starters.available("xx") == []


def test_installing_puts_them_in_the_library_in_order(multilingual):
    made = multilingual.post("/api/lessons/starters", json={"lang": "it"})
    assert made.status_code == 201
    assert [lesson["title"] for lesson in made.json()] == [
        "Mi chiamo Elena",
        "Al bar",
        "La giornata di Elena",
    ]
    assert {lesson["collection"] for lesson in made.json()} == {"Primi passi"}
    assert [lesson["position"] for lesson in made.json()] == [1, 2, 3]


def test_pressing_twice_makes_no_duplicates(multilingual):
    multilingual.post("/api/lessons/starters", json={"lang": "it"})
    again = multilingual.post("/api/lessons/starters", json={"lang": "it"})
    assert again.json() == []
    assert len(multilingual.get("/api/lessons?lang=it").json()) == 3


def test_a_deleted_starter_can_be_put_back(multilingual):
    made = multilingual.post("/api/lessons/starters", json={"lang": "it"}).json()
    multilingual.delete(f"/api/lessons/{made[0]['id']}")
    back = multilingual.post("/api/lessons/starters", json={"lang": "it"}).json()
    assert [lesson["title"] for lesson in back] == ["Mi chiamo Elena"]


def test_listing_says_what_you_already_have(multilingual):
    before = multilingual.get("/api/lessons/starters?lang=it").json()
    assert [s["imported"] for s in before] == [False, False, False]
    multilingual.post("/api/lessons/starters", json={"lang": "it"})
    after = multilingual.get("/api/lessons/starters?lang=it").json()
    assert [s["imported"] for s in after] == [True, True, True]


def test_the_starters_route_is_not_read_as_a_lesson_id(multilingual):
    """Routes match in declaration order; the wrong order is a 422 here."""
    assert multilingual.get("/api/lessons/starters?lang=it").status_code == 200


def test_the_library_can_be_asked_for_one_language(multilingual):
    multilingual.post("/api/lessons/starters", json={"lang": "it"})
    multilingual.post("/api/lessons/starters", json={"lang": "ru"})
    assert len(multilingual.get("/api/lessons").json()) == 6
    assert len(multilingual.get("/api/lessons?lang=it").json()) == 3
    assert {lesson["lang"] for lesson in multilingual.get("/api/lessons?lang=ru").json()} == {"ru"}


def test_a_language_with_no_starters_is_not_an_error(multilingual):
    assert multilingual.get("/api/lessons/starters?lang=fr").json() == []
    assert multilingual.post("/api/lessons/starters", json={"lang": "fr"}).json() == []
