# Status & roadmap

**New session? Run `./scripts/check.sh`, then read this file.**

Current state and what's next. Design lives in `../CLAUDE.md`, the data model in
`data-model.md`, and the reasoning behind individual decisions in `decisions/`. Those
change on a decision; this file changes on an event. Don't copy one into the other.

## Where things stand

**Readable, keyboard-first, with definitions.** Paste French text, read it coloured by
what you know, Tab between unknown words, and the page decolourises as you go.

Working and verified against real text, in the browser:
- French pipeline: spaCy `fr_core_news_md`, POS-tagged lemmas, run at import
- plain-text import (paste or `.txt`), pages, saved position, "mark page known"
- all five render states, including known-lemma-novel-form
- a legend page explaining them, reachable from the library and the palette
- Wiktionary glosses: 126k senses for French, from a kaikki.org extract
- morphology: "conditional · 1st person singular", with rules that stay quiet
  rather than guess (see below)
- sentence translation, off by default, per page on demand
- a legend page explaining the colours and keys
- lexicon export: Anki TSV, CSV, JSON — all, one bucket, or a ticked selection
- collections, a legend, light/dark, sorting and search in the library
- the library listing is O(lessons), not O(every word you ever imported): 1.8ms,
  and 0.7ms at five hundred lessons (`counts.py`, `decisions/0016`)
- lemma override, in the UI and honoured by the read path
- vocabulary page: every lemma, with the inflections you have actually met
- library shows each text's shape — what share of it you can already read
- keyboard: Tab/Shift-Tab (new words *and* the ones at level 4), 1, k, i,
  Shift-K, j/arrows, Enter, Esc, o, /
- levels counted from exposure, not self-rated (decision 0008)
- undo for "mark page known"
- the sentence you first met a word in, kept and shown
- `--dry-run`-able reprocessing for stale token streams (rule 6)
- 207 tests, ruff and tsc clean

Numbers worth knowing: a 12,000-word chapter imports in 1.3s. Opening a page costs
more the longer the lesson is, because the page boundaries are re-derived from every
token each time: 5ms on a 2,000-word article, 10ms at 20,000, 31ms on a 100,000-word
book. The dictionary is a 573MB download that leaves 12MB in the database.

Not built: audio, EPUB import, Russian, sync, anything on a phone.

### Four rules the pilot decided by hand

- **Confidence.** spaCy gives no per-token score, so the only honest signal is the
  tagger admitting defeat: POS `X` falls back to the surface form (rule 7). The
  fallback happens in the adapter; there is no confidence column any more, because
  nothing ever read it.
- **When a form counts as met.** Not on page open — that would erase the novel-form
  highlight before you'd read the word. Recorded when you act on a word, and in bulk
  when you turn the page, for every word you have judged rather than only the known
  ones. Words you have *not* judged are still left out, for the reason above.
- **What "the rest" means.** "Mark page known" takes the blue words only. A word you
  set to learning stays learning.
- **Verb tense.** `fr_core_news_md` scores 8/16 on tense and mood and never produces a
  conditional. French endings are uniform across verbs, and future/conditional stems
  always end in `-r`, so a form can be classified against its own lemma with certainty
  (`nlp/languages/fr.py`). Where the rules are silent and the tagger is not
  trustworthy, no tense is shown at all: 14 correct, 0 wrong, 4 silent.

### Pages

~150 tokens, packed greedily and broken between sentences. **Derived at read time, not
stored**, and position is a token index, so changing the page size reflows a book
without losing anyone's place. Position never moves backwards.

## Next

