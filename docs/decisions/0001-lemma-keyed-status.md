# 0001 — Status is keyed on the lemma, with a separate form-seen table

**Decided:** 2026-09-01 · **Status:** accepted

## Context
The obvious implementation tracks a status per surface form. It is trivial and works for
any language without NLP. It also makes the word counts fiction in morphologically rich
languages, which is exactly where this app is meant to be useful (Russian, Arabic).

## Decision
Key status on `(lang, lemma, pos)`. Track met inflections separately in `form_seen`.
Render a known lemma in an unmet form as a third, lighter state.

## Consequences
- Requires a POS tagger, so lemmatisation must run at import, not at render.
- Lessons become token streams with char offsets, not strings.
- Needs `lemma_override` as an escape hatch, or model errors are unfixable by the user.
- Row count roughly doubles. Irrelevant at this scale.
- Difficulty scoring and any word-count milestone must be computed, never stored.
