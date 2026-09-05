# LL_textreader — agent instructions

A reading app for language learners. You read real text; every word is coloured by
whether *you* know it. Clicking an unknown word gives you a definition and records it.
As you read more, the page decolourises. That is the whole product.

Solo project — one maintainer, no team. Target languages, in order: **French, Russian,
Arabic (MSA + Levantine), Dutch**.

**Pilot scope: French, Russian and Italian. Nothing else** — explicitly not Dutch
(maintainer, 4 September 2026). All three read today. Arabic is not an afterthought —
it is the hardest case, and the data model below exists because of it — but the pilot does
not have to handle its edge cases. Build so Arabic *can* land later without a rewrite; do
not spend pilot time making it work. Dutch comes last, if at all.

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

- lemma new -> **solid blue**
- lemma known, form you have not met -> **a dashed blue outline**
- lemma learning, form met -> **yellow**
- lemma learning, form you have not met -> **a dashed yellow outline**
- lemma met on four pages -> **a blue rule under the word** — time you decided
- lemma known, form met -> **plain**

**Two colours and two treatments, and between them they say everything.** The
*colour* says whose the word is: blue the app is asking, yellow it is actively
yours. The *dash* says the form is one you have not met. They are independent, so
the dash appears over either colour and always means the same thing — which is
what `decisions/0023` changed, after a dashed blue outline on a word you were
mid-way through learning read as "you don't know this" when the opposite was true.
The weights differ by *shape*, not just shade — two blue fills of different
darkness do not separate at reading speed.

The novel-form state is the point of the whole design. It is the difference between
"you don't know this word" and "you know this word, this is a shape of it you haven't
met", which is the only useful distinction in Russian or Arabic. It applies whether the
lemma is known or still being learned -- marking `perçu` must not turn `perçoit` plain
yellow, because you have never met that shape. Levels are counted
from exposure, never self-rated — see `docs/decisions/0008-learning-levels.md`.

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
8. **"Mark rest of page known" is a required feature, not a nicety.** It clears the
   never-judged words *and* answers the ones the app has been asking about (status 4),
   but never touches a word you are actively learning (1-3). It is the pressure
   valve that stops the reader being unusably tedious. Design for it early.

## Layout

```
backend/ll_textreader/
  main.py        FastAPI app; also serves /privacy and /terms
  db.py          sqlite connection, migrations
  config.py      env-backed settings
  schema.sql     the source of truth for the schema
  models.py      pydantic types shared with the API, and state_for()
  auth.py        sessions, the current_user dependency, the account cap
  google.py      the OAuth exchange — the only thing that talks to Google
  limits.py      what one account may cost: rates per hour, absolute caps
  dictionary.py  load a kaikki extract; look a lemma up
  translate.py   sentence translation (optional extra)
  export.py      the lexicon as Anki TSV / CSV / JSON
  counts.py      the library's cached per-lesson counts; recompute, never adjust
  starters.py    the texts a language starts with: given at sign-up, and a button
  starters/      <lang>/<collection>/NN-*.txt — first line is the title
  legal/         privacy.html, terms.html — served without signing in
  nlp/           tokenise + lemmatise -> token stream
    languages/   one adapter per language; each carries its own rules
  api/           routes: lessons, terms, vocab, dictionary, reports,
                 auth (sign in/out), account (export, delete) — docs/api.md
  importers/     plain_text.py, from_url.py -> lesson
backend/tests/
frontend/        vite + react + typescript
  src/i18n.ts    the interface in English or German; English is the type
  src/lang.ts    which language you are reading
  src/morph.ts   UD features -> grammar a learner can read
scripts/         setup: download models & dictionaries (never vendored)
docs/            data-model.md, decisions/ (one file per real decision)
data/            gitignored: the sqlite db, downloaded models, imported texts
```

## Conventions

- **Python 3.12** (not 3.13/3.14 — spaCy and Stanza lag). `uv` for envs and deps.
- French, Russian and Italian read; `fr` is the default. A language is added by
  dropping `<code>.py` into `nlp/languages/` exposing `adapter()` — an object with
  `lang`, `pipeline_id` and `analyse(text) -> list[AnalysedToken]` — and adding the
  code to `LL_TEXTREADER_LANGUAGES`. No other file should learn it exists; the menu
  is built from `/api/health`, and its display name is one entry in `i18n.ts`.
