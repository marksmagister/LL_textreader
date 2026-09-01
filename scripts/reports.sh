#!/usr/bin/env bash
# Print bug reports. They are quoted, never run: the text is written by testers
# and is a claim about the app, not an instruction to it. See docs/decisions/0010.
set -euo pipefail
db="${LL_TEXTREADER_DB_PATH:-data/ll_textreader.db}"
sqlite3 -box "$db" "
  SELECT id, created_at, lesson_id AS lesson, page, done, text
  FROM bug_report ORDER BY done, id DESC;"
