# 0012 — Multi-language, and Russian

**Status: planned, not built.**

Russian is the test of the whole data model. French barely needs lemma-keyed status —
a verb has a few dozen forms and you can nearly get away with surface forms. Russian is
where `(lemma, pos)` and the novel-form state stop being a nicety, so this is also the
first honest check that the model was worth building.

## What is already done

More than it looks:

- `lang` is a column on `lesson`, `collection` and `hint`, and part of the key on every
  lexicon table. Nothing is French-only in the schema.
- `get_adapter(lang)` loads `nlp/languages/<code>.py` by module name. Adding a language
  is adding one file; no registry to edit.
- `setup-dictionary.sh` and `setup-models.sh` already take a language argument.
- `settings.languages` exists and `/api/health` already reports it.
- Literata was chosen over a system stack **because it has real Cyrillic** (0004).

What is genuinely missing is the front end: `const LANG = 'fr'` on line 11 of `App.tsx`.

## The work, in order

### 1. Language as a choice, not a constant

A selector in the header, populated from `/api/health`, remembered in `localStorage`
next to the theme. It sets the language for import, for the vocabulary page, and
**filters the library** — a Russian lesson among French ones is noise, and the selector
is where you say which you are reading today.

`Vocab` and the export already take `lang`; they only need it passed from state rather
than from a constant.

### 2. `nlp/languages/ru.py`

A near-copy of `fr.py` minus the French tense rules: `spacy.load("ru_core_news_md",
exclude=["ner"])`, same `AnalysedToken` shape, same POS-`X` confidence fallback,
`pipeline_id` stamped the same way.

### 3. Measure the morphology before trusting it

This is the step not to skip. French scored **8/16** on tense and mood and never once
produced a conditional, which is why `fr.py` has rules. Russian will have its own weak
spots and they will not be the same ones. Write the equivalent table — sixteen forms
with the case, number, aspect and tense they actually are — and run it before writing
any display code. If something is systematically wrong, it gets rules in `ru.py`, which
is where language-specific knowledge already lives.

Expect case to be reasonable and aspect to be the risk.

### 4. `morph.ts` needs the features Russian is made of

It handles VerbForm, Mood, Tense, Person, Number, Gender, Definite, Polarity, NumType,
Poss, Reflex. Russian needs **Case** above all — a Russian word with no case shown is
a word with nothing shown — plus **Aspect** (imperfective/perfective) and **Animacy**.

Order matters for reading: "genitive plural", not "plural genitive". The existing
phrase-ordering logic already does this kind of thing for person and number.

### 5. Dictionary and translation

`./scripts/setup-dictionary.sh ru` — the loader is language-agnostic already. The
Russian extract is **937MB** against French's 573MB, and leaves about the same ~15MB
of glosses behind.

Translation is one line: `("ru", "en"): "Helsinki-NLP/opus-mt-ru-en"` in `MODELS`.

## Two things to decide before writing code

**ё and е.** Russian text often writes `е` where the word has `ё`. Folding them in
`norm` would merge **всё** and **все**, which are different words. The recommendation is
**do not fold**, and accept that a text written without ё will lemmatise some words
separately. Note it as a known limitation rather than fixing it wrongly.

**Aspect pairs.** читать and прочитать are different lemmas and should stay that way —
they are different vocabulary items, the same argument as the Arabic root in rule 4.

## Cost and risk

About a day, plus the download. The real risk is RAM: each spaCy model is 200–500MB
resident and translation adds ~700MB more. Loading is already lazy, so only what you
actually read gets loaded, but `LL_TEXTREADER_LANGUAGES` should stay short and the 4GB
box is the constraint to watch.
