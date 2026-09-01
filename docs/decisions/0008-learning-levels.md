# 0008 — The 1–4 learning levels

**Status: proposed, undecided.** Written for the maintainer to accept or reject.

## The problem, as put

> I find the different levels of knowing a word a bit difficult to use — nobody can tell
> how well they know a word in a text, and they are never prompted to check or compare
> it, so those things easily go out of date.

This is correct, and it is worse than it looks. The 1–4 scale asks for a judgement
nobody can make reliably ("how well do I know *quai*, on a scale of four?"), records it
at the single worst moment to ask (mid-sentence, in a hurry), and then never revisits
it. Every number in the table is a guess made once and never corrected. Filtering or
scoring on it would be building on sand.

It is also, notably, a flashcard-era artifact. Decision 0005 says to leave SRS out
because "re-encounter in context is the actual mechanism". A self-rated confidence score
is the same idea wearing a different hat.

## Recommendation: keep the field, delete the self-rating

Don't remove the levels — **stop asking the user for them, and let exposure set them.**

The app already records exactly the right signal and currently only uses it for
colouring: `form_seen.count`, incremented every time a word appears on a page you
finished. That is an observation, not a guess.

- The reader offers three actions: **learning**, **known**, **ignore**. That is the full
  set of judgements a person can actually make about a word in front of them.
- A word marked learning starts at 1 and **rises automatically as you meet it again**,
  one level per encounter on a finished page.
- At 4, it is promoted to known — with the promotion visible and reversible, not silent.

The number then means something checkable: *times met since you flagged it*. It cannot
go stale, because it is derived from behaviour rather than opinion.

## Why not simply collapse to three states

Because the middle band is where the interesting information is, and the data is already
there. Collapsing throws away the only honest measure of "how far along am I with this
word" the app can obtain without interrogating the user. Keeping it costs nothing: the
schema is unchanged, and the UI gets *simpler*, not more complex.

## What changes

- Panel and shortcuts: `1` becomes "learning", `2`/`3` retire, `4` retires. `k` and `i`
  as now. Fewer keys, not more.
- On page turn, bump the level of every learning lemma that appeared. Promote at 4.
- Vocabulary page shows "met 3 times" instead of "learning 3".
- Nothing in the schema moves.

## Risks

- **Silent promotion is annoying if wrong.** Mitigate by showing what was promoted when
  a page is turned, and making it one click to send a word back to learning.
- **Encounters aren't understanding.** Meeting *quai* four times doesn't mean you know
  it. But it is a strictly better estimator than a number you invented once, and the
  cost of being wrong is one click.
- If this turns out worse in practice, the retreat is trivial: stop bumping, and the
  levels become inert.

## The alternative, if this is rejected

Collapse to new / learning / known / ignored and drop the middle entirely. That is
honest and simple. It just leaves a real measurement on the floor.
