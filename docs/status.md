# Status & roadmap

Current state and what's next. Design lives in `../CLAUDE.md`, the data model in
`data-model.md`, and the reasoning behind individual decisions in `decisions/`. Those
change on a decision; this file changes on an event. Don't copy one into the other.

## Where things stand

**Readable, keyboard-first, with definitions.** Paste French text, read it coloured by
what you know, Tab between unknown words, and the page decolourises as you go.

Working and verified against real text, in the browser:
- French pipeline: spaCy `fr_core_news_md`, POS-tagged lemmas, run at import
- plain-text import (paste or `.txt`), pages, saved position, "mark page known"
- all four render states, including known-lemma-novel-form
- Wiktionary glosses: 126k senses for French, from a kaikki.org extract
- morphology: "conditional · 1st person singular", with rules that stay quiet
  rather than guess (see below)
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

0. **Deployment.** Files are written (`Dockerfile`, `docker-compose.yml`, `Caddyfile`,
   `docs/deploying.md`) but the image build is untested — no Docker on the machine.
   Single-user by design: a friend with the URL reads with your lexicon, which is what
   a demo wants and is not a login system.
1. **Edit and re-import a lesson.** If you notice a bad import on page 3 you should be
   able to fix the text without losing anything. Cheaper than it looks: the lexicon is
   keyed on lemma, not lesson, so it survives untouched. The only casualty is
   `reading_progress.last_token` — convert it to a character offset first, re-import,
   then snap to the first token at or after it. Merge this with the library folder
   below; they are the same mechanism.
2. **A watched library folder.** See `decisions/0006-managing-lessons.md`. One `.txt`
   per lesson in `data/library/`, imported on change by content hash. Solves import,
   export, editing and backup at once, and makes the corpus greppable.
3. **EPUB import**, then URL (trafilatura), then subtitles.
4. **Sentence translation, toggleable.** See `decisions/0007-sentence-translation.md`.
5. **Russian.** One adapter file, plus a decision about Stanza.

## Nice to have

- Reading position within a page (`last_token` is per page turn, not per scroll)
- Lexicon export (JSON/CSV) — the vocabulary is the asset, the lessons are replaceable
- Audio and sentence timestamps; `Space`/`Shift-Space` are reserved for it
- A phone client (PWA + iOS share-sheet import, see 0005) — **after** the desktop web
  app is good, not before

## Open questions

- Levantine Arabic: MSA-trained analysers mis-handle بدي / عم بكتب / مش. Not a pilot
  problem — see `decisions/0002-arabic-pipeline.md`.
- Does "turn the page" remain the right moment to record met forms, under real use?
