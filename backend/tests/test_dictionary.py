"""Loading Wiktionary glosses, and looking one up."""

import json
import sqlite3
from pathlib import Path

import pytest

from ll_textreader.dictionary import load, lookup

SCHEMA = Path(__file__).resolve().parents[1] / "ll_textreader" / "schema.sql"

ENTRIES = [
    {"word": "porte", "pos": "noun", "lang_code": "fr",
     "senses": [{"glosses": ["door"]}, {"glosses": ["gate"]}]},
    {"word": "porte", "pos": "verb", "lang_code": "fr",
     "senses": [{"glosses": ["inflection of porter"], "tags": ["form-of"]}]},
    {"word": "porter", "pos": "verb", "lang_code": "fr",
     "senses": [{"glosses": ["to carry"]}]},
    # an inflected entry: the lemmatiser already handles these
    {"word": "marchait", "pos": "verb", "lang_code": "fr",
     "senses": [{"form_of": [{"word": "marcher"}], "glosses": ["third-person of marcher"]}]},
    # another language in the same file
    {"word": "haus", "pos": "noun", "lang_code": "de", "senses": [{"glosses": ["house"]}]},
    {"word": "faire", "pos": "verb", "lang_code": "fr",
     "senses": [{"glosses": [f"sense {i}"]} for i in range(20)]},
    {"word": "nogloss", "pos": "noun", "lang_code": "fr", "senses": [{"tags": ["rare"]}]},
]


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA.read_text())
    return c


@pytest.fixture
def extract(tmp_path):
    path = tmp_path / "fr.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in ENTRIES), encoding="utf-8")
    return path


def test_glosses_load_with_ud_pos(conn, extract):
    load(conn, extract, "fr")
    assert [h["gloss"] for h in lookup(conn, "fr", "porte", "NOUN")] == ["door", "gate"]
    assert lookup(conn, "fr", "porter", "VERB")[0]["pos"] == "VERB"


def test_inflected_entries_are_skipped(conn, extract):
    """The lemmatiser already maps marchait -> marcher. A "form of" gloss where the
    definition should be is worse than nothing."""
    load(conn, extract, "fr")
    assert lookup(conn, "fr", "marchait", "VERB") == []
    assert all("inflection of" not in h["gloss"] for h in lookup(conn, "fr", "porte", None))


def test_other_languages_in_the_file_are_ignored(conn, extract):
    load(conn, extract, "fr")
    assert lookup(conn, "fr", "haus", "NOUN") == []


def test_senses_are_capped(conn, extract):
    """Wiktionary lists twenty senses for faire; the panel is a reading aid."""
    load(conn, extract, "fr")
    assert len(lookup(conn, "fr", "faire", "VERB")) == 6


def test_senses_without_a_gloss_are_skipped(conn, extract):
    load(conn, extract, "fr")
    assert lookup(conn, "fr", "nogloss", "NOUN") == []


def test_matching_pos_sorts_first_but_does_not_filter(conn, extract):
    """When the tagger and Wiktionary disagree, the other reading beats nothing."""
    load(conn, extract, "fr")
    hits = lookup(conn, "fr", "porte", "VERB")
    assert hits and hits[0]["gloss"] == "door"  # still shown, just not filtered out


def test_reloading_replaces_rather_than_duplicates(conn, extract):
    load(conn, extract, "fr")
    load(conn, extract, "fr")
    assert [h["gloss"] for h in lookup(conn, "fr", "porte", "NOUN")] == ["door", "gate"]


def test_a_truncated_download_does_not_crash_the_load(conn, tmp_path):
    """Interrupted downloads leave half a line. Load what arrived."""
    good = json.dumps(ENTRIES[0])
    path = tmp_path / "cut.jsonl"
    path.write_text(good + "\n" + json.dumps(ENTRIES[2])[:40], encoding="utf-8")
    assert load(conn, path, "fr") == 2
