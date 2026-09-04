import sqlite3
from pathlib import Path

from .config import settings

SCHEMA = Path(__file__).with_name("schema.sql")

# There is deliberately no USER_ID constant here any more. It used to be 1, read
# at forty-odd call sites, and docs/decisions/0013 was blunt about why removing it
# had to mean *removing* it rather than leaving a default: a call site that forgets
# to pass a user must fail to import, not quietly serve user 1's vocabulary to
# whoever asked. Every query that touches user data takes the id as an argument.
# See auth.py for where it comes from.


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
    # Accounts (0022). Nullable, because the row that already exists in a
    # database predating them has none of these and is adopted rather than
    # replaced. Declared plain rather than UNIQUE because SQLite cannot add a
    # UNIQUE column to an existing table — the index below does that job, and it
    # permits many NULLs, which is exactly right for un-adopted rows.
    ("user", "google_sub", "TEXT"),
    ("user", "email", "TEXT"),
    ("user", "picture", "TEXT"),
    ("user", "lang", "TEXT NOT NULL DEFAULT 'fr'"),
]

# Indexes over columns that ADDED_COLUMNS may have just created, so they cannot
# live in schema.sql — that runs first, against a table which may not have them.
ADDED_INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_google ON user(google_sub)",
]


def init_db() -> None:
    """Apply schema.sql. It is written to be idempotent (CREATE ... IF NOT EXISTS).

    No user is created here. It used to insert user 1 so the single-user app had
    somewhere to put things; now a user exists only once someone has signed in,
    and an install that predates accounts keeps whatever rows it already had.
    """
    with connect() as conn:
        conn.executescript(SCHEMA.read_text())
        for table, column, decl in ADDED_COLUMNS:
            existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        for statement in ADDED_INDEXES:
            conn.execute(statement)
