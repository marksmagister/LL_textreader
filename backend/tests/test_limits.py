"""What one account is allowed to cost.

These exist because open signup means the people using this are not people the
maintainer chose. None of the numbers matter much; what matters is that every
expensive action has *some* ceiling and that the ceiling is counted per account
rather than globally — one noisy reader must not be able to lock everyone else out.
"""

import pytest

from ll_textreader import limits
from ll_textreader.db import connect

from .conftest import user_id


def test_importing_is_capped_by_rate(client, monkeypatch):
    monkeypatch.setitem(limits.PER_HOUR, "import", 2)
    for _ in range(2):
        assert (
            client.post("/api/lessons", json={"text": "Il marchait.", "lang": "fr"}).status_code
            == 201
        )
    refused = client.post("/api/lessons", json={"text": "Il marchait.", "lang": "fr"})
    assert refused.status_code == 429
    assert "import" in refused.json()["detail"]


def test_one_account_hitting_a_limit_does_not_stop_another(client, other, monkeypatch):
    """The ceiling is per account. A shared counter would let one bot take the
    whole box down for everybody, which is worse than what it prevents."""
    monkeypatch.setitem(limits.PER_HOUR, "import", 1)
    assert (
        client.post("/api/lessons", json={"text": "Il marchait.", "lang": "fr"}).status_code == 201
    )
    assert (
        client.post("/api/lessons", json={"text": "Il marchait.", "lang": "fr"}).status_code == 429
    )
    assert (
        other.post("/api/lessons", json={"text": "Il marchait.", "lang": "fr"}).status_code == 201
    )


def test_the_lesson_cap_refuses_the_next_one(client, monkeypatch):
    monkeypatch.setattr(limits, "MAX_LESSONS", 1)
    assert (
        client.post("/api/lessons", json={"text": "Il marchait.", "lang": "fr"}).status_code == 201
    )
    refused = client.post("/api/lessons", json={"text": "Il marchait.", "lang": "fr"})
    assert refused.status_code == 409
    assert "limit" in refused.json()["detail"]


def test_an_enormous_text_is_refused_before_the_tagger_sees_it(client, monkeypatch):
    monkeypatch.setattr(limits, "MAX_TEXT_CHARS", 20)
    refused = client.post("/api/lessons", json={"text": "Il marchait. " * 20, "lang": "fr"})
    assert refused.status_code == 413


def test_url_fetch_is_capped(client, monkeypatch):
    """The tightest of the three: it makes the *server* fetch an address a
    stranger typed, which costs our address's reputation as well as our time."""
    monkeypatch.setitem(limits.PER_HOUR, "fetch", 0)
    assert client.post("/api/lessons/fetch", json={"url": "https://example.com"}).status_code == 429


def test_reports_are_capped(client, monkeypatch):
    monkeypatch.setitem(limits.PER_HOUR, "report", 1)
    assert client.post("/api/reports", json={"text": "the colours are wrong"}).status_code == 201
    assert client.post("/api/reports", json={"text": "still wrong"}).status_code == 429


def test_rating_words_is_capped_far_above_real_reading(client, monkeypatch):
    """The core loop writes one of these per word judged, so a limit set anywhere
    near a real session would break the product rather than protect it."""
    assert limits.PER_HOUR["term"] >= 1000
    monkeypatch.setitem(limits.PER_HOUR, "term", 1)
    body = {"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5}
    assert client.put("/api/terms", json=body).status_code == 200
    assert client.put("/api/terms", json=body).status_code == 429


def test_a_refused_request_still_counts(client, monkeypatch):
    """Otherwise being refused is a free reset, and hammering the endpoint costs
    the attacker nothing while still costing us the handling."""
    monkeypatch.setitem(limits.PER_HOUR, "report", 1)
    client.post("/api/reports", json={"text": "one"})
    client.post("/api/reports", json={"text": "two"})
    client.post("/api/reports", json={"text": "three"})
    with connect() as conn:
        n = conn.execute(
            "SELECT n FROM rate_limit WHERE user_id = ? AND action = 'report'", (user_id(),)
        ).fetchone()[0]
    assert n == 3


def test_sweeping_drops_windows_that_have_passed(client):
    with connect() as conn:
        conn.execute(
            "INSERT INTO rate_limit (user_id, action, window, n)"
            " VALUES (?, 'import', '2020-01-01T00', 9)",
            (user_id(),),
        )
        assert limits.sweep_rates(conn) == 1


@pytest.mark.parametrize("action", sorted(limits.PER_HOUR))
def test_every_limit_is_a_positive_number(action):
    assert limits.PER_HOUR[action] > 0
