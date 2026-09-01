"""The door.

Empty password means no door, which is right on localhost and wrong behind a
tunnel — scripts/serve.sh is what enforces the difference.
"""

from base64 import b64encode

import pytest
from fastapi.testclient import TestClient

from ll_textreader.config import settings
from ll_textreader.main import app


def header(user: str, password: str) -> dict[str, str]:
    return {"Authorization": "Basic " + b64encode(f"{user}:{password}".encode()).decode()}


@pytest.fixture
def guarded(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "db_path", tmp_path / "t.db")
    monkeypatch.setattr(settings, "password", "hunter2")
    with TestClient(app) as c:
        yield c


def test_no_password_set_means_no_door(client):
    assert client.get("/api/health").status_code == 200


def test_a_password_locks_everything(guarded):
    for path in ("/api/health", "/api/lessons", "/api/vocab?lang=fr"):
        assert guarded.get(path).status_code == 401


def test_the_challenge_makes_a_browser_ask(guarded):
    """Without this header the browser shows a blank 401 instead of a prompt."""
    assert "Basic" in guarded.get("/api/health").headers.get("WWW-Authenticate", "")


def test_the_right_password_gets_in(guarded):
    assert guarded.get("/api/health", headers=header("read", "hunter2")).status_code == 200


def test_wrong_credentials_do_not(guarded):
    assert guarded.get("/api/health", headers=header("read", "hunter3")).status_code == 401
    assert guarded.get("/api/health", headers=header("someone", "hunter2")).status_code == 401
    assert (
        guarded.get("/api/health", headers={"Authorization": "Bearer hunter2"}).status_code == 401
    )
    assert guarded.get("/api/health", headers={"Authorization": "garbage"}).status_code == 401


def test_writes_are_guarded_too_not_just_reads(guarded):
    """A door only on GET would be no door at all."""
    assert guarded.post("/api/lessons", json={"text": "bonjour", "lang": "fr"}).status_code == 401
    assert (
        guarded.put("/api/terms", json={"lang": "fr", "lemma": "x", "status": 5}).status_code == 401
    )
