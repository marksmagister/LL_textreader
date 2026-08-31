#!/usr/bin/env bash
# Download Wiktionary-derived dictionary data (kaikki.org) into data/dictionaries/.
# CC BY-SA — deliberately NOT vendored, so the repo's licence story stays simple.
set -euo pipefail

lang="${1:?usage: setup-dictionary.sh <lang-code>}"
dest="data/dictionaries"
mkdir -p "$dest"

echo "TODO: fetch the kaikki.org extract for '$lang' into $dest/"
echo "      then load it into the hint table (backend/ll_textreader/api/dictionary.py)."
