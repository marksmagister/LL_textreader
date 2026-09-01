"""Re-running the pipeline over stored lessons (CLAUDE.md rule 6).

A model upgrade or a rule change makes stored token streams stale. pipeline_id
records which pipeline produced each one; this is the tool that acts on it.
"""

from ll_textreader.api import lessons
from ll_textreader.db import USER_ID, connect
from ll_textreader.importers.plain_text import reprocess, stale
from ll_textreader.nlp import languages

TEXT = "Il marchait le long du quai. Nous marchons. Une mouette cria."


def make(client, text=TEXT):
    return client.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]


def bump_pipeline(monkeypatch, version="stub@2"):
    """Stand in for a model upgrade."""
    monkeypatch.setattr(languages._cache["fr"], "pipeline_id", version, raising=False)


def test_nothing_is_stale_when_the_pipeline_has_not_moved(client):
    make(client)
    with connect() as conn:
        assert stale(conn) == []


def test_a_pipeline_change_marks_lessons_stale_and_reprocesses_them(client, monkeypatch):
    lesson = make(client)
    bump_pipeline(monkeypatch)
    with connect() as conn:
        assert stale(conn) == [lesson]
        assert reprocess(conn, lesson) is True
        assert stale(conn) == []
        assert reprocess(conn, lesson) is False  # already current


def test_reprocessing_keeps_your_lexicon(client, monkeypatch):
    """The lexicon is keyed on lemma, not lesson, so it must survive untouched."""
    lesson = make(client)
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5, "surface": "marchait"},
    )
    before = client.get("/api/vocab?lang=fr").json()

    bump_pipeline(monkeypatch)
    with connect() as conn:
        reprocess(conn, lesson)

    assert client.get("/api/vocab?lang=fr").json() == before
    states = {
        t["surface"]: t["state"] for t in client.get(f"/api/lessons/{lesson}").json()["tokens"]
    }
    assert states["marchait"] == "known" and states["marchons"] == "novel-form"


def test_reprocessing_keeps_your_place(client, monkeypatch):
    """Token numbering can move; where you had got to must not."""
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 6)
    lesson = make(client)
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    page_before = client.get(f"/api/lessons/{lesson}").json()["page"]
    assert page_before > 0

    bump_pipeline(monkeypatch)
    with connect() as conn:
        reprocess(conn, lesson)
        moved = conn.execute(
            "SELECT last_token FROM reading_progress WHERE lesson_id = ? AND user_id = ?",
            (lesson, USER_ID),
        ).fetchone()["last_token"]

    assert moved > 0
    assert client.get(f"/api/lessons/{lesson}").json()["page"] == page_before


def test_the_body_is_never_touched(client, monkeypatch):
    lesson = make(client)
    body = client.get(f"/api/lessons/{lesson}").json()["body"]
    bump_pipeline(monkeypatch)
    with connect() as conn:
        reprocess(conn, lesson)
    assert client.get(f"/api/lessons/{lesson}").json()["body"] == body
