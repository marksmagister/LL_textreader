# Data model

The product is one join. A lesson's token stream, joined against your personal lexicon,
resolved at render time — everything else is UI around that.

## Why the lemma, not the surface form

Keying status on the surface form is cheap and language-agnostic, and it keeps the reader
honest about what you can recognise on a page. It also wrecks the numbers: French verbs
alone put dozens of forms behind one word, Russian inflates a "known words" count
several-fold against English, and Arabic is worse, because
clitics attach to the orthographic word — `وسيكتبونها` is و + س + يكتبون + ها, four
learnable units in one whitespace-delimited string.

So the status key is `(lang, lemma, pos)`.

Full lemma collapsing is too aggressive on its own: knowing *courir* doesn't mean a
beginner parses *courussent*. Hence the second table.

| table | holds | changes when |
|---|---|---|
| `lemma_status` | do you know this word | you mark it |
| `form_seen` | which shapes of it you've met | you read |

Render:

- lemma new → **blue**
- lemma learning → **yellow**
- lemma met on four pages → **hollow blue** — the app stops guessing and asks
- lemma known, form novel → **a lighter tint**
- lemma known, form seen → **plain**

The third state is what the two-table split buys. It also gives coverage data for free —
"you've met 40 verbs but never a past subjunctive" — without asking the user anything.

Cost: roughly double the rows. Still tiny.

## Why POS is in the key

`porte` is *porter* (verb, 1sg) or *porte* (noun, door); `est` is *être* or the compass
point. A context-free lemmatiser gets these wrong constantly. A POS-tagged one gets them mostly right — which is worse in a way, since
rare failures are more confusing than frequent ones. Including POS separates the
homographs cleanly and lets you know one without the other, which is correct behaviour.

The remaining failures need `lemma_override`. Without a user-facing "this is wrong", one
bad model decision is unfixable and the colouring stops being trusted.

## Why offsets, not reconstruction

`lesson.body` is the original text, untouched. Tokens carry `char_start`/`char_end` into
it and spans are overlaid at render. Never rebuild display text from tokens: Arabic
segmentation is one-to-many, and any lossy tokenisation would silently corrupt the text.

## Pages are derived, position is a token index

A lesson is stored whole; pages are computed from the token stream on each read and
never stored. `reading_progress.last_token` is a token index, not a page number, so
the page size is free to change — an imported book reflows and every reader keeps
their place. Storing page numbers would have frozen the layout the day it was imported.

## Difficulty is not a property of a lesson

Blue density in a text is a per-user score. Content filtering and recommendation derive
from it, which means they must be computed against the reader, never stored on the lesson.

## Migration note (for when it applies)

If surface-form statuses ever exist and need lemmatising:

- all forms of a lemma known → lemma known, all forms marked seen
- mixed → take the max, but **cap at learning, not known**; three of eight forms shouldn't
  buy the lemma
- ambiguous with no context → leave as an orphan surface entry, resolve on next encounter

Every known-word count drops, often by half in Russian. Run it in shadow mode and diff
first. Any milestone or difficulty constant tuned against the old numbers needs refitting,
not adjusting.
