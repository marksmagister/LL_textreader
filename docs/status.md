# Status & roadmap

Current state and what's next. Design lives in `../CLAUDE.md`, the data model in
`data-model.md`, and the reasoning behind individual decisions in `decisions/`. Those
change on a decision; this file changes on an event. Don't copy one into the other.

## Where things stand

**Readable.** Paste French text, get it back coloured, click words, and the page
decolourises as you go. That is the product, end to end, for one language.

Working and verified against real text:
- French pipeline: spaCy `fr_core_news_md`, POS-tagged lemmas, run at import
- plain-text import (paste or `.txt`), reader, lookup panel, pages, saved position
- all four render states, including known-lemma-novel-form
- 12,000-word chapter: 1.3s to import, 0.08s to open a page. The join is not the problem
- 29 tests, ruff and tsc clean

Not built: dictionary glosses, the `lemma_override` UI, EPUB/URL import, Russian,
audio. `hint`, `root_index` and `reading_progress.last_token` are schema-only.

### Three rules the pilot decided by hand

- **Confidence.** spaCy gives no per-token score, so the only honest signal is the
  tagger admitting defeat: POS `X` falls back to the surface form (rule 7).
- **When a form counts as met.** Not on page open — that would erase the novel-form
  highlight before you'd read the word. It's recorded when you act on a word, and in
  bulk when you turn the page. So the highlight resolves when you say you've read it.
- **What "the rest" means.** "Mark page known" takes the blue words only. A word you
  set to learning stays learning: you made a decision about it, and a bulk button must
  not silently reverse it.

### Pages

A page is ~150 tokens, packed greedily and broken between sentences. Pages are
**derived at read time, not stored** (`api/lessons.py:_pages`), and your position is
kept as a token index, so changing the page size reflows a book without losing anyone's
place. Turning a page saves that position; position never moves backwards, so
rereading chapter two doesn't forget that you'd reached chapter nine.

Words cleared on one page are known on the next — that is the point of the button.

## Next

0. **Show the morphology.** The lemmatiser already knows that `marchait` is
   `Tense=Imp|Number=Sing|Person=3` — spaCy hands it over for free in `token.morph`
   and we currently throw it away. Storing it and showing it in the panel answers
   *why* a word looks different, not just what it belongs to. It is the natural
   partner of the novel-form highlight: "you know marcher, this is the future."
   Needs a `morph` column, the adapter to fill it, and a human-readable rendering
   ("imperfect · 3rd person singular") rather than raw UD feature strings.
1. **Dictionary loader** — a kaikki.org French extract into `hint`. The lookup panel
   is a note field until this exists, which is the biggest hole in the pilot.
2. **`lemma_override` UI** — a "this is wrong" action. The read path already honours
   the table (`api/lessons.py`); nothing writes to it yet. Rule 5 says the colouring
   loses trust without it, so this is not optional for long.
3. **EPUB import**, then URL.
4. **Reading position** — `reading_progress.last_token` is written but never read.
5. **Russian**, if the pilot survives contact with actual reading. One adapter file.

## Open questions

- Levantine Arabic: MSA-trained analysers mis-handle بدي / عم بكتب / مش. Dialect-ID step
  routing to a dialect analyser, or accept the accuracy hit and lean on `lemma_override`?
  Not a pilot problem — see `decisions/0002-arabic-pipeline.md`.
- Does "Done reading" as the thing that records met forms survive real use, or does it
  need to follow the scroll position instead?
- Where audio and sentence-level timestamps fit, if at all.
