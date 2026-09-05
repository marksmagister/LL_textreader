# 0025 — Reading statistics

**Status: planned, not built.** From report #24. Written because the maintainer
asked for a good plan rather than a quick feature, and because the cheap version
and the expensive version differ by a schema change.

## The report

> long term it could be cool to track stats a little bit (like the heat map sort
> of thing for streaks that claude code has, where every day gets coloured in
> depending on the work done. Smth along those lines would be very neat and
> motivating i'd think. Long term we could think about how one might even offer
> statistics across languages

## The good news: most of it is already stored

Nothing new has to be recorded to draw a year of daily activity. Three tables
already carry dates, and each answers a different question:

| table | column | what a row means |
|---|---|---|
| `exposure` | `(user, lang, lemma, pos, lesson, page)` | you finished a page containing this word |
| `lemma_status` | `updated_at` | you judged a word — the deliberate act |
| `form_seen` | `first_seen` | you met a shape of a word for the first time |
| `reading_progress` | `last_read` | you turned a page in this lesson |

`exposure` is the interesting one. It has no timestamp of its own — but it is
written when a page is finished, so **adding one `created_at` column to it gives
a complete daily activity log for free**, with no new writing path and nothing to
keep in step. That is the whole schema change.

Without even that, `lemma_status.updated_at` and `form_seen.first_seen` already
give "words judged per day" and "new shapes met per day", which is a real heat map
covering every day the reader has used the app.

## What to build, in order

### 1. A heat map of one thing, not four

A year grid, one square per day, shaded by **words judged that day** —
`COUNT(*) FROM lemma_status WHERE date(updated_at) = ?`. One number, because a
heat map that blends pages, words and minutes is a heat map nobody can read.

Words judged is the right number: it is the deliberate act, it is what the level
system already counts from (`0008`), and it cannot be inflated by leaving a tab
open. Pages turned would reward skimming; time spent would need a timer, which
means recording when someone is *not* reading, which is a surveillance-shaped
feature this project should not grow.

### 2. A streak, honestly defined

Consecutive days with at least one word judged. Say the threshold out loud in the
interface rather than hiding it — an unexplained streak that breaks is worse than
no streak. **No freezes, no repair, no notifications.** The moment a streak can be
bought back it stops measuring anything, and the moment it sends a push it is
nagging rather than reflecting.

### 3. Across languages, which is the part worth thinking about

The report is right that this is the interesting question, and it is also where
it gets easy to build something dishonest. **A word in Russian is not a word in
French.** 500 French lemmas and 500 Russian lemmas are not the same achievement,
and a leaderboard across the two invites exactly the comparison the data cannot
support.

So: **shared axis, separate series.** One heat map of total activity, because
"did I do anything today" genuinely is one question. Per-language counts shown
side by side, never summed into a single score and never ranked. `lang` is
already a key on every one of the tables above, so this costs a `GROUP BY` and
nothing else.

### 4. What it should never become

Written down now because these are the natural next asks and each would make the
thing worse:

- **No goals or targets.** A daily target turns a reading app into a chore with a
  guilt mechanic, and the honest failure mode of this product is reading less,
  not reading less than a number.
- **No comparison with other people.** Single-instance, single-user by design
  (`CLAUDE.md`); there is nobody to compare with and there should not be.
- **No estimated vocabulary size**, unless it is measured. "You know ~4,200
  words" is the kind of number people quote, and this app only knows about words
  it has actually shown you.

## Cost

- one column on `exposure`, or zero if `updated_at` is enough to start
- one endpoint, `GET /api/stats?lang=`, returning `[{day, judged, met, pages}]`
- one screen, reachable from the palette like everything else
- the grid itself is a `<div>` per day and about thirty lines of CSS; no chart
  library, no dependency

Call it a day, and it is a day that adds nothing to the reading path — which is
the argument for doing it *after* the lemmatiser work in `0024`, not before.
