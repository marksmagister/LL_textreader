import re

import pytest
from fastapi.testclient import TestClient

from ll_textreader import auth, db
from ll_textreader.config import settings
from ll_textreader.models import AnalysedToken
from ll_textreader.nlp import languages

# A two-form toy lexicon: enough to exercise "known lemma, novel form".
LEMMAS = {"marchait": "marcher", "marchons": "marcher", "quais": "quai"}


class StubAdapter:
    """Stands in for spaCy so the plumbing can be tested without a 500MB model."""

    lang = "fr"
    pipeline_id = "stub@0"

    def analyse(self, text: str) -> list[AnalysedToken]:
        out, sent = [], 0
        for m in re.finditer(r"\w+|[^\w\s]", text):
            word = m.group()
            lexical = word.isalpha()
            out.append(
                AnalysedToken(
                    idx=len(out),
                    surface=word,
                    norm=word.casefold(),
                    lemma=LEMMAS.get(word.casefold(), word.casefold()) if lexical else None,
                    pos="VERB" if lexical else None,
                    char_start=m.start(),
                    char_end=m.end(),
                    sent_id=sent,
                )
            )
            if word in ".!?":
                sent += 1
        return out


def sign_in(client: TestClient, name: str, sub: str) -> int:
    """Make an account and put its session cookie on the client.

    Straight into the database rather than through Google: the OAuth round trip
    needs a browser and a person pressing Allow, and every test below is about
    what happens *after* somebody is signed in. What the real callback does with
    the identity it gets back is covered separately, against a stubbed exchange.
    """
    with db.connect() as conn:
        user = auth.create_user(conn, sub=sub, name=name, email=f"{name}@example.com", picture=None)
        token = auth.open_session(conn, user.id)
    client.cookies.set(auth.COOKIE, token)
    return user.id


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A database and a stub French pipeline. No user, no session."""
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")
    # Anything a developer puts in .env must not change what is tested. This bit
    # them once: a password set for sharing turned 58 tests into 401s.
    monkeypatch.setattr(settings, "signup", "open")
    monkeypatch.setattr(settings, "max_users", 100)
    monkeypatch.setattr(settings, "cookie_secure", False)
    monkeypatch.setitem(languages._cache, "fr", StubAdapter())
    db.init_db()
    with TestClient(app_factory()) as c:
        yield c


@pytest.fixture
def client(env):
    """Signed in. What almost every test wants, and what `client` has always meant."""
    sign_in(env, "alice", "sub-alice")
    return env


@pytest.fixture
def other(env):
    """A second reader, with their own session, sharing the database with `client`.

    Two clients over one database is the whole point: it is what lets a test ask
    whether one reader can see the other's words.
    """
    second = TestClient(app_factory())
    second.cookies = type(second.cookies)()
    sign_in(second, "bob", "sub-bob")
    return second


def app_factory():
    from ll_textreader.main import app

    return app


def user_id() -> int:
    """The id of the only account in the test database.

    Tests that reach past the API into SQL need a user id, and used to import the
    USER_ID constant. That constant is gone on purpose (0022), and hardcoding 1
    in its place would quietly re-introduce the assumption it was deleted to
    remove — so this asks the database instead.
    """
    with db.connect() as conn:
        return int(conn.execute("SELECT id FROM user ORDER BY id LIMIT 1").fetchone()[0])
