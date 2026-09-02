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

- lemma new → **solid blue**
- a form of it you have not met → **a dashed blue outline**
- lemma learning, form met → **yellow**
- lemma met on four pages → **a blue rule under the word** — time you decided
- lemma known, form met → **plain**

Blue means "this wants something from you", in three weights: solid you have never
judged, dashed you know the word but not this shape, underlined you have met it often
enough that it is time you decided. Yellow is the one state that is actively yours. The weights differ
by *shape*, not just shade — two blue fills of different darkness do not separate at
reading speed.

The novel-form state is what the two-table split buys. It also gives coverage data for free —
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
from it, which means they belong to the reader, not to the text.

They *are* stored on the lesson row all the same — `n_new`, `n_learning`, `n_known`,
recomputed whenever a word crosses between buckets (`counts.py`, `decisions/0016`).
That is safe only because a lesson belongs to exactly one user: `lesson.user_id` is
part of the row, so the cached numbers are already per-reader. The day two people
share a lesson, these columns are wrong and have to move to a table keyed on the
reader as well.

## Migration note (for when it applies)

If surface-form statuses ever exist and need lemmatising:

- all forms of a lemma known → lemma known, all forms marked seen
- mixed → take the max, but **cap at learning, not known**; three of eight forms shouldn't
  buy the lemma
- ambiguous with no context → leave as an orphan surface entry, resolve on next encounter

Every known-word count drops, often by half in Russian. Run it in shadow mode and diff
first. Any milestone or difficulty constant tuned against the old numbers needs refitting,
not adjusting.
