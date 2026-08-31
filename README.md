# LL_textreader

A reading app for language learners.

You read real text — an article, a book, whatever you actually want to read. Every word
is coloured by whether you know it. Blue means you've never seen it; click it, get a
definition, and it turns yellow. Words you know are plain black. The more you read, the
more the page decolourises.

There's no deck to grind. Review happens by meeting the word again somewhere else.

## Why it's not just a highlighter

Word status is tracked per **lemma**, not per surface form. *court* and *courraient* are
the same word; *كتب* and *يكتبونها* are the same word. But knowing a lemma doesn't mean
you'll recognise every shape of it, so a known word in an inflection you've never met gets
its own, lighter highlight. In French that's a modest gain. In Russian and Arabic it's the
difference between a useful word count and a fictional one.

## Status

Early — skeleton only, nothing to read yet. First target is **French**, then possibly
Russian. Arabic is designed for but deliberately not built yet; Dutch comes last.

## Setup

Requires Python 3.12 and Node 20+.

```bash
git clone git@github.com:marksmagister/LL_textreader.git
cd LL_textreader
uv sync                      # backend deps
./scripts/setup-models.sh fr # downloads NLP models — not vendored, see NOTICE
./scripts/setup-dictionary.sh fr
cp .env.example .env
uv run uvicorn ll_textreader.main:app --reload --app-dir backend

cd frontend && npm install && npm run dev
```

## Licence

AGPL-3.0. No third-party data ships in this repo — the setup scripts fetch it. See
`NOTICE` for what gets downloaded and under what terms.

Not affiliated with, derived from, or a copy of any existing reading app.
