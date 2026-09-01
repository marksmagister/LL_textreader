#!/usr/bin/env bash
# Optional. Fetch the French->English translation model (~300MB) so the reader
# can show a sentence in English. Not vendored; see NOTICE. Marian/OPUS-MT is a
# dedicated translation model, not an LLM — see docs/decisions/0007.
set -euo pipefail

uv run python - <<'PY'
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
name = "Helsinki-NLP/opus-mt-fr-en"
print(f"Fetching {name}…")
AutoTokenizer.from_pretrained(name)
AutoModelForSeq2SeqLM.from_pretrained(name)
print("ready")
PY
