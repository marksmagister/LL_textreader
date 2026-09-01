"""Levels are counted from exposure, not self-assessment (decision 0008).

An encounter is one page. Not one occurrence — a word three times in a paragraph
is still one meeting, and what makes a repeat worth anything is the delay before
it. Not one button press either: turning the same page twice is not two
encounters, and the page you were on when you flagged a word is the meeting that
made you flag it, not a further one.
"""

import pytest

from ll_textreader.api import lessons

# `quai` on every page; `marcher` only on the first.
TEXT = (
    "Il marchait le long du quai. "
    "Une mouette passait sur le quai. "
    "Le brouillard couvrait le quai. "
    "Une cloche sonnait sur le quai. "
    "La pluie tombait sur le quai. "
)


@pytest.fixture
def lesson(client, monkeypatch):
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 8)  # one sentence per page
    return client.post("/api/lessons", json={"text": TEXT, "lang": "fr"}).json()["id"]


def status_of(client, lemma="quai"):
    entry = next(
        (e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == lemma),
        None,
    )
    return entry and entry["status"]


def learn(client, lemma="quai", **extra):
    # The reader always sends the form you were looking at, so the tests do too —
    # without it every other form of the word reads as novel, which is correct
    # but not what these tests are about.
    client.put(
        "/api/terms",
        json={
            "lang": "fr",
            "lemma": lemma,
            "pos": "VERB",
            "status": 1,
            "surface": extra.pop("surface", lemma),
            **extra,
        },
    )


def finish(client, lesson, page):
    client.post(f"/api/lessons/{lesson}/finish", json={"page": page})


def states(client, lesson, page=0):
    r = client.get(f"/api/lessons/{lesson}?page={page}").json()
    return {t["surface"]: t["state"] for t in r["tokens"]}


def test_each_new_page_containing_the_word_raises_it_by_one(client, lesson):
    learn(client)
    for page, expected in enumerate((2, 3, 4), start=0):
        finish(client, lesson, page)
        assert status_of(client) == expected


def test_finishing_the_same_page_again_does_not_count_again(client, lesson):
    """The bug this file was rewritten for. Pressing Next page, going back and
    pressing it again is one encounter, not two."""
    learn(client)
    finish(client, lesson, 0)
    assert status_of(client) == 2
    for _ in range(5):
        finish(client, lesson, 0)
    assert status_of(client) == 2


def test_the_page_you_flagged_a_word_on_does_not_also_count(client, lesson):
    """Meeting it is why you flagged it. Counting that page again would make one
    encounter into two, which is what made levels rise too fast."""
    learn(client, lesson_id=lesson, page=0)
    finish(client, lesson, 0)
    assert status_of(client) == 1  # still just flagged

    finish(client, lesson, 1)  # a page you had not met it on
    assert status_of(client) == 2


def test_a_word_repeated_within_one_page_counts_once(client, monkeypatch):
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 400)  # the whole text on one page
    text = "Le quai. Le quai encore. Toujours le quai."
    lid = client.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]
    learn(client)
    finish(client, lid, 0)
    assert status_of(client) == 2


def test_it_stops_at_review_and_never_promotes_itself_to_known(client, lesson):
    """Only the reader gets to say a word is known."""
    learn(client)
    for page in range(5):
        finish(client, lesson, page)
    assert status_of(client) == 4


def test_review_is_its_own_render_state_so_the_reader_can_ask(client, lesson):
    learn(client)
    assert states(client, lesson)["quai"] == "learning"
    for page in range(3):
        finish(client, lesson, page)
    assert states(client, lesson)["quai"] == "review"


def test_only_words_on_the_page_rise(client, lesson):
    learn(client, "quai")
    learn(client, "marcher")
    finish(client, lesson, 1)  # marcher appears only on page 0
    assert status_of(client, "quai") == 2
    assert status_of(client, "marcher") == 1


def test_new_and_known_words_are_not_touched_by_the_bump(client, lesson):
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5})
    client.put("/api/terms", json={"lang": "fr", "lemma": "mouette", "pos": "VERB", "status": -1})
    finish(client, lesson, 0)
    finish(client, lesson, 1)
    assert status_of(client, "quai") == 5
    assert status_of(client, "mouette") == -1


def test_seen_counts_occurrences_even_though_the_level_counts_pages(client, lesson):
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5, "surface": "quai"},
    )
    for page in range(3):
        finish(client, lesson, page)
    entry = next(
        e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == "quai"
    )
    assert entry["met"] > 1
