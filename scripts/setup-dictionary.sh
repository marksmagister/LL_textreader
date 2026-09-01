#!/usr/bin/env bash
# Download a kaikki.org Wiktionary extract and load it into the `hint` table.
#
# CC BY-SA — deliberately NOT vendored, so the repo's licence story stays simple.
# See NOTICE. The raw extract is large (French is ~570MB); it is kept in data/
# so a re-run doesn't re-download, and can be deleted once loaded.
set -euo pipefail

lang="${1:?usage: setup-dictionary.sh <lang-code>}"
dest="data/dictionaries"
raw="$dest/$lang-raw.jsonl"

case "$lang" in
  fr) name="French" ;;
  ru) name="Russian" ;;
  nl) name="Dutch" ;;
  *)  echo "unknown language: $lang" >&2; exit 1 ;;
esac

mkdir -p "$dest"
echo "Downloading the $name extract (resumable — re-run if your connection drops)…"
curl -L -C - --retry 10 --retry-delay 3 --retry-all-errors --progress-bar \
  -o "$raw" "https://kaikki.org/dictionary/$name/kaikki.org-dictionary-$name.jsonl"

echo "Loading into the hint table…"
uv run python -m ll_textreader.dictionary "$lang" "$raw"
