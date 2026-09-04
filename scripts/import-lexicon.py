"""Move one reader's whole library and lexicon from another database into this one.

    uv run python scripts/import-lexicon.py <other.db> --into-user 1 [--replace] [--dry-run]

Written for the migration this project actually needed: the maintainer read with
a laptop copy for weeks before the box existed, and that reading had to end up on
the box under their account rather than being retyped or lost.

**It moves rows, not identity.** The target user row is not touched — not its
name, not its `google_sub`. Linking a Google identity to a row is a separate,
deliberate `UPDATE`, for the reason `decisions/0022` gives: adoption was cut
because a feature that binds an identity to an existing lexicon can hand one
person's whole reading history to whoever opens a link. Keep the two apart.

`--replace` deletes what the target user already has first. Without it the copy
is refused when the target is non-empty, because merging two libraries means
deciding what to do about two lessons with the same title and two statuses for
the same lemma, and quietly picking one is the wrong answer.

What is not copied, and why:
  hint        the dictionary, not user data — the destination usually has more
  root_index  derived from hint; rebuilt, never carried
  session     signing in is not a thing you migrate
  rate_limit  a rolling window; carrying it over would import someone's cooldown
  bulk_undo   the offer to take back the last bulk change, valid for a minute
"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from ll_textreader.counts import refresh_all  # noqa: E402
from ll_textreader.db import connect  # noqa: E402

# Owned directly by a reader.
BY_USER = [
    "collection",
    "lesson",
    "lemma_status",
    "form_seen",
    "lemma_override",
    "exposure",
    "reading_progress",
    "bug_report",
]
# Owned by a lesson, and so by whoever owns the lesson.
BY_LESSON = ["token", "sentence_gloss"]


def columns(conn: sqlite3.Connection, table: str, schema: str = "main") -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA {schema}.table_info({table})")]


def common(conn: sqlite3.Connection, table: str) -> list[str]:
    """Columns both databases have. The source may predate a migration."""
    here, there = columns(conn, table), columns(conn, table, "src")
    return [c for c in here if c in there]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="the other .db file")
    ap.add_argument("--from-user", type=int, default=1)
    ap.add_argument("--into-user", type=int, default=1)
    ap.add_argument("--replace", action="store_true", help="delete the target's rows first")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.source).resolve()
    if not src.is_file():
        sys.exit(f"no such database: {src}")

    with connect() as conn:
        if not conn.execute("SELECT 1 FROM user WHERE id = ?", (args.into_user,)).fetchone():
            sys.exit(f"no user {args.into_user} here — create the row first")
        conn.execute("ATTACH DATABASE ? AS src", (str(src),))

        have = conn.execute(
            "SELECT COUNT(*) FROM lesson WHERE user_id = ?", (args.into_user,)
        ).fetchone()[0]
        if have and not args.replace:
            sys.exit(f"user {args.into_user} already has {have} lessons — pass --replace")

        coming = conn.execute(
            "SELECT COUNT(*) FROM src.lesson WHERE user_id = ?", (args.from_user,)
        ).fetchone()[0]
        words = conn.execute(
            "SELECT COUNT(*) FROM src.lemma_status WHERE user_id = ?", (args.from_user,)
        ).fetchone()[0]
        print(f"{src.name}: user {args.from_user} has {coming} lessons, {words} words")
        if args.dry_run:
            print("dry run — nothing written")
            return

        if have:
            # Children first: token and sentence_gloss hang off lesson.
            for table in BY_LESSON:
                conn.execute(
                    f"DELETE FROM {table} WHERE lesson_id IN"
                    " (SELECT id FROM lesson WHERE user_id = ?)",
                    (args.into_user,),
                )
            for table in reversed(BY_USER):
                conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (args.into_user,))
            print(f"replaced: {have} lessons removed from user {args.into_user}")

        for table in BY_USER:
            cols = common(conn, table)
            names = ", ".join(cols)
            # user_id is rewritten to the destination's id; everything else rides.
            picked = ", ".join(
                f"{args.into_user} AS user_id" if c == "user_id" else c for c in cols
            )
            n = conn.execute(
                f"INSERT INTO {table} ({names}) SELECT {picked} FROM src.{table}"
                " WHERE user_id = ?",
                (args.from_user,),
            ).rowcount
            print(f"  {table}: {n}")

        for table in BY_LESSON:
            cols = common(conn, table)
            names = ", ".join(cols)
            n = conn.execute(
                f"INSERT INTO {table} ({names}) SELECT {names} FROM src.{table}"
                " WHERE lesson_id IN (SELECT id FROM src.lesson WHERE user_id = ?)",
                (args.from_user,),
            ).rowcount
            print(f"  {table}: {n}")

        # The cached per-lesson counts came across as they were; recompute them
        # rather than trust them, because a drifted count is worse than a slow one.
        refresh_all(conn, args.into_user)
        conn.commit()
        conn.execute("DETACH DATABASE src")
        print(f"done — user {args.into_user} now has {coming} lessons and {words} words")


if __name__ == "__main__":
    main()
