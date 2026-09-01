# 0015 — Response to the zero-cost hosting plan

A document arrived arguing that a LingQ-style reader should be local-first: IndexedDB
holds everything, Cloudflare Pages serves a static bundle, per-user cost is ≈ €0, and a
paid tier sells sync rather than features. It is well argued and its economics are
right. It also assumes one thing this project does not have.

## The one thing that decides it

**The plan works because it assumes no server-side NLP.**

LingQ can be local-first because LingQ mostly does not lemmatise — it treats surface
forms as terms. That is cheap, language-agnostic, and it is exactly the decision this
project was started to reject (0001). Our whole premise is `(lemma, pos)`: that *porte*
the door and *porter* the verb are different entries, and that a known word in an unmet
form is its own state. That needs a POS tagger. A POS tagger needs spaCy. spaCy needs
Python.

So the fork is not storage, and not egress. It is:

| | keep lemmatisation | go static |
|---|---|---|
| quality | `est` → *être*, `porte` disambiguated | homographs collapse |
| the novel-form state | works | still works, on worse lemmas |
| per-user cost | a server | ≈ €0 |
| scale | tens of readers | thousands |

Going static does not mean losing lemmatisation entirely — a lookup lexicon (Lefff, or
spaCy's own lookup tables) is a few megabytes and could be chunked and lazy-loaded
exactly as the plan proposes for definitions. What it loses is **disambiguation**,
because a lookup table cannot tell you which *porte* you are looking at without
context. Rule 7 already says a guess is worse than no lemma, and rule 3 says POS is part
of the key. A lookup-only lemmatiser contradicts both.

That is a product decision, not a hosting one, and it should be made deliberately rather
than arrived at by choosing a host.

## The scope question underneath it

The plan is written for thousands of users and a paid tier. `CLAUDE.md` currently says
the opposite: single-instance, single-user, each person runs their own copy, and no
shared lesson library — the last one for copyright reasons, not technical ones.

Nothing here is wrong, but the plan is answering a question that has not been asked yet.
Until "should this become a product with strangers on it?" is decided, the cost curve it
solves is hypothetical. Ten readers on a €5 box is not a problem that needs solving.

## What is worth taking regardless

Four things, none of which depend on going static:

1. **`navigator.storage.persist()` and a PWA install prompt**, asked for *after* the
   reader has invested something rather than on page load. On iOS this is the difference
   between IndexedDB surviving and being wiped after seven days. Relevant the moment
   there is a phone client (0005), and the plan is right that it is the single biggest
   data-loss vector there.

2. **Automatic periodic export**, not just the manual one that exists. The lexicon
   export already produces JSON; dropping one into Downloads every N days, with an
   obvious restore, is the thing that has saved a lot of Anki users. Inelegant and
   effective.

3. **Sync as one compressed blob per user, not normalised rows.** This corrects 0014,
   which described a row-by-row merge. The numbers say it plainly: 126,214 dictionary
   rows against 467 rows of actual lexicon. The private half is kilobytes — small
   enough that syncing it whole is simpler *and* cheaper than merging it per row, and
   O(1) per sync instead of O(n) per word.

4. **A `SyncBackend` interface with a local no-op implementation.** Good shape whether
   or not there is ever a paid tier: it keeps "no network at all" as a first-class mode
   rather than a degraded one.

## What does not apply

- **Static export mechanics.** The plan is written for Next.js. This is Vite; there is
  no `output: 'export'` question, and the frontend already builds to a folder of files
  that any static host would serve. The server is not there because of the framework.
- **Egress.** The dictionary is 126k rows *on the server*, queried a lemma at a time.
  It is not shipped to anyone. Egress is a few kilobytes of JSON per page turn.
- **Browser TTS.** Already done — `speak.ts` uses `SpeechSynthesis`, for exactly the
  reasons given.
- **BYO API key for LLM features.** There are no LLM features and 0007 explains why: a
  dedicated translation model is smaller, faster, deterministic and needs no key.
- **MIT over AGPL.** 0003 chose AGPL deliberately, to stop a closed hosted fork, and
  noted it is one file to swap if that stops being the goal. The plan's argument — that
  MIT deters nobody who would have converted — only matters once there is something to
  convert. Revisit if the product question is ever answered yes.

## Conclusion

Nothing here changes the near-term plan. Russian next, an instance per reader, and the
four preservation points in 0014 stand — with the blob correction above.

The plan becomes the right plan the day the answer to "is this a product?" is yes. At
that point the honest cost of taking it is the POS tagger, and that is worth naming now
rather than discovering later.
