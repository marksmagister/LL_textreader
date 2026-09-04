#!/usr/bin/env bash
# Download NLP models into data/models/. Nothing here is vendored into the repo —
# the models carry their own licences (see NOTICE).
#
# _md, not _lg: the extra 500MB in _lg is static word vectors, which the pipeline
# does not use. Lemmas and POS tags are the same.
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/_config.sh

# No arguments: every language the app is configured to offer.
force=""
args=""
for arg in "$@"; do
  case "$arg" in
    --force) force=1 ;;
    *)       args="$args $arg" ;;
  esac
done
langs="${args:-$(configured_langs)}"

# Re-run this after any `uv sync`: the model is installed as a wheel that is not
# in the lockfile, so syncing prunes it — after which the check below finds it
# missing and fetches it again, which is the whole point of the check being an
# import rather than a marker file.

for lang in $langs; do
  if [ -z "$force" ] && uv run python -c "import ${lang}_core_news_md" 2>/dev/null; then
    echo "$lang: model already installed — skipping (--force to reinstall)"
    continue
  fi
  case "$lang" in
    fr) uv run python -m spacy download fr_core_news_md ;;
    ru) uv run python -m spacy download ru_core_news_md ;;
    it) uv run python -m spacy download it_core_news_md ;;
    nl) uv run python -m spacy download nl_core_news_md ;;
    ar) echo "Arabic needs a morphological analyser, not just spaCy — deferred past the"
        echo "pilot. See docs/decisions/0002-arabic-pipeline.md."; exit 1 ;;
    *)  echo "unknown language: $lang" >&2; exit 1 ;;
  esac
done
