import re

import pytest
from fastapi.testclient import TestClient

from ll_textreader import db
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
        out = []
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
                    sent_id=0,
                )
            )
        return out


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")
    monkeypatch.setitem(languages._cache, "fr", StubAdapter())
    db.init_db()
    with TestClient(app_factory()) as c:
        yield c


def app_factory():
    from ll_textreader.main import app

    return app