1. **Confirm the hosting, then set a backup destination.** The box is provisioned:
   netcup Vienna, Debian 13, `v2202609408983511171.ultrasrv.de`, built by
   `scripts/provision.sh` (two passes, deploy key added, script ran to completion).
   Deploys are now `ssh llt@159.195.244.92 '/opt/ll-textreader/scripts/deploy.sh'`.

   Three things were never confirmed in-session and should be, first thing:
   - `curl -sS -o /dev/null -w '%{http_code}\n' https://v2202609408983511171.ultrasrv.de/api/health`
     — **401 is the pass**: valid certificate, backend up, password enforced.
     502 means the backend is down, a TLS error means the certificate did not issue.
   - The root password netcup emailed in plaintext — rotated, or still the emailed one?
   - SSH still accepts passwords. `deploying.md` has the two-line hardening; it was
     deliberately left for a human, because getting it wrong locks you out.

   Then the one real gap: **the backups have nowhere to go.** The timer runs daily and
   `backup.sh` works, but `LL_TEXTREADER_BACKUP_TO` is unset, so every copy lands on the
   same disk as the database. `decisions/0006` is blunt about why that is not a backup.

2. **Russian** — `decisions/0012`. Before accounts, deliberately: Russian is the thing
   that proves the lemma-keyed model was worth building, and it is better to find that
   out before strangers arrive. Mostly front-end work; the step not to skip is measuring
   Russian morphology before trusting it.
3. **Export the lessons, and account deletion** — `decisions/0013`. An afternoon each,
   and they are what "your data is yours" actually means. Worth having whether accounts
   ever happen or not.
4. **Accounts**, by invite first — `decisions/0013`. Roughly two days to an invite-only
   beta; open sign-up is then a flag, and password reset can wait behind invites.

Alongside all of it: read with the thing. Every real bug so far came from using it, not
from the tests — the Finish button that did nothing, "mark known" eating learning
words, levels rising five times too fast. That is still the highest-yield activity
available.

## Planned in detail, not started

- **Multi-language and Russian** — `decisions/0012`. Mostly front-end: `lang` is already
  a key everywhere and adapters load by module name. The step not to skip is measuring
  Russian morphology before trusting it, the way French was measured.
- **Multi-user** — `decisions/0013`, with a recommendation to run an instance per reader
  instead until that becomes the annoying part.
- **Local-first** — `decisions/0014`. A direction rather than a plan, plus the four small
  things worth preserving now so it stays possible. `decisions/0015` answers a
  zero-cost-hosting proposal and names the fork it implies: going fully static means
  giving up the POS tagger, which is the thing this project exists to have.

## Waiting, deliberately

Russian · a phone client · audio · multi-user. None of these is blocked; they are
held back so the desktop reader gets good first. Multi-user in particular stays out:
a second reader is a second container (`docs/deploying.md`), not an auth system.

## Testing

207 tests: 184 backend (pytest), 23 frontend (vitest). `npm test` in `frontend/`.
Seven of the backend ones need the real French model and skip without it, so
`./scripts/setup-models.sh fr` is part of running the suite, not just the app.

The frontend tests cover `reading.ts` and `morph.ts` — pure functions, no DOM and no
component framework, deliberately. What they pin is the logic that is easy to get
subtly wrong: that laying spans over the text loses no character of it, that Tab
wraps and then stops, and that `Imp` is imperfect under Tense and imperative under
Mood. React rendering is still only checked by driving a browser.

`test_counts.py` earns its place separately: the library's per-lesson counts are cached,
and it compares the stored numbers against counting from scratch after every operation
that could move a word between buckets. A drifted count is worse than a slow one.

## Known, not urgent

Written down so the next session doesn't rediscover them and think they are news.

- **Page open is linear in the length of the lesson.** `_pages()` groups a lesson's
  whole token stream by sentence on every read, every page turn and every
  translation request — the numbers above. A covering index halved it and the shape
  is unchanged. The fix, when it is worth doing, is the same one decision 0016 used
  for the library: derive the boundaries once and keep them, invalidated by
  `pipeline_id`. Not now: 31ms is not felt, and it only bites on whole books.
- **DNS rebinding on URL import.** `decisions/0018` says why it is left open and
  what changes that: accounts.
- **`ago()` is written twice**, in `Vocab.tsx` and `LessonList.tsx`, with different
  wording on purpose. Both had the same timestamp-parsing bug. A third copy means
  it is time to merge them.

## Open questions

- Levantine Arabic: MSA-trained analysers mis-handle بدي / عم بكتب / مش. Not a pilot
  problem — see `decisions/0002-arabic-pipeline.md`.
- Does "turn the page" remain the right moment to record met forms, under real use?
