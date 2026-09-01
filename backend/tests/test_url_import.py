"""Fetching a URL, and refusing to be used as a proxy into the network."""

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
#
# Fetching is its own step. Extraction gets formatting wrong often enough that
# you want to see the text, and fix it, before it becomes a lesson — so a URL
# fills the boxes and Import is a separate press.


def test_fetching_returns_the_text_and_title_without_importing(client, monkeypatch):
    monkeypatch.setattr(
        from_url, "fetch", lambda url: ("Le vieil homme marchait le long du quai.", "Le quai")
    )
    got = client.post("/api/lessons/fetch", json={"url": "https://example.com/a"}).json()
    assert got["title"] == "Le quai"
    assert got["text"].startswith("Le vieil homme")
    assert got["source"] == "https://example.com/a"
    assert client.get("/api/lessons").json() == []  # nothing stored yet


def test_what_you_edit_is_what_gets_imported(client, monkeypatch):
    """The whole point of the split: bad extraction is fixable."""
    monkeypatch.setattr(from_url, "fetch", lambda url: ("Le  chat   dort  BUTTONS MENU", "Chat"))
    got = client.post("/api/lessons/fetch", json={"url": "https://example.com/a"}).json()

    fixed = got["text"].replace(" BUTTONS MENU", "")
    lesson = client.post(
        "/api/lessons",
        json={"text": fixed, "title": got["title"], "source": got["source"], "lang": "fr"},
    ).json()
    assert lesson["title"] == "Chat"
    assert lesson["source"] == "https://example.com/a"
    body = client.get(f"/api/lessons/{lesson['id']}").json()["body"]
    assert "BUTTONS" not in body


def test_a_page_with_no_article_is_a_clear_error(client, monkeypatch):
    def nothing(url):
        raise BadUrl("no article text found on that page")

    monkeypatch.setattr(from_url, "fetch", nothing)
    r = client.post("/api/lessons/fetch", json={"url": "https://example.com/a"})
    assert r.status_code == 400 and "no article text" in r.json()["detail"]
    assert client.get("/api/lessons").json() == []


def test_a_page_of_only_furniture_is_refused_too(client, monkeypatch):
    """trafilatura can succeed and still return nothing worth reading."""
    monkeypatch.setattr(from_url, "fetch", lambda url: ("   \n  ", "Cookie notice"))
    r = client.post("/api/lessons/fetch", json={"url": "https://example.com/a"})
    assert r.status_code == 400
