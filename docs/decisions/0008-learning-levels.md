# 0008 — The 1–4 learning levels

**Status: accepted, with one amendment, and implemented.**

The amendment: **no automatic promotion to known.** Levels rise with exposure and
stop at 4, where the word is marked with a dotted rule that asks "do you know this
now?". Only the reader promotes a word. The app can observe how often you have met
something; it cannot observe whether you understood it.

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
  **one level per finished page**, however many times it appears on that page. A word
  three times in one paragraph is one encounter: what makes a repeat worth anything is
  the delay before it, and within a page there is none.
- At 4 it stops, and is rendered with a dotted rule: met often enough that you should
  decide. Promotion to known is always yours.

The number then means something checkable: *times met since you flagged it*. It cannot
go stale, because it is derived from behaviour rather than opinion.

## Why not simply collapse to three states

Because the middle band is where the interesting information is, and the data is already
there. Collapsing throws away the only honest measure of "how far along am I with this
word" the app can obtain without interrogating the user. Keeping it costs nothing: the
schema is unchanged, and the UI gets *simpler*, not more complex.

## Two different numbers

`form_seen.count` counts *occurrences*; the level counts *pages*. The vocabulary page
shows the first as "seen 6×" and the second as the status. They are deliberately
different, and neither is a rating.

## What changes

- Panel and shortcuts: `1` becomes "learning", `2`/`3` retire, `4` retires. `k` and `i`
  as now. Fewer keys, not more.
- On page turn, bump the level of every learning lemma that appeared. Promote at 4.
- Vocabulary page shows "met 3 times" instead of "learning 3".
- Nothing in the schema moves.

## Risks

- **Encounters aren't understanding.** Meeting *quai* four times doesn't mean you know
  it — which is exactly why the level stops at 4 and asks instead of deciding.
- The dotted state could become a nag if a word sits there unanswered. Watch for it.
- If this turns out worse in practice, the retreat is trivial: stop bumping, and the
  levels become inert.

## The alternative, if this is rejected

Collapse to new / learning / known / ignored and drop the middle entirely. That is
honest and simple. It just leaves a real measurement on the floor.
