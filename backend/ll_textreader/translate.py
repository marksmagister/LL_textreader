"""Sentence translation.

A dedicated translation model, not an LLM: smaller, faster, deterministic,
offline, and better at this one job. See `docs/decisions/0007-sentence-translation.md`.

Optional. Without `uv sync --extra translate` the reader simply never offers it,
which is the right default anyway — a translation always on hand means you stop
reading the French.
"""

import sqlite3
from functools import cached_property

# OPUS-MT, one dedicated model per pair. Verified to exist on Hugging Face
# 2026-09-04. Each is a ~300MB download, fetched on first use of translation for
# that language and then cached.
MODELS = {
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("ru", "en"): "Helsinki-NLP/opus-mt-ru-en",
    ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
}

# Marian is small; batching is what makes a page fast rather than a sentence at a time.
BATCH = 16


class Unavailable(Exception):
    """No translator for this pair, or the optional dependencies aren't installed."""


class Translator:
    def __init__(self, source: str, target: str) -> None:
        self.source, self.target = source, target
        self.name = MODELS[(source, target)]

    @cached_property
    def _model(self):
        # The model directly, not transformers' `pipeline`: the "translation"
        # task was removed in transformers 5, and generate() is the stable API.
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        except ImportError as exc:
            raise Unavailable("uv sync --extra translate") from exc
        return (
            AutoTokenizer.from_pretrained(self.name),
            AutoModelForSeq2SeqLM.from_pretrained(self.name),
        )

    def translate(self, sentences: list[str]) -> list[str]:
        if not sentences:
            return []
        tokenizer, model = self._model
        out: list[str] = []
        for i in range(0, len(sentences), BATCH):
            batch = tokenizer(
                sentences[i : i + BATCH],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            generated = model.generate(**batch, max_new_tokens=512)
            out += tokenizer.batch_decode(generated, skip_special_tokens=True)
        return out


_cache: dict[tuple[str, str], Translator] = {}


def get_translator(source: str, target: str = "en") -> Translator:
    key = (source, target)
    if key not in MODELS:
        raise Unavailable(f"no model for {source}->{target}")
    if key not in _cache:
        _cache[key] = Translator(source, target)
    return _cache[key]


def sentences_of(conn: sqlite3.Connection, lesson_id: int, lo: int, hi: int) -> dict[int, str]:
    """The text of each sentence in a token range, sliced out of the body.

    Sliced by offset, never rebuilt from tokens — the same rule the reader follows.
    """
    body = conn.execute("SELECT body FROM lesson WHERE id = ?", (lesson_id,)).fetchone()["body"]
    rows = conn.execute(
        "SELECT sent_id, MIN(char_start) AS a, MAX(char_end) AS b FROM token"
        " WHERE lesson_id = ? AND idx BETWEEN ? AND ? GROUP BY sent_id ORDER BY sent_id",
        (lesson_id, lo, hi),
    ).fetchall()
    return {r["sent_id"]: body[r["a"] : r["b"]].strip() for r in rows}


def glosses_for(
    conn: sqlite3.Connection, lesson_id: int, lang: str, lo: int, hi: int, target: str = "en"
) -> dict[int, str]:
    """Translations for a token range, translating and storing whatever is missing.

    Done on demand rather than at import: translation is off by default, and an
    import should not pay for a feature most lessons never use.
    """
    have = {
        r["sent_id"]: r["text"]
        for r in conn.execute(
            "SELECT sent_id, text FROM sentence_gloss WHERE lesson_id = ? AND target_lang = ?",
            (lesson_id, target),
        )
    }
    wanted = sentences_of(conn, lesson_id, lo, hi)
    missing = {k: v for k, v in wanted.items() if k not in have and v}
    if missing:
        translator = get_translator(lang, target)
        done = translator.translate(list(missing.values()))
        conn.executemany(
            "INSERT OR REPLACE INTO sentence_gloss"
            " (lesson_id, sent_id, target_lang, text, model) VALUES (?,?,?,?,?)",
            [
                (lesson_id, sent_id, target, text, translator.name)
                for sent_id, text in zip(missing, done, strict=True)
            ],
        )
        have.update(dict(zip(missing, done, strict=True)))
    return {k: have[k] for k in wanted if k in have}
