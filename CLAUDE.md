# LL_textreader — agent instructions

A reading app for language learners. You read real text; every word is coloured by
whether *you* know it. Clicking an unknown word gives you a definition and records it.
As you read more, the page decolourises. That is the whole product.

Solo project — one maintainer, no team. Target languages, in order: **French, Russian,
Arabic (MSA + Levantine), Dutch**.

**Pilot scope: French, and maybe Russian. Nothing else.** Arabic is not an afterthought —
it is the hardest case, and the data model below exists because of it — but the pilot does
not have to handle its edge cases. Build so Arabic *can* land later without a rewrite; do
not spend pilot time making it work. Dutch comes last.

**Current state and next steps: `docs/status.md`.** This file describes *design and
conventions* (changes on a decision); `docs/status.md` holds *state* (changes on an event).
Don't duplicate one into the other. Everything about this project lives in this repo.

## Boring on purpose

This is the cornerstone, above every specific rule below.

The characteristic failure of AI-written software is bloat: layers nobody asked for,
abstractions with a single implementation, options no one will ever set, five files
doing one file's work. It reads as thoroughness. It is a tax you pay on every return
visit, and it buries the ideas that actually matter under ceremony.

So build the smallest thing that genuinely works, out of boring parts:

- No abstraction until there is a second caller. One implementation is not a pattern.
- No flag, option or config key until something real needs to differ. Hardcode it and
  move it when that stops being true.
- No dependency that replaces twenty lines you could read.
- Prefer a function to a class, a class to a framework, and raw SQL to any of them.
- Ship vertical slices, not layers. If you can't demonstrate it in the running app,
  it isn't built.
- Delete rather than deprecate. One user, no API contract, no audience to keep happy.

A change that makes the codebase bigger without making it clearer is the wrong change.
Every file here should be one you'd be willing to read on a bad day.

## The core model

The atomic unit is a status per user per word — but keyed on the **lemma**, not the
surface form:

```
lemma_status: (user, lang, lemma, pos) -> 0..5     # 0 new, 1-4 learning, 5 known
form_seen:    (user, lang, lemma, pos, surface) -> count, first_seen
```

The lemma carries the status; the form table records which inflections have actually
been met. Rendering follows from the join of those two against a lesson's token stream:

- lemma unknown -> **blue**
- lemma known, this surface form seen before -> **plain**
- lemma known, novel surface form -> **third, lighter highlight**

That third state is the point of the whole design. It is the difference between "you
don't know this word" and "you know this word, this is a shape of it you haven't met",
which is the only useful distinction in Russian or Arabic.

## Rules that are easy to get wrong

1. **Lemmatisation runs at import, never at render.** A lesson is stored as a token
   stream, not a string. Page open must be a DB join and nothing else.
2. **Token records carry char offsets into the original text.** Never reconstruct
   display text from tokens — overlay spans onto the raw string. Arabic clitic splitting
   produces several tokens from one whitespace-delimited word, so offsets are the only
   thing that survives.
3. **POS is part of the key.** Homographs are separate entries. A user may know
   `porte` (noun, door) without knowing `porter` (verb).
4. **Never key on the Arabic triliteral root.** ك-ت-ب spans write/book/office/writer/
   library — different vocabulary items. Root is a *secondary index* for a "related
   words" panel only. *(Post-pilot, but the schema already reserves room for it — don't
   design it out.)*
5. **The user can always override the lemmatiser.** A "this is wrong" action detaches a
   surface form from its assigned lemma and makes it its own entry, stored as a user-level
   override joined against pipeline output. Without this escape hatch one bad model
   decision is unfixable and the colouring loses trust.
6. **Stamp the pipeline version onto every token stream.** Model upgrades make stored
   streams stale; you need to know which lessons to reprocess.
7. **Low-confidence analysis falls back to surface-form behaviour.** Guessing is worse
   than not lemmatising, because the failures are rare enough to be confusing.
8. **"Mark rest of page known" is a required feature, not a nicety.** It is the pressure
   valve that stops the reader being unusably tedious. Design for it early.

## Layout

```
backend/ll_textreader/
  main.py        FastAPI app
  db.py          sqlite connection, migrations
  config.py      env-backed settings
  schema.sql     the source of truth for the schema
  models.py      pydantic types shared with the API
  nlp/           tokenise + lemmatise -> token stream
    languages/   one adapter per language (nl, fr, ru, ar)
  api/           route modules: lessons, terms, dictionary
  importers/     epub / url / plain text -> lesson
backend/tests/
frontend/        vite + react + typescript
scripts/         setup: download models & dictionaries (never vendored)
docs/            data-model.md, decisions/ (one file per real decision)
data/            gitignored: the sqlite db, downloaded models, imported texts
```

## Conventions

- **Python 3.12** (not 3.13/3.14 — spaCy and Stanza lag). `uv` for envs and deps.
- Default language is `fr`. A language is added by dropping `<code>.py` into
  `nlp/languages/` exposing `adapter()` — an object with `lang`, `pipeline_id` and
  `analyse(text) -> list[AnalysedToken]`. No other file should learn it exists.
- **SQLite, single file, no ORM** unless it starts hurting. Raw SQL in `schema.sql`;
  it stays readable and it is the thing you'll reason about most.
- Backend formatting/lint: `ruff`. Types: `pyright` where it's cheap.
- Frontend: React + TypeScript via Vite. No component library until there's a reason.
- **Ship no third-party data in the repo.** Wiktionary/Kaikki data is CC-BY-SA and NLP
  models carry their own licences — `scripts/` downloads them into `data/` at setup time.
  This keeps the repo's licence story simple. See `NOTICE`.
- **Single-instance, single-user.** Each person runs their own copy with their own
  imports. Do not add a shared lesson library — that is the line between "read-later app"
  and "hosting other people's copyrighted text".
- Don't name it, style it, or word it after LingQ. Trademark is a separate risk from
  copyright and it's the one that generates letters.

## Working style

- Commit straight to `main`, no branches, no PRs — one person, branching is friction.
  Commit whenever something works, so a bad session can be undone.
- Deployment (eventually, a Hetzner box) is `git pull`. Keep it that way.
- Keep prose short. The maintainer reads everything you write; length is a cost they pay.
