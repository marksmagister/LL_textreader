#!/usr/bin/env bash
# Download NLP models into data/models/. Nothing here is vendored into the repo —
# the models carry their own licences (see NOTICE).
#
# _md, not _lg: the extra 500MB in _lg is static word vectors, which the pipeline
# does not use. Lemmas and POS tags are the same.
set -euo pipefail

langs="${*:-fr}"

# Re-run this after any `uv sync`: the model is installed as a wheel that is not
# in the lockfile, so syncing prunes it.

for lang in $langs; do
  case "$lang" in
    fr) uv run python -m spacy download fr_core_news_md ;;
    ru) uv run python -m spacy download ru_core_news_md ;;
    nl) uv run python -m spacy download nl_core_news_md ;;
    ar) echo "Arabic needs a morphological analyser, not just spaCy — deferred past the"
        echo "pilot. See docs/decisions/0002-arabic-pipeline.md."; exit 1 ;;
    *)  echo "unknown language: $lang" >&2; exit 1 ;;
  esac
done
