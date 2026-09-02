#!/usr/bin/env bash
# Download a kaikki.org Wiktionary extract and load it into the `hint` table.
#
# CC BY-SA — deliberately NOT vendored, so the repo's licence story stays simple.
# See NOTICE.
#
# The extract is big (French ~570MB, Russian ~940MB) and there is no smaller one
# on offer, but almost all of it is etymology, pronunciation and translations we
# don't store.
# So it is downloaded resumably, parsed, and then deleted: what stays on disk is
# the ~20MB of glosses. Pass --keep to hold on to the raw file.
set -euo pipefail

lang="${1:?usage: setup-dictionary.sh <lang-code> [--keep]}"
keep="${2:-}"
dest="data/dictionaries"
raw="$dest/$lang-raw.jsonl"

case "$lang" in
  fr) name="French" ;;
  ru) name="Russian" ;;
  it) name="Italian" ;;
  nl) name="Dutch" ;;
  *)  echo "unknown language: $lang" >&2; exit 1 ;;
esac

mkdir -p "$dest"
echo "Downloading the $name extract (resumable — re-run if your connection drops)…"
curl -L -C - --retry 10 --retry-delay 3 --retry-all-errors --progress-bar \
  -o "$raw" "https://kaikki.org/dictionary/$name/kaikki.org-dictionary-$name.jsonl"

echo "Loading into the hint table…"
uv run python -m ll_textreader.dictionary "$lang" "$raw"

if [ "$keep" != "--keep" ]; then
  rm -f "$raw"
  echo "Removed $raw — the glosses are in the database now."
fi
