# 0023 — A novel form takes the colour of the word it belongs to

**Status: decided and built, 5 September 2026.** From bug report #28, filed while
reading. It changes the render rule in `models.py:state_for`, which `CLAUDE.md`
calls the point of the whole design, so it gets a file rather than a commit.

## The report

> okay so different versions of words i am learning right now, should not be blue
> light circled but just yellow light circled. that makes the most sense by far

## What was wrong

There were five render states, and one of them did two jobs. `novel-form` — a
dashed blue outline — meant "this is a shape of the word you have not met",
whether or not you had settled the word itself. So a word you were actively
learning, met in a new inflection, came out **blue**.

Blue is the colour this app uses for *the app asking you something*. Yellow is
the one state that is actively yours. So the old rule said, of a word you were
halfway through learning, "this is one for the app" — when in fact it is the
clearest possible case of a word that is yours and in progress. Reading it, the
word looked like it had been forgotten and handed back.

## The decision

**Colour and treatment become independent, and each says one thing.**

- **Colour** says whose the word is. Blue: the app is asking. Yellow: yours.
- **A dashed outline**, over either colour, says the *form* is new to you.

Which gives six states rather than five, but fewer *ideas* than before — two
orthogonal signals instead of one colour carrying an exception:

| lemma | form met? | render |
|---|---|---|
| never judged | — | solid blue |
| learning (1–3) | yes | solid yellow |
| learning (1–3) | **no** | **dashed yellow** ← new |
| met on four pages | — | blue rule beneath |
| known (5) | no | dashed blue |
| known (5) | yes | plain |

`review` still outranks both dashed states. A word the app has decided to ask
about is asking about the *word*, and that outranks a remark about the shape —
unchanged from before, and the reason `state_for` tests it first.

## Why this is not just a repaint

The dash was already doing the work of saying "new shape". What the old rule did
was overload the *colour* as well, so that the same colour meant two different
things depending on a condition you could not see. Splitting them means the
question "whose is this word?" now has one answer everywhere on the page, and it
is the answer the lexicon actually holds.

It also makes the novel-form idea legible in the case that matters most. In
Russian, most of what you meet in your first months is *new shapes of words you
are working on*, not new shapes of words you have mastered. Under the old rule
that whole experience was painted in the colour of "not yours yet".

## Cost, and what was considered instead

- **A second yellow, solid but lighter**, rather than a dash. Rejected on the
  rule `CLAUDE.md` already states: the weights must differ by *shape*, not just
  shade, because two fills of different darkness do not separate at reading speed.
  The dash is the shape difference, and it already existed.
- **Leaving it alone**, on the grounds that five states are easier to learn than
  six. Rejected because the sixth state is not a new idea to learn — it is the
  removal of an exception. The legend now shows the two dashed states adjacent so
  the contrast is a single glance.
- No schema change, no migration, nothing stored. `state_for` derives it from the
  status and `form_seen` that were already there, so this is display only and
  reversible in one line.

## What to watch

Whether dashed yellow and solid yellow separate fast enough while actually
reading. The dash is a one-pixel outline over a 45%-mixed fill; if it turns out
not to read, the fix is more contrast between the two yellows, not a third
colour. Nobody has read a long page in it yet.
