# 0009 — The next five steps, and the most boring way to do each

Planning only. Nothing here is built. The question asked of every item was "what is
the most boring way to do this", because the boring version is the one still
comprehensible in a year.

## The pivot

Everything below is downstream of one question: **does the Tab-and-rate loop feel good
after a fortnight of real reading?** Decision 0005 said to build the import pipeline and
the reader, then find out. If the answer is no, hosting, multi-user and audio are all
wasted motion. So the alpha is not step one of five — it is the thing the other four
are waiting on.

## 1. Alpha, and fixing what it turns up

**Boring version:** read with it, keep a list, fix what annoys. No infrastructure, no
bug tracker, no process. A "Known issues" heading in `status.md` is enough.

Worth noting: every real bug so far — the dead Finish button, "mark known" eating
learning words, levels rising five times too fast — was found by using the app, not by
the 121 tests. That ratio is the argument for this step.

**One dependency.** The alpha is throttled by paste-only import. Less reading means
fewer findings and a weaker answer to the question above. The boring unblock is URL
import: `trafilatura` fetches an article, hands the text to the importer that already
exists. ~30 lines, one endpoint, no new concepts. Worth doing *before* the alpha rather
than after.

## 2. Hosting it properly

**Boring version:** a €4 box, `uv sync`, one systemd unit, Caddy in front. Deploy is
`git pull && systemctl restart`, which is what `CLAUDE.md` already says it should be.

Not Docker — it inserts an image build between pull and run, on a small box, for spaCy
and torch, and the Dockerfile here is still unverified. The files stay in the repo for
whenever a container is genuinely wanted; they are not the recommended path.

**The part that actually matters is backups.** The lexicon cannot be reconstructed and
a disk is a single point of failure. Boring answer: cron `scripts/backup.sh`, copy the
result off the box. Not a backup product.

If a managed platform is preferred instead, the one thing that must not be forgotten is
a **persistent volume** — without it a deploy silently destroys the database.

## 3. Multi-user

**Boring version: don't.** One instance per person — a systemd template unit, separate
data directories, Caddy routing by hostname. Zero code, and it keeps the `CLAUDE.md`
line about not hosting other people's text clean, because each person imports their own.

*(An earlier estimate in this project called multi-user "the expensive one". That was
wrong and is corrected here.)* If one instance ever becomes necessary, the boring
version is not accounts and sessions: HTTP basic auth already carries a username, so
add a `user` row per person, map username to `user_id`, and replace the `USER_ID`
constant with a FastAPI dependency. That is 28 lines across 4 files, and every table
that needs `user_id` already has one. No login page, no registration, no password
reset — the browser does that. Still not worth it below about five people.

## 4. Multi-language

**Boring version: mostly already done.** `lang` is a column on `lesson` and part of
every lexicon key, adapters are found by module name, and `config` already takes a list
of languages. What is missing is one dropdown — the frontend hardcodes the language in
a single line — plus the per-language model and dictionary downloads.

For Russian, the boring choice is **spaCy `ru_core_news_md`, not Stanza**: the same
adapter shape, the same download script, no second NLP stack. Stanza's morphology is
better, but if Russian proves as weak as French tense did, the answer is rules in
`ru.py` the way `fr.py` has them — a pattern that already exists and took 8/16 to 14/16.

Two dull details that will otherwise bite:

- `frontend/src/morph.ts` has no `Case`, `Aspect` or `Animacy`. Russian is mostly case;
  without them the panel would show almost no grammar. Ten lines.
- Each model is 200–500MB resident. Loading is already lazy; keep
  `LL_TEXTREADER_LANGUAGES` short.

## 5. Audio

Two different features hide under this word, and they are not the same size.

**Boring version, and the one to do first: `window.speechSynthesis`.** No model, no
server, no install, no download; macOS ships good French voices. Bind it to the `Space`
already reserved in 0004 and speak the current sentence. Roughly 20 lines. It answers
"how does this sound", which is most of what a reader wants.

The other feature — a podcast or audiobook with the text aligned to it — needs Whisper
with `word_timestamps`, an audio store, a player, and seek-on-sentence-click. Worth
doing only if the free version proves the appetite.

## Proposed order

1. URL import, so the alpha is real reading
2. `speechSynthesis`, because it is twenty lines and belongs in the alpha
3. **Alpha** — read for a fortnight, fix what annoys
4. Host properly, one instance per person, backups off the box
5. Russian, only if the loop proved itself
6. Multi-user, only when running several instances becomes annoying
