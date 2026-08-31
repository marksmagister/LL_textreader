# 0003 — AGPL-3.0, and no third-party data in the repo

**Decided:** 2026-09-01 · **Status:** accepted

## Decision
- Own code under **AGPL-3.0**. It's a network app; AGPL is what stops someone running a
  closed hosted fork. Swap to MIT by replacing one file if that stops being the goal.
- **No third-party data ships in the repo.** Wiktionary/kaikki extracts are CC BY-SA and
  NLP models carry assorted licences. `scripts/` downloads them into `data/` at setup, so
  code and data stay separate and the repo's licence question stays simple.
- **Single-instance, single-user.** Each person's imports live in their own copy. This is
  the same footing as any read-later app. A shared lesson library would change that
  completely and is out of scope.
- **Don't name or style it after LingQ.** The method isn't copyrightable; the trademark is
  the thing that generates letters.

## Consequences
Donations for hosting don't change any of the above. `NOTICE` credits Wiktionary, spaCy
and Stanza and must stay accurate as sources are added.
