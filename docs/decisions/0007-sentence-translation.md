# 0007 — Sentence translation, and why not an LLM

**Request.** An optional English translation under the text, aligned so it starts at
the beginning of a sentence, toggleable — because only sometimes does a learner want
the sentence handed to them.

## Use a translation model, not an LLM

A general LLM is the wrong tool for this. A dedicated NMT model is smaller, faster,
deterministic, and better at exactly this one job:

| | opus-mt-fr-en (Helsinki-NLP) | small local LLM | an API |
|---|---|---|---|
| size | ~300MB | 2–8GB | none |
| speed on CPU | fast | slow | network |
| deterministic | yes | no | no |
| offline | yes | yes | no |
| key/quota | none | none | yes |

It also matches the stance already taken for dictionaries: downloaded by `scripts/`,
never vendored, no vendor and no API key. An API (DeepL, Claude) would translate better,
but it breaks the tailnet-only design in 0005 and puts what you're reading on someone
else's server.

## Translate at import, not at render

Same rule as lemmatisation (CLAUDE.md rule 1). Tokens already carry `sent_id`, so:

```sql
CREATE TABLE sentence_gloss (
    lesson_id   INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    sent_id     INTEGER NOT NULL,
    target_lang TEXT    NOT NULL,
    text        TEXT    NOT NULL,
    pipeline_id TEXT    NOT NULL,
    PRIMARY KEY (lesson_id, sent_id, target_lang)
);
```

Reading stays a join. The toggle becomes purely a display concern, and alignment is
free because the unit is the sentence the tokeniser already found.

Make it an optional extra (`[translate]`), so a setup that doesn't want a 300MB model
doesn't get one.

## One caution

Translation on by default would quietly undermine the product: you stop reading the
French and start reading the English. Default off, per-sentence reveal rather than a
whole-page wall of English, and never for a sentence whose words you already know.
