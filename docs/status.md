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
- keyboard: Tab/Shift-Tab, 1, k, i, Shift-K, j/arrows, Enter, Esc, o, /
- levels counted from exposure, not self-rated (decision 0008)
- undo for "mark page known"
- the sentence you first met a word in, kept and shown
- `--dry-run`-able reprocessing for stale token streams (rule 6)
- 93 tests, ruff and tsc clean

Numbers worth knowing: a 12,000-word chapter imports in 1.3s and a page opens in
0.08s. The dictionary is a 573MB download that leaves 12MB in the database.

Not built: audio, EPUB/URL import, Russian, sync, anything on a phone.

### Four rules the pilot decided by hand

- **Confidence.** spaCy gives no per-token score, so the only honest signal is the
  tagger admitting defeat: POS `X` falls back to the surface form (rule 7).
- **When a form counts as met.** Not on page open — that would erase the novel-form
  highlight before you'd read the word. Recorded when you act on a word, and in bulk
  when you turn the page.
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

1. **Finish the hosting.** The box exists — netcup, Vienna, Debian 13, at
   `v2202609408983511171.ultrasrv.de` — and `scripts/provision.sh` builds it in one
   command. What is left needs a human at a keyboard: rotate the root password netcup
   emailed in plaintext, run the script, paste the deploy key it prints into GitHub
   (the repo is private), run it again. Then TLS is automatic — netcup's hostname
   already resolves to the box, so there is no DNS to buy or configure.
   See `deploying.md` and `decisions/0018`. Until it is done, `./scripts/serve.sh
   --share` puts it on a Cloudflare tunnel from the laptop.
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
from the 195 tests — the Finish button that did nothing, "mark known" eating learning
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

195 tests: 174 backend (pytest), 21 frontend (vitest). `npm test` in `frontend/`.

The frontend tests cover `reading.ts` and `morph.ts` — pure functions, no DOM and no
component framework, deliberately. What they pin is the logic that is easy to get
subtly wrong: that laying spans over the text loses no character of it, that Tab
wraps and then stops, and that `Imp` is imperfect under Tense and imperative under
Mood. React rendering is still only checked by driving a browser.

`test_counts.py` earns its place separately: the library's per-lesson counts are cached,
and it compares the stored numbers against counting from scratch after every operation
that could move a word between buckets. A drifted count is worse than a slow one.

## Open questions

- Levantine Arabic: MSA-trained analysers mis-handle بدي / عم بكتب / مش. Not a pilot
  problem — see `decisions/0002-arabic-pipeline.md`.
- Does "turn the page" remain the right moment to record met forms, under real use?
