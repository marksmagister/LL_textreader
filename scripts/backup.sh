#!/usr/bin/env bash
# Back up the lexicon. The lessons are replaceable; lemma_status and form_seen
# are months of reading and cannot be reconstructed.
#
# Uses sqlite3 .backup rather than cp: the database runs in WAL mode, so copying
# the file while the server is writing can capture a torn state. This is safe on
# a live database.
set -euo pipefail

db="${LL_TEXTREADER_DB_PATH:-data/ll_textreader.db}"
dest="${1:-backups}"
mkdir -p "$dest"
out="$dest/ll_textreader-$(date +%Y%m%d-%H%M%S).db"

sqlite3 "$db" ".backup '$out'"
echo "$out  ($(du -h "$out" | cut -f1))"
