"""Importing from a URL, and refusing to be used as a proxy into the network."""

import pytest

from ll_textreader.importers import from_url
from ll_textreader.importers.from_url import BadUrl, check


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/secrets",
        "http://127.0.0.1:8000/api/lessons",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://192.168.1.1/admin",
        "http://10.0.0.5/",
        "https://[::1]/",
    ],
)
def test_private_and_loopback_addresses_are_refused(url):
    """The server does the fetching, so a URL is a request made from inside
    wherever this is hosted. Anyone who can reach the app could otherwise read
    the private network back as a lesson."""
    with pytest.raises(BadUrl):
        check(url)


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "ftp://example.com/x", "gopher://x/", "notaurl"]
)
def test_only_http_and_https(url):
    with pytest.raises(BadUrl):
        check(url)


def test_a_public_address_is_allowed():
    assert check("https://example.com/article") == "https://example.com/article"


def test_a_name_that_does_not_resolve_is_refused():
    with pytest.raises(BadUrl):
        check("https://this-host-does-not-exist.invalid/")


# ---------------------------------------------------------------- the endpoint


def test_importing_a_url_uses_the_page_title_and_records_the_source(client, monkeypatch):
    monkeypatch.setattr(
        from_url, "fetch", lambda url: ("Le vieil homme marchait le long du quai.", "Le quai")
    )
    lesson = client.post("/api/lessons", json={"url": "https://example.com/a", "lang": "fr"}).json()
    assert lesson["title"] == "Le quai"
    assert lesson["source"] == "https://example.com/a"
    assert lesson["n_words"] > 0


def test_your_own_title_wins_over_the_page_title(client, monkeypatch):
    monkeypatch.setattr(from_url, "fetch", lambda url: ("Le chat dort.", "Their Title"))
    lesson = client.post(
        "/api/lessons", json={"url": "https://example.com/a", "title": "Mine", "lang": "fr"}
    ).json()
    assert lesson["title"] == "Mine"


def test_a_page_with_no_article_is_a_clear_error_not_an_empty_lesson(client, monkeypatch):
    def nothing(url):
        raise BadUrl("no article text found on that page")

    monkeypatch.setattr(from_url, "fetch", nothing)
    r = client.post("/api/lessons", json={"url": "https://example.com/a", "lang": "fr"})
    assert r.status_code == 400 and "no article text" in r.json()["detail"]
    assert client.get("/api/lessons").json() == []
