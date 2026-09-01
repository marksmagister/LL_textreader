import sqlite3
from pathlib import Path

from .config import settings

SCHEMA = Path(__file__).with_name("schema.sql")

# Single-instance, single-user (CLAUDE.md). user_id exists in the schema so that
# assumption is cheap to drop; until then everything is this row.
USER_ID = 1


def connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# schema.sql stays the source of truth, but CREATE TABLE IF NOT EXISTS will not
# add a column to a database that already exists. Columns added after a database
# was first created go here too. Adding one is idempotent, so there is no version
# number to keep in step.
ADDED_COLUMNS = [
    ("token", "morph", "TEXT NOT NULL DEFAULT ''"),
    ("lesson", "collection_id", "INTEGER REFERENCES collection(id) ON DELETE SET NULL"),
    ("lesson", "position", "INTEGER NOT NULL DEFAULT 0"),
    # Cached, because computing them meant joining every token of every lesson
    # against the lexicon on every visit to the library — 325,000 index lookups
    # at 500 lessons. See counts.py; they are recomputed, never adjusted.
    ("lesson", "n_new", "INTEGER NOT NULL DEFAULT 0"),
    ("lesson", "n_learning", "INTEGER NOT NULL DEFAULT 0"),
    ("lesson", "n_known", "INTEGER NOT NULL DEFAULT 0"),
    # Fixed at import: how long the lesson is. Kept here for the same reason —
    # otherwise the library still has to touch every token to say "650 words".
    ("lesson", "n_tokens", "INTEGER NOT NULL DEFAULT 0"),
    ("lesson", "n_words", "INTEGER NOT NULL DEFAULT 0"),
]


def init_db() -> None:
    """Apply schema.sql. It is written to be idempotent (CREATE ... IF NOT EXISTS)."""
    with connect() as conn:
        conn.executescript(SCHEMA.read_text())
        for table, column, decl in ADDED_COLUMNS:
            existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        conn.execute("INSERT OR IGNORE INTO user (id, name) VALUES (?, 'me')", (USER_ID,))
