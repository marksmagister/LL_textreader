#!/usr/bin/env bash
# Back up the lexicon. The lessons are replaceable and the dictionary is a
# re-download; lemma_status and form_seen are months of reading and cannot be
# reconstructed.
#
# Uses sqlite3 .backup rather than cp: the database runs in WAL mode, so copying
# the file while the server is writing can capture a torn state.
#
#   ./scripts/backup.sh                     write one to backups/
#   LL_TEXTREADER_BACKUP_TO=host:path ...   and send it somewhere else
#
# A backup on the same disk as the database is not a backup. Set BACKUP_TO.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a

db="${LL_TEXTREADER_DB_PATH:-data/ll_textreader.db}"
dest="${1:-backups}"
keep="${LL_TEXTREADER_BACKUP_KEEP:-14}"
mkdir -p "$dest"
out="$dest/ll_textreader-$(date +%Y%m%d-%H%M%S).db"

sqlite3 "$db" ".backup '$out'"

# A file that exists is not yet a backup. Check it opens and holds the tables
# that matter before trusting it enough to delete an older one.
rows=$(sqlite3 "$out" "SELECT COUNT(*) FROM lemma_status" 2>/dev/null || echo FAIL)
if [ "$rows" = FAIL ] || [ "$(sqlite3 "$out" 'PRAGMA integrity_check')" != "ok" ]; then
  echo "backup failed its own integrity check: $out" >&2
  exit 1
fi

# Opening the copy to check it puts it into WAL mode, which leaves -wal and -shm
# beside it. Switching the journal back merges them in and removes them, so the
# backup is the single file it claims to be.
sqlite3 "$out" "PRAGMA journal_mode=DELETE;" >/dev/null
rm -f "$out-wal" "$out-shm"

gzip -f "$out"          # mostly text; roughly a third of the size
out="$out.gz"
echo "$out  ($(du -h "$out" | cut -f1), $rows words)"

# Oldest first, delete everything past the newest $keep.
ls -1t "$dest"/ll_textreader-*.db.gz 2>/dev/null | tail -n +$((keep + 1)) | while read -r old; do
  rm -f "$old" && echo "  pruned $old"
done

if [ -n "${LL_TEXTREADER_BACKUP_TO:-}" ]; then
  rsync -a "$out" "$LL_TEXTREADER_BACKUP_TO/" && echo "  copied to $LL_TEXTREADER_BACKUP_TO"
else
  echo "  NOT copied off this machine — set LL_TEXTREADER_BACKUP_TO" >&2
fi