- **Measure a new language before trusting it.** Sixteen forms with the features
  they actually are, run before any display code, and kept as a floor in the tests.
  Every language so far has been broken in a way nobody predicted — see
  `docs/decisions/0021`. An adapter may only correct what is certain from the form
  or from a closed class; anything else is a guess, and rule 7 applies.
- The interface is English or German. Strings live in `i18n.ts`, where English is
  the type, so a missing German string fails the build rather than the reader.
- **SQLite, single file, no ORM** unless it starts hurting. Raw SQL in `schema.sql`;
  it stays readable and it is the thing you'll reason about most.
- Backend formatting/lint: `ruff`. Types: `pyright` where it's cheap.
- Frontend: React + TypeScript via Vite. No component library until there's a reason.
- **Ship no third-party data in the repo.** Wiktionary/Kaikki data is CC-BY-SA and NLP
  models carry their own licences — `scripts/` downloads them into `data/` at setup time.
  This keeps the repo's licence story simple. See `NOTICE`.
- **One instance, many readers, and every reader is alone in it.** Sign in with Google
  (`decisions/0022`). The Google project stays in *Testing*, so the people who can sign
  in are the ones on its test-user list — that list is the invite system, and it is why
  there is no invite table here. What has *not* changed is the isolation:
  `user_id` is part of the key on everything a reader owns, and there is no ambient
  current user — every query that touches reader data carries the id, passed in from
  `current_user`. Do not add a `USER_ID` default back; a call site that forgets must
  fail rather than serve somebody else's vocabulary. `test_auth.py` enumerates the
  routes from the app's own schema, so a new route without a user fails on the day it
  is written.
- **No text this project does not own.** Imports are private to the account that made
  them: not shared between readers, not published, not a library. The starter lessons
  in `starters/` are the one thing every reader gets, and they are original prose
  written for the purpose — an excerpt there would break both this rule and `NOTICE`.
  The line is ownership of the text, not whether two people can see the same file.
- Don't name it, style it, or word it after LingQ. Trademark is a separate risk from
  copyright and it's the one that generates letters.

## Starting a session

Run `./scripts/check.sh` first. Two seconds, changes nothing, and every line in it has
gone wrong at least once — most often `uv sync` silently pruning the spaCy model.

Then read `docs/status.md`. It says where things stand and what is next; `docs/api.md`
lists every endpoint; `docs/decisions/` holds the reasoning behind anything that looks
arbitrary. If something in the code seems odd, the explanation is usually in a decision
file rather than a comment.

## Keeping the record straight

Everything about this project lives in this repo, so a thing not written down is a thing
lost when the session ends. This has already happened once: an entire keyboard spec and
an architecture document existed only in a chat log and had to be recovered from another
session's transcript.

- **Write down what the maintainer says, in the same turn they say it.** Feature ideas,
  preferences, decisions — even in passing, even prefixed "long term" or "low priority".
  `docs/status.md` for state and backlog, `docs/decisions/` for anything with a reason
  behind it. Capture the *why*: the feature is easy to reconstruct later, the reasoning
  is not. Do not wait to be asked and do not batch it to the end.
- **Fix the docs in the same commit as the code.** Five things have gone stale here
  already — a file map missing three modules, two documents describing three render
  states when there were five, a keyboard spec listing keys that had been retired, and
  an endpoint list that did not exist. Each would have had a new session confidently
  building the wrong thing.
- **A decision file per real decision, numbered, never reused.** Two files were both
  0010 at one point. Check `ls docs/decisions/` before picking a number.
- **Correct the record when you were wrong.** Measurements especially: one capacity
  figure in this repo was out by 7× because the benchmark query differed from the real
  one. The correction lives in the document beside the original, not instead of it.

## Working style

- Commit straight to `main`, no branches, no PRs — one person, branching is friction.
  Commit whenever something works, so a bad session can be undone. The one exception so
  far was accounts, on a branch because it touched forty-one call sites at once and the
  failure mode was one reader seeing another's words. Use a branch when a change is
  that shape; otherwise don't.
- Deployment (eventually, a Hetzner box) is `git pull`. Keep it that way.
- Keep prose short. The maintainer reads everything you write; length is a cost they pay.
