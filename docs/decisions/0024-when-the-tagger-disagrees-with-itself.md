# 0024 — When the tagger disagrees with itself

**Status: measured, not yet decided.** Reports #22, #25 and #27 are one problem.
The measurement is below; the choice of rule is the maintainer's, and 0021 is the
constraint it has to satisfy.

## The reports

> #25 The second time "aimez" appeared here it did not lematise it. maybe because
> within aimez-moi, maybe different reason
>
> #27 "flemme" was recognised as two different words here (?) why does that
> happen explain. see if fixable. supsicions: due to grammatical contexty(?)
>
> #22 there should be slightly improved lemmatisation - we are sometimes missing
> obvious verbs or lemmatising a verb to a related noun

## What is actually happening

The suspicion in #27 is right. The same word, twice on a page, gets two different
POS tags — and **POS is part of the lexicon key** (`CLAUDE.md` rule 3), so one
word becomes two vocabulary entries:

```
"aimez-moi" ( aimez-moi )   →  aimez → aimer VERB  ·  aimez → aimez X
j'ai la flemme ( flemme )   →  flemme → flemme NOUN ·  flemme → flemme PROPN
```

Rule 7 is working as designed in the `X` case — the tagger gave up, so the
surface form was used rather than a guess. The damage is not a wrong lemma; it is
an entry that splits in two.

## The measurement

All 22 lessons in the maintainer's own library, 14,298 tokens, 11,962 of them
lexical. Counting only surface forms that split across POS *where one reading is
a give-up tag* (`X` or `PROPN`) — a `NOUN`/`ADJ` split is usually a real
homograph and should stay two entries.

| | |
|---|---|
| surface forms damaged this way | **30** |
| ...of which in one lesson (rap lyrics) | **15** |
| damaged tokens | 101 (87 `PROPN`, 14 `X`) |
| base rate outside that one lesson | **15 in ~9,650 lexical tokens ≈ 0.16%** |

Where the damaged tokens sit:

| position | tokens | share |
|---|---|---|
| opens a sentence or a line | 35 | 35% |
| inside brackets | 44 | 44% |
| capitalised mid-sentence | 7 | 7% |
| lowercase mid-sentence | 15 | 15% |

**The bracket figure is one lesson.** It is song lyrics, where `(...)` marks
ad-libs and every chorus word is echoed in brackets. No other text in the library
does this. Treating 44% as the headline would be fitting a rule to one document.

## What the sample shows, and it was not what was expected

The damaged openers are:

```
Bon(ADJ) · Viens(ADJ) · Ah(ADV) · Normalement(ADV) · Douze(PRON)
Pardon(NOUN) · Vas(NOUN) · Samedi(NOUN) · Salut(VERB) · Prends(VERB)
```

`fr.py` **already has a rule for exactly this position** — a capitalised word
opening a sentence gets read again on its own — and it is refusing almost all of
them, because it takes the second reading *only if it comes back a verb*. That
guard was written for report #14, where the goal was recovering `Tenez → tenir`,
and it does its job. It simply never fires for `Bon`, `Ah` or `Pardon`.

So the largest fixable category is not brackets. It is a rule that already exists
and is one condition too narrow.

## The options

**A. Widen the opener rule where the lemma agrees.** Take the isolated reading's
*part of speech* when both readings produce the same lemma, and leave everything
else alone. `Bon` is `bon` either way, so `PROPN` is simply wrong and `ADJ` is
simply right — that is certain from the two readings, which is what 0021 requires.
Where the lemmas differ (`Porte` → `porte` NOUN vs `porter` VERB) nothing changes,
which is the case the existing comment warns about and it stays warned about.
Fixes most of the 35, and the existing VERB path is untouched.

**B. Also re-read bracketed tokens.** Same shape, applied to a token inside
`( )`. Fixes #25 and #27 directly. But the evidence for it is one lesson of song
lyrics, and `CLAUDE.md` is explicit that a rule wants a second caller.

**C. Nothing, and use the override.** 0.16% is roughly one word in 640 — about
one per two pages of prose, and `o` already fixes each in a keystroke. Four
overrides exist after weeks of reading, so the escape hatch is not under strain.

**Recommendation: A now, B only if a second text ever shows the pattern.** A is
narrow, certain, and fixes the category that recurs across nine different
lessons. B currently fits one document.

## Whichever is chosen

It changes stored token streams, so `RULES` in `fr.py` must go up and every French
lesson needs reprocessing (`CLAUDE.md` rule 6) — and the pronoun-entry lesson from
`0021` applies again: entries keyed on the old POS stop matching, so a few words
come back blue once.

## Reproducing the numbers

The two scripts that produced this table were throwaways and are not in the repo.
What they did: for every lesson, group tokens by `norm`, keep the groups with more
than one `pos` where one of them is `X` or `PROPN`, and classify each by whether
it opens a sentence, sits inside brackets, or neither. Anyone can rewrite that in
twenty lines against the read-only database.
