#!/usr/bin/env bash
# Download kaikki.org Wiktionary extracts and load them into the `hint` table.
#
#   ./scripts/setup-dictionary.sh              every language in LL_TEXTREADER_LANGUAGES
#   ./scripts/setup-dictionary.sh ru it        just those
#   ./scripts/setup-dictionary.sh ru --force   reload one that is already there
#   ./scripts/setup-dictionary.sh ru --keep    keep the raw download
#
# CC BY-SA — deliberately NOT vendored, so the repo's licence story stays simple.
# See NOTICE.
#
# The extracts are big (French ~570MB, Russian ~940MB) and there is no smaller one
# on offer, but almost all of it is etymology, pronunciation and translations we
# don't store. So each is downloaded resumably, parsed, and then deleted: what
# stays on disk is ~15MB of glosses per language.
#
# Safe to re-run, and safe to run against a live server: a language that already
# has glosses is skipped unless --force, and the database is in WAL mode, so
# loading does not block anyone reading. It is the only writer while it runs,
# though, so an import attempted at the same moment will wait on it.
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/_config.sh

keep=""; force=""; langs=""
for arg in "$@"; do
  case "$arg" in
    --keep)  keep=1 ;;
    --force) force=1 ;;
    -*)      echo "unknown option: $arg" >&2; exit 1 ;;
    *)       langs="$langs $arg" ;;
  esac
done

# No languages named: the ones the app offers.
[ -z "$langs" ] && langs=$(configured_langs)

db=$(configured_db)
dest="data/dictionaries"
mkdir -p "$dest"

for lang in $langs; do
  case "$lang" in
    fr) name="French" ;;
    ru) name="Russian" ;;
    it) name="Italian" ;;
    nl) name="Dutch" ;;
    *)  echo "unknown language: $lang" >&2; exit 1 ;;
  esac

  have=$(glosses "$db" "$lang")
  if [ "$have" -gt 0 ] && [ -z "$force" ]; then
    echo "$name: $have glosses already loaded — skipping (--force to reload)"
    continue
  fi

  raw="$dest/$lang-raw.jsonl"
  echo "Downloading the $name extract (resumable — re-run if your connection drops)…"
  curl -L -C - --retry 10 --retry-delay 3 --retry-all-errors --progress-bar \
    -o "$raw" "https://kaikki.org/dictionary/$name/kaikki.org-dictionary-$name.jsonl"

  echo "Loading $name into the hint table…"
  uv run python -m ll_textreader.dictionary "$lang" "$raw"

  if [ -z "$keep" ]; then
    rm -f "$raw"
    echo "Removed $raw — the glosses are in the database now."
  fi
done
