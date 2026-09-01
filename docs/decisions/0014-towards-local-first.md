# 0014 — Towards local-first

**Status: direction, not a plan.** Nothing here is scheduled. It exists so the next
year of decisions do not quietly close the door.

## The constraint that shapes everything

Lemmatisation needs spaCy, spaCy needs Python, and Python does not run in a browser.
That was the founding decision (0005) and it has not changed. So **local-first cannot
mean "no server"** for this application, however much one might want it to.

What it can mean is that the server is *yours*. A personal instance holding only your
lessons and your vocabulary is local-first in the way that matters: nobody else's data
is in that database, nobody else's outage is your outage, and moving it is copying one
SQLite file. That is what running an instance per reader already gives, today, and it is
why 0013 recommends instances over accounts.

## Where the data would actually live

| | holds | why |
|---|---|---|
| server | lessons, token streams, dictionaries, models | needs Python, and is large |
| browser | the lexicon, as a cache | small, private, and read on every page |

The lexicon is the part worth having locally: 171 words today, a few hundred kilobytes
even at ten thousand. The token streams and the 126k-gloss dictionary are neither
private nor small, and belong where the compute is.

Browser storage is a **cache, not the source of truth**. Safari evicts storage from
sites unused for seven days, installed web apps included, and the File System Access API
does not exist outside Chromium. Losing a cache costs a re-download; losing the truth
costs six months of reading. 0005 already reached this conclusion for the phone.

## What to preserve, cheaply, starting now

Four things keep the door open. None is speculative work; each is small and defensible
on its own terms.

1. **Every user-owned row needs a modification time.** `lemma_status`, `exposure`,
   `reading_progress` and `bulk_undo` have one. **`form_seen` has only `first_seen`** —
   it should gain `updated_at`. Without it a merge cannot tell which side is newer.

2. **Keep the render join reproducible off the server.** Today the state of a word is
   computed in SQL. It is a lookup — token's lemma against a map of statuses — and
   `state_for()` is already one pure function in `models.py`. Keep it that way: no
   business logic that only exists inside a query.

3. **Natural keys in user data, never server-assigned ids.** `lemma_status` is keyed on
   `(lemma, pos)` and `form_seen` on `(lemma, pos, surface)`. Two devices can create the
   same row independently and it merges. This is already true; the point is not to
   break it.

4. **A raw mode for the reader.** Eventually the client wants the token stream *without*
   the joined state, so it can join against its own lexicon. That is a query parameter
   on an endpoint that already exists, not a new architecture.

## The merge, when it comes

**Corrected by 0015: send the lexicon as one blob, not row by row.** The whole private
half is 467 rows today and would be kilobytes at ten thousand words, against 126,214
rows of dictionary that never leave the server. A whole-blob sync is O(1) per sync
rather than O(n) per word, and it is less code than a per-row merge, not more.

Within a blob, or if per-row merging is ever needed anyway: the data is almost
monotonic, so no CRDT. Status takes the maximum, tie-broken on `updated_at`. `form_seen`
counts add. `exposure` is a set union — idempotence is its entire purpose. Notes are
last-write-wins. Lessons stay server-authoritative, since import only happens online.

The one genuinely awkward case is a *downgrade*: marking a known word back to learning
on one device while another still says known. Maximum would lose it. Timestamps settle
it, and the cost of getting it wrong is one word.

## What would make this wrong

If lemmatisation ever runs in the browser, all of it changes and the server becomes
optional. That is not close: a spaCy pipeline compiled to WebAssembly with its model is
hundreds of megabytes and nobody has made it pleasant. Worth checking again in a couple
of years, not worth designing around now.
