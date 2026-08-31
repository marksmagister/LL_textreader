import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / "ll_textreader" / "schema.sql"


def test_schema_applies_and_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA.read_text())
    conn.executescript(SCHEMA.read_text())  # re-running must not fail
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"lemma_status", "form_seen", "lemma_override", "token", "lesson"} <= tables


def test_lemma_status_is_keyed_on_lemma_and_pos():
    """Homographs must be able to hold different statuses."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA.read_text())
    conn.execute("INSERT INTO user (id, name) VALUES (1, 'test')")
    conn.executemany(
        "INSERT INTO lemma_status (user_id, lang, lemma, pos, status) VALUES (?,?,?,?,?)",
        [(1, "nl", "lees", "NOUN", 5), (1, "nl", "lezen", "VERB", 1)],
    )
    rows = conn.execute("SELECT lemma, status FROM lemma_status ORDER BY lemma").fetchall()
    assert rows == [("lees", 5), ("lezen", 1)]
