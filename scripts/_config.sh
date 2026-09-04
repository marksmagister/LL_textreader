#!/usr/bin/env bash
# What the app is configured to do, for the scripts that have to agree with it.
# Sourced, never run. Run from the repo root, as the other scripts do.
#
# Read out of .env rather than sourcing it: a value with a space in it would make
# `.` fail, and these run on a server where a script that dies quietly is a
# language whose model silently never gets installed.
#
# The `[ -f .env ]` guard is load-bearing. Under `set -euo pipefail` a sed that
# cannot open the file takes the whole script down without printing anything —
# which is exactly what happened on a clone that had not copied .env yet, i.e.
# every fresh checkout following the README in order.

# The languages the menu offers, space separated. The fallback has to match the
# default in config.py, or these scripts check for a different set of languages
# than the app actually offers.
configured_langs() {
  local from_env=""
  [ -f .env ] && from_env=$(sed -n 's/^LL_TEXTREADER_LANGUAGES=//p' .env | tail -1 | tr -d '"'"'"'')
  echo "${LL_TEXTREADER_LANGUAGES:-${from_env:-fr,ru,it}}" | tr ',' ' '
}

# Where the database is.
configured_db() {
  local from_env=""
  [ -f .env ] && from_env=$(sed -n 's/^LL_TEXTREADER_DB_PATH=//p' .env | tail -1 | tr -d '"'"'"'')
  echo "${LL_TEXTREADER_DB_PATH:-${from_env:-data/ll_textreader.db}}"
}

# One number out of the database: db_scalar <db> <sql> [params...]
#
# Two things it must do, both learned the hard way. It **never creates** the
# database — a probe that did left a root-owned empty file the loader could not
# write, which is how the first provisioning run died half way (decision 0018),
# hence the read-only URI. And it uses Python rather than the sqlite3 CLI,
# because the CLI is not installed everywhere and where it is missing its absence
# reads as a real answer of zero rather than "cannot tell".
#
# Zero when anything at all goes wrong, which is the safe direction here: every
# caller treats zero as "not set up yet" and prints the command that sets it up.
db_scalar() {
  local db=$1 sql=$2
  shift 2
  uv run python -c "
import sqlite3, sys
try:
    conn = sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True)
    print(conn.execute(sys.argv[2], sys.argv[3:]).fetchone()[0])
except Exception:
    print(0)
" "$db" "$sql" "$@" 2>/dev/null || echo 0
}

# How many Wiktionary glosses a language has.
glosses() {
  db_scalar "$1" "SELECT COUNT(*) FROM hint WHERE lang = ?" "$2"
}
