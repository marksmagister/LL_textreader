#!/usr/bin/env bash
# Download NLP models into data/models/. Nothing here is vendored into the repo —
# the models carry their own licences (see NOTICE).
set -euo pipefail

langs="${*:-fr}"

for lang in $langs; do
  case "$lang" in
    fr) uv run python -m spacy download fr_core_news_lg ;;
    ru) uv run python -m spacy download ru_core_news_lg ;;
    nl) uv run python -m spacy download nl_core_news_lg ;;
    ar) echo "Arabic needs a morphological analyser, not just spaCy — deferred past the"
        echo "pilot. See docs/decisions/0002-arabic-pipeline.md."; exit 1 ;;
    *)  echo "unknown language: $lang" >&2; exit 1 ;;
  esac
done
