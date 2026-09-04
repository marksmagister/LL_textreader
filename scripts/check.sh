#!/usr/bin/env bash
# Is this working copy ready to run? Two seconds, changes nothing.
#
# Every item here has actually gone wrong at least once. `uv sync` silently
# prunes the spaCy model, a stale server serves code from before your edit, and
# a password in .env locks the Vite dev proxy out unless it carries the header.
set -uo pipefail
cd "$(dirname "$0")/.."
. scripts/_config.sh
ok=0; bad=0
say() { if [ "$1" = y ]; then echo "  ✓ $2"; ok=$((ok+1)); else echo "  ✗ $2 — $3"; bad=$((bad+1)); fi; }

[ -d .venv ] && say y "python env" || say n "python env" "uv sync --extra nlp"

# Every language the menu offers needs its model, or importing in it fails with a
# 503 that reads like a bug.
langs=$(configured_langs)
for lang in $langs; do
  uv run python -c "import ${lang}_core_news_md" 2>/dev/null \
    && say y "$lang model" \
    || say n "$lang model" "./scripts/setup-models.sh $lang  (uv sync prunes it)"
done
uv run python -c "import transformers" 2>/dev/null \
  && say y "translation extra" || echo "  · translation not installed (optional: uv sync --extra translate)"
[ -d frontend/node_modules ] && say y "node modules" || say n "node modules" "npm install --prefix frontend"

db=$(configured_db)
if [ -f "$db" ]; then
  for lang in $langs; do
    n=$(glosses "$db" "$lang")
    [ "$n" -gt 0 ] && say y "$lang dictionary ($n glosses)" \
                   || say n "$lang dictionary" "./scripts/setup-dictionary.sh $lang"
  done
  echo "  · $(sqlite3 "$db" 'SELECT COUNT(*) FROM lesson') lessons, $(sqlite3 "$db" 'SELECT COUNT(*) FROM lemma_status') words known"
else
  say n "database" "it is created on first run"
fi

if pgrep -f "uvicorn ll_textreader" >/dev/null; then
  echo "  · backend is running — restart it after editing Python, it does not reload"
else
  echo "  · backend not running: ./scripts/serve.sh"
fi

echo
[ "$bad" -eq 0 ] && echo "Ready." || echo "$bad thing(s) to fix first."
exit 0
