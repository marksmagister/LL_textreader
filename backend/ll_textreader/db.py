import sqlite3
from pathlib import Path

from .config import settings

SCHEMA = Path(__file__).with_name("schema.sql")


def connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Apply schema.sql. It is written to be idempotent (CREATE ... IF NOT EXISTS)."""
    with connect() as conn:
        conn.executescript(SCHEMA.read_text())
