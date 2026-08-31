# Status & roadmap

Current state and what's next. Design lives in `../CLAUDE.md`, the data model in
`data-model.md`, and the reasoning behind individual decisions in `decisions/`. Those
change on a decision; this file changes on an event. Don't copy one into the other.

## Where things stand

Skeleton only — you cannot read a sentence in it yet.

Working and verified:
- `schema.sql` applies and is idempotent
- backend boots, serves `/api/health`, creates the DB on startup
- frontend builds and renders the four token states (hardcoded demo sentence, not wired to anything)
- tests and ruff pass

Not built: importer, lemmatiser, dictionary, reader view, lookup panel.

## Next

1. **French pipeline** — spaCy `fr_core_news_lg` → token stream, computed at import and
   stored. First real test of the data model against actual text.
2. **Plain-text importer**, then EPUB.
3. **Reader view** against real lessons, and the lookup panel.
4. **"Mark rest of page known"** — the pressure valve. Without it the reader is unusable
   for anything above beginner level, so don't leave it to the end.
5. **Dictionary loader** — a kaikki.org French extract into the `hint` table.

## Open questions

- Levantine Arabic: MSA-trained analysers mis-handle بدي / عم بكتب / مش. Dialect-ID step
  routing to a dialect analyser, or accept the accuracy hit and lean on `lemma_override`?
  Not a pilot problem — see `decisions/0002-arabic-pipeline.md`.
- Russian in the pilot or not. French first regardless.
- Where audio and sentence-level timestamps fit, if at all.
