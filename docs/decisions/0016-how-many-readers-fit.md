# 0016 — How many readers fit, and what it costs

Measured on the development machine against the real database, September 2026. An
M-series laptop is roughly two to three times quicker than the netcup box's two shared
vCPUs, so halve the throughput figures and leave the storage ones alone.

## What was measured

| | |
|---|---|
| shared data (dictionary, one copy however many readers) | 8.9 MB |
| a reader's own data, 15 lessons | 0.8 MB |
| per lesson | 53.5 kB |
| per known word | 120 bytes |
| open a page | 3.9 ms |
| open the library | 1.8 ms (was 85 ms — see below) |
| import | ~11,000 words/s |
| concurrent page opens | 52–208 req/s |

## The three limits, in order of how far away they are

**RAM is not the limit, and this is the important one.** The spaCy model is loaded once
per process and shared by every request, not per reader. Python, French and the
translation model together are about 1.2 GB and *do not grow with the number of
readers*. The 4 GB box holds that with room for Russian.

**Storage is not the limit either.** The dictionary is 8.9 MB once, not per person. A
heavy reader with 500 lessons is about 28 MB; a normal one with 50 is under 3 MB.
Against 100 GB of usable disk that is somewhere between three thousand and thirty
thousand readers.

**CPU is the limit, and it is further out than expected.** A reader in a twenty-minute
session turns maybe ten pages, rates thirty words and loads the library once — about
0.3 seconds of server work, call it a second with overhead. Two vCPUs have 172,800
seconds a day. Concurrency, not total work, is what binds: at roughly 25 requests a
second sustained on the smaller box, and about one request per ten seconds from someone
actually reading, that is **200 or so people reading simultaneously**. If one in twenty
registered readers is reading during the busy hour, the box holds **three to four
thousand registered readers**.

Imports are the spike. One is a second or two of solid CPU on the VPS, and ten people
importing a chapter at the same moment will stall everyone. That wants a concurrency
limit long before it wants a bigger machine.

## The library listing, measured twice

The first measurement said 121 ms at 10,000 tokens and extrapolated to four seconds at
500 lessons. **That measurement was wrong** — the benchmark query omitted `lang` from
the join, which defeats the primary key index and made it seven times slower than the
query the code actually runs. The real figures were 8 ms at fifteen lessons, 283 ms at
five hundred, 1.2 s at two thousand.

Still linear in every token you have ever imported, and still worth fixing, so it is
fixed. The counts are now stored on the lesson row and recomputed only for the lessons
a change actually touches — see `counts.py`. Measured after:

| lessons | tokens | before | after |
|---|---|---|---|
| 15 | 9,750 | 8 ms | 0.0 ms |
| 100 | 65,000 | 60 ms | 0.1 ms |
| 500 | 325,000 | 297 ms | 0.7 ms |
| 2,000 | 1,300,000 | 1,214 ms | 2.4 ms |

The endpoint went from 85 ms to 1.8 ms, and is now linear in the number of lessons
rather than the number of words in them.

The rule that keeps the cache honest is **recompute, never adjust**: no arithmetic on
deltas, no reasoning about what a change implies. `test_counts.py` compares the stored
numbers against counting from scratch after every operation that could move a word
between buckets, because a drifted count is worse than a slow one.

## What it costs

| readers | box | €/month |
|---|---|---|
| 1–50 | the current VPS 500 G12 | 5.72 |
| a few hundred | the same | 5.72 |
| ~3,000 | same, watch imports | 5.72 |
| ~10,000 | 8 GB, 4 vCPU | 12–15 |
| 50,000+ | several machines, a CDN, real operations | 100+, and no longer a side project |

## What this does to the zero-cost argument

0015 answered a plan built on the premise that cost scales fast with users. **The
measurements say it does not** — not for this shape of application on one box — because
the two things that would scale per-user are shared: the dictionary is one copy and the
models are one copy. Per reader, the marginal cost is a few megabytes of disk and a
second of CPU a day.

That plan estimated donations at under 1% conversion bringing €20–40 a month at a few
thousand users, and judged it hopeless against a growing bill. Against **€5.72**, the
same estimate covers the bill several times over. The argument does not fail because
the conversion estimate was wrong; it fails because the bill is two orders of magnitude
smaller than assumed.

## Keeping it free, in order of preference

1. **Say it is self-hostable and mean it.** `docs/deploying.md` is a page and a script.
   A Reddit audience for a French-reading tool skews technical; some will run their own,
   and every one who does costs nothing and gains full ownership.
2. **Cap the hosted instance.** Invite-only, or a waitlist with a number on it. Cost
   stays bounded by choice rather than by hope, and a small instance stays fast.
3. **Ask, once, quietly.** At €6 a month a handful of supporters covers it permanently.
   No tiers, no gating, no feature held back — which is also the only version of this
   that does not sour an open-source project.
4. **If it ever genuinely outgrows one box**, that is the moment to revisit 0015, and
   the honest price of its architecture is the POS tagger.

Nothing here needs deciding before publishing. The one thing that does is the library
query.
