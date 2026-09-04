# Status & roadmap

**New session? Run `./scripts/check.sh`, then read this file.**

Current state and what's next. Design lives in `../CLAUDE.md`, the data model in
`data-model.md`, and the reasoning behind individual decisions in `decisions/`. Those
change on a decision; this file changes on an event. Don't copy one into the other.

## Session note — 4 September (Sonnet, part-done, needs review)

**The next session that is Opus should check briefly that this work was done
thoroughly and properly** — done under a tight token budget.

The maintainer's instruction this session: the online box should teach **French,
Russian and Italian** — nothing else (not Dutch). Make the server operational
with all three; the sign-in hand-off tasks are on hold (see below).

### Done — Russian and Italian, built and verified locally

- `nlp/languages/_spacy.py` — a minimal shared spaCy adapter (analyse loop,
  offsets, sentence ids, POS-`X` and PRON→surface fallback). `fr.py` does **not**
  use it: French keeps its tense rules and report fixes. Second/third callers:
- `nlp/languages/ru.py`, `nlp/languages/it.py` — 12-line subclasses, model as it
  comes, no hand rules yet.
- `scripts/setup-models.sh` gained an `it` case (`it_core_news_md`); ru was there.
- `scripts/setup-dictionary.sh` gained `it) name="Italian"`.
- `translate.py` `MODELS` gained `("ru","en")` and `("it","en")` —
  `Helsinki-NLP/opus-mt-{ru,it}-en`, both verified to exist on Hugging Face.
- Frontend: `App.tsx` now has a language picker (fr/ru/it) in the header,
  remembered in `localStorage`, that sets the import language, filters the
  library, and drives the vocab page. `Reader.tsx` dropped its `lang` prop and
  follows the open lesson's own language.
- Tests: `backend/tests/test_languages.py` (adapter wiring + a model-gated
  analyse check). 188 backend / 25 frontend green, ruff + tsc clean.
- **Verified in a browser locally**: imported Russian prose, read it fully
  coloured, `читает → читать` VERB with morphology attached, page segmentation
  correct. Glosses show "no dictionary entry" locally because the ru/it kaikki
  extracts are not loaded on this laptop (they go on the box — see below).

### Deployed to the box, 4 September

`main` at `62d7a2e` is live. `/api/health` reports `["fr","ru","it"]`. On the box:

- all three spaCy models installed (`fr/ru/it_core_news_md@3.8.0`);
  `deploy.sh` now re-fetches all three after `uv sync` prunes them. **Any bare
  `uv run` on the box re-syncs and re-prunes ru/it** — use `uv run --no-sync`
  or `UV_NO_SYNC=1` for one-off commands there. The systemd unit runs
  `.venv/bin/uvicorn` directly, so restarts are safe.
- `hint` table: fr 126,214 / it 207,759 / ru 89,823 glosses (kaikki, loaded on
  the box, raw files deleted). `книга → "book"`, `libro → "book; …"` verified.
- `LL_TEXTREADER_LANGUAGES=fr,ru,it` appended to `/opt/ll-textreader/.env`.
- Verified through the box API: Russian import (`Дети → ребёнок`, `читает →
  читать`) and Italian import (`bambini → bambino`, `leggere`), both then
  deleted — no test data left, library is the 5 French demo lessons.
- RAM after loading all three pipelines in testing: ~1.4 GB used, ~2.5 GB
  available. Headroom is fine for reading; a loaded translator adds ~1 GB, so
  0012's RAM caution still stands if several translators wake at once.

### Not done in this session

- **SSH hardening** — handed back to the maintainer (see below). Key access for
  `llt` and `root` is confirmed working, so `PasswordAuthentication no` will not
  lock anyone out, but this is a security-setting change and stays a human job
  per `deploying.md`.
- **Measure Russian and Italian morphology** before trusting it (0012 step 3).
  Not started. Known model quirks already seen: Italian `giocavano →
  "giocavare"` (should be `giocare`) and fused-preposition lemmas like `nel →
  "in il"`; Russian looked clean on a handful of sentences but that is not a
  measurement. Same class of issue as French `marchions → "marchion"` — the
  defence is noticing and pressing `o`.
  See also the open question at the bottom of this file. `morph.ts` still names
  grammar in French and lacks Case/Aspect/Animacy (0012 step 4).
- **Verify ru/it translation** end to end (first call downloads ~300MB each).
  `translate.py` has the model entries; nothing has exercised them.

### Hand-off tasks 1–4 (Google sign-in) — blocked, code not in repo

The sign-in tasks presuppose a Google OAuth flow, a sessions/cookie layer, a
`user.email`/`google_sub` column, a `starters/` directory, and a starter-lesson
import path. **None exist on `main`:** `user` is still `(id, name, created_at)`,
`main.py` auth is the one shared HTTP-basic password, there is no `starters/`.
`decisions/0013` still describes the password/invite design with Google sign-in
marked "not yet a decision" (item 5 below). The two cloud sessions' output is not
on any pushed branch and not stashed. Before tasks 1–4 proceed, the maintainer
needs to say where that work lives, or a decision file for Google sign-in needs
writing and the feature building.

### SSH hardening — for the maintainer to run

Still `publickey,password` on the box, `/etc/ssh/sshd_config.d/` empty, the
plaintext-emailed root password still a live door. Key access for both `llt` and
`root` is confirmed working from this laptop, so closing password auth will not
lock you out. Left for a human because it is a security-setting change and wants
a second terminal open (per `deploying.md`). In one terminal, staying logged in:

```
ssh -i ~/.ssh/ll_textreader_deploy root@159.195.244.92
printf 'PermitRootLogin prohibit-password\nPasswordAuthentication no\nKbdInteractiveAuthentication no\n' > /etc/ssh/sshd_config.d/harden.conf
sshd -t && systemctl restart ssh
```

Then, from a *second* terminal, confirm `ssh -i ~/.ssh/ll_textreader_deploy
llt@159.195.244.92` still works before closing the first.

### Confirmed infrastructure

- **SSH to the box works**: `ssh -i ~/.ssh/ll_textreader_deploy -o IdentitiesOnly=yes
  llt@159.195.244.92` (and `root@` with the same key). The `--disabled-password`
  diagnosis here is right; `-i` is the way in. `deploy.sh` is
  `ssh -i ~/.ssh/ll_textreader_deploy llt@159.195.244.92 '/opt/ll-textreader/scripts/deploy.sh'`.
- Both `claude/*` remote branches are **already merged into `main`**
  (`git log main..origin/<branch>` empty on both) — "merge the branch" is done.
- The laptop now carries `ru_core_news_md` and some HF cache from this session's
  aborted downloads. **These, and all other local models/dictionaries, are to be
  deleted once the project is fully server-based** — the maintainer asked to be
  reminded and to have removal confirmed, so a later session must raise it.

## Where things stand

**Readable, keyboard-first, with definitions.** Paste French text, read it coloured by
what you know, Tab between unknown words, and the page decolourises as you go.

Working and verified against real text, in the browser:
- French pipeline: spaCy `fr_core_news_md`, POS-tagged lemmas, run at import
- plain-text import (paste or `.txt`), pages, saved position, "mark page known"
- all five render states, including known-lemma-novel-form
- a legend page explaining them, reachable from the library and the palette
- Wiktionary glosses: 126k senses for French, from a kaikki.org extract
- morphology: "conditional · 1st person singular", with rules that stay quiet
  rather than guess (see below)
- sentence translation, off by default, per page on demand
- a legend page explaining the colours and keys
- lexicon export: Anki TSV, CSV, JSON — all, one bucket, or a ticked selection
- collections, a legend, light/dark, sorting and search in the library
- the library listing is O(lessons), not O(every word you ever imported): 1.8ms,
  and 0.7ms at five hundred lessons (`counts.py`, `decisions/0016`)
- lemma override, in the UI and honoured by the read path
- vocabulary page: every lemma, with the inflections you have actually met
- library shows each text's shape — what share of it you can already read
- keyboard: Tab/Shift-Tab (new words *and* the ones at level 4), 1, k, i,
  Shift-K, j/arrows, Enter, Esc, o, /
- levels counted from exposure, not self-rated (decision 0008)
- undo for "mark page known"
- the sentence you first met a word in, kept and shown
- `--dry-run`-able reprocessing for stale token streams (rule 6)
- 207 tests, ruff and tsc clean

Numbers worth knowing: a 12,000-word chapter imports in 1.3s. Opening a page costs
more the longer the lesson is, because the page boundaries are re-derived from every
token each time: 5ms on a 2,000-word article, 10ms at 20,000, 31ms on a 100,000-word
book. The dictionary is a 573MB download that leaves 12MB in the database.

Russian and Italian: adapters, model/dictionary scripts, translation entries and
a front-end language picker landed 4 September and work locally; not yet deployed
to the box, and Russian morphology is not yet measured (see the session note up
top and open questions below).

Not built: audio, EPUB import, sync, anything on a phone.

### Four rules the pilot decided by hand

- **Confidence.** spaCy gives no per-token score, so the only honest signal is the
  tagger admitting defeat: POS `X` falls back to the surface form (rule 7). The
  fallback happens in the adapter; there is no confidence column any more, because
  nothing ever read it.
- **When a form counts as met.** Not on page open — that would erase the novel-form
  highlight before you'd read the word. Recorded when you act on a word, and in bulk
  when you turn the page, for every word you have judged rather than only the known
  ones. Words you have *not* judged are still left out, for the reason above.
- **What "the rest" means.** "Mark page known" takes the blue words only. A word you
  set to learning stays learning.
- **Verb tense.** `fr_core_news_md` scores 8/16 on tense and mood and never produces a
  conditional. French endings are uniform across verbs, and future/conditional stems
  always end in `-r`, so a form can be classified against its own lemma with certainty
  (`nlp/languages/fr.py`). Where the rules are silent and the tagger is not
  trustworthy, no tense is shown at all: 14 correct, 0 wrong, 4 silent.

### Pages

~150 tokens, packed greedily and broken between sentences. **Derived at read time, not
stored**, and position is a token index, so changing the page size reflows a book
without losing anyone's place. Position never moves backwards.

## Next

1. **It is live, with two things left undone on purpose.** The box serves the
   reader at `https://v2202609408983511171.ultrasrv.de` — netcup Vienna, Debian
   13, app under systemd on `127.0.0.1:8000`, Caddy in front, database in
   `/var/lib/ll-textreader/`. Deploys are
   `ssh llt@159.195.244.92 '/opt/ll-textreader/scripts/deploy.sh'`.

   Verified on 2 September, through the public URL and not just on the box:
   401 without the password and 200 with it, the frontend and the font served,
   an import running spaCy on the box (`dort` → `dormir`, morphology attached),
   `porte` → "door" out of the 126,214 glosses, and a delete putting the library
   back to empty.

   Getting there took two corrections to what this file claimed:

   - **The first provisioning run had not finished.** It died at the dictionary
     step, because the probe asking whether the glosses were loaded ran as root
     and *created* the database before the loader could — leaving a root-owned
     empty file the loader could not write. Everything after that step never
     ran, so the box was answering with Caddy's stock welcome page on 80 and
     nothing at all on 443. Fixed: the probe is `sqlite3 -readonly`, and the
     state directory is chowned back to `llt` on every run, so re-running the
     provisioner repairs a box in that state.
   - **The certificate is real, and took three attempts to get right.** Let's
     Encrypt refused at first — the 50-a-week limit counts per *registered
     domain*, and every netcup customer on `ultrasrv.de` shares it. Calling
     that permanent and settling for `tls internal` was wrong: renewals are
     exempt from that limit, so the name only had to win a slot once.
     Configured to keep asking — `acme` then `internal`, with a one-hour
     stand-in so Caddy retries every forty minutes — it won on the first retry,
     18:58 UTC on 2 September. `curl` validates the full chain with no
     `-k` and no warning. `decisions/0020` carries the reasoning and the
     correction. A domain of your own is still worth five euros for the
     password-reset email `0013` needs, but it is no longer needed for TLS.

   **There is demo content on the box**, so a visitor sees the product rather
   than an empty library: four short French texts written for the purpose (not
   excerpts — the repo ships no third-party text), three of them in a collection
   called "Une semaine à Lyon". They were read through the real endpoints, not
   seeded into the database: one completed, two part-read, one never opened, and
   twelve words left in learning. The point is the fourth text — never opened,
   and already 66% readable, with `reviendront`, `sait`, `assis` and `arrivé`
   showing as novel forms of lemmas the first three taught. That is the whole
   argument for the lemma-keyed model, visible on a page nobody has touched.
   It is demo data in a real lexicon: if the box becomes the maintainer's own
   reader, this is the thing to clear first.

   Left undone, deliberately, both decided on 2 September:

   - **Backups still have nowhere to go — and this is a launch blocker.** The
     timer runs daily and `backup.sh` works, but `LL_TEXTREADER_BACKUP_TO` is
     unset, so every copy lands on the same disk as the database, which
     `decisions/0006` is blunt about not being a backup. Left running that way
     on 3 September with the risk understood, because a same-disk copy is still
     worth having: it does not survive a dead disk, but it does survive a bad
     migration or a page marked known by mistake, which are likelier. What it
     must not do is survive until launch. **Before anyone but the maintainer
     has a lexicon on this box, an off-machine destination is required** — an
     hour's work, and the only loss here that cannot be undone.
   - **SSH still accepts passwords** — the box advertises `publickey,password`,
     so the root password netcup emailed in plaintext is still a live door, and
     it is not known whether it was ever rotated. `deploying.md` has the
     two-line hardening; it stays a human's job because getting it wrong locks
     you out, and it wants a second terminal open.

2. **The bug reports.** Seventeen filed from real use. Fourteen are now closed
   (`./scripts/reports.sh`); **10, 11 and 17 are the ones still open.** Until
   2 September the `done` column had never been set on anything, so if it looks
   untouched again, suspect that before suspecting the list. What each one was:

   - **#1 title as vocabulary — already fixed.** `with_title()` puts the title in
     the body, so it is tokenised like everything else.
   - **#2 and #3 novel form shown as plain learning — already fixed.**
     `state_for()` returns `novel-form` before it splits learning from known, so
     marking `perçu` leaves `perçoit` dashed. This is the rule `CLAUDE.md` calls
     the point of the design, and it now matches.
   - **#5 legend words look clickable — fixed 2 September.** The legend shows real
     `.tok` spans so it cannot drift from the reader, and `.tok` carries
     `cursor: pointer`. Scoped it away in the legend rather than dropping the
     shared class.
   - **#6 Tab should reach every coloured word — fixed 2 September**, reversing
     `0004`. See the caveat under Russian below.
   - **#7 hover shows the shortcut — fixed 2 September**, `title` on each button.
   - **#8 the button row jumped — fixed 2 September.** The actions are their own
     flex row now, so they hold position whatever the title does.
   - **#9 notes did not save — fixed 2 September**, and it was two bugs. The note
     was only written as a side effect of rating a word, and it was never read
     back, so even a saved note looked lost. Tokens now carry `status` and `note`,
     the box opens with what you wrote, and clicking away saves it without
     touching the level.
   - **#4 dictionary covers the text — was already fixed**, and I nearly fixed
     it twice: `main.with-panel` already reserves `45vh + 3rem` under the page.
     Check before adding a second mechanism.
   - **#12 does "mark page known" swallow the dashed forms of a word you are
     learning? No** — asked, checked, and now pinned by a test. The sweep is
     decided on the lemma's status (`NULL`, 0 or 4), so a lemma at 1-3 is
     excluded whatever shape of it happens to be on the page.
   - **#13 reports had no page number — fixed 2 September.** The column always
     existed; `App.tsx` never passed it. The reader now reports its page up.
   - **#14 `Tenez` not matched to `tenir` — fixed 2 September**, on the second
     try. It was capitalisation: capitalised at the start of a sentence, spaCy
     called it PROPN. Such an opener now gets read again on its own and the
     second reading is taken *only* if it comes back a verb, so `Marc descend…`
     and `Paris est…` keep their proper nouns. The first attempt tested the
     first *token* of the sentence and so missed the actual report, because the
     line was `— Tenez, voilà Karim.` and French dialogue opens on an em dash —
     which is precisely where imperatives live. It now tests the first *word*.
     Still missed: `« Regardez ! »`, where the tag is NOUN rather than PROPN.
     Widening the rule to NOUN would misread a sentence opening on a real noun
     (`Porte fermée.` → `porter`), so that one stays a job for the override.
   - **#15 `Elle` → `lui` — fixed 2 September**, and it was worse than reported:
     `lui` itself came back as `luire`, the verb, while still tagged PRON. UD has
     reasons for collapsing third-person pronouns; a learner does not care about
     them. Pronouns are closed-class, so the form is now the lemma.
   - **#16 tense names in French — done, minus the switch.** `morph.ts` has a
     table per locale and `LOCALE = 'fr'`; the settings screen that flips it
     comes with the Russian and Italian work (`0012`).
   - **#17 the first translation took ~20s — still open**, deliberately. It is
     the model loading on first use, and all that changed is that the app now
     says so instead of sitting silent. That makes the wait explicable, not
     shorter, so the report stays open: the real fix is warming the translator
     at startup, which costs a slow boot and a 300MB download on a box that may
     never translate anything.
   - **#10 and #11 — open**, on the timeline below. Both want a decision file
     before any code.

   **#14 and #15 change stored token streams**, so the pipeline stamp went from
   `+tense1` to `+rules2` and every lesson needed reprocessing (rule 6). One cost
   worth knowing: pronoun entries keyed on the old lemmas no longer match, so a
   few very common words — `elle`, `celle` — come back blue once. The lexicon
   also still holds `celer` and `luire` tagged PRON, which is what the old
   lemmatiser left behind.
   The one that outranks everything after it: #2 and #3 both say a known
   lemma's unmet form renders as plain yellow learning. That is the novel-form
   state, the one distinction the schema exists for, and Russian is the
   language that stresses it hardest — shipping Russian on top of it means
   debugging both at once. Also core: #4, the dictionary covering text with no
   way to scroll, and #9, notes that do not save.

   Two are ideas rather than bugs, and both are on the timeline rather than in
   this list. Neither has a decision file yet and neither should be started
   without one:

   **#10 multi-word units.** "du coup" means something "coup" does not, so a
   phrase needs to be one clickable, markable unit. The maintainer expects this
   to be hard and is right — it touches the token stream, the key on every
   lexicon table, and rendering. Their own suggested way in, which is a good
   one because it needs no phrase dictionary: **let the reader select several
   words in the text**, and on a button or after a second's pause, treat the
   selection as one thing — translate it, or check it against known phrases.
   That turns an unbounded NLP problem into a UI gesture, and the manual case
   is the one that always works.

   **#11 LLM-generated lessons.** Generate text at a level, in a style, on a
   topic — the way these demo texts were written — and later reuse the words
   you have learned in new contexts, which the maintainer describes as "a true
   SRS within context". The open questions are theirs and are the real content
   of the decision: bring-your-own API token, or connect your own model? Are
   locally run models good enough? Is there a lean version? Or is this better
   left to people themselves, outside the app? Worth noting against `0015`,
   which already argued about what this project should and should not host.

3. **Russian and Italian** — `decisions/0012`. **The reading path is built**
   (4 September, see the session note up top): adapters, model/dictionary
   scripts, translation entries, a header language picker that filters the
   library. What is left of this item:
   - deploy it to the box and load the ru/it models and dictionaries there;
   - **measure Russian morphology before trusting it**, the way French was
     measured — the step not to skip, still not done;
   - `morph.ts` still names grammar in French and has no Case/Aspect/Animacy, so
     Russian words show a thin or French-worded description;
   - the German interface and a switchable translation target are untouched —
     the UI still has no i18n. Interface language and translation target are two
     settings, not one (a German speaker reading French may want English glosses).

   One thing to re-examine here rather than assume: Tab now stops on novel forms
   (report #6). `0004` originally refused to, predicting that in a heavily
   inflected language it would make Tab useless. Nobody has tested that, and
   Russian is the test.

   One thing to re-examine here rather than assume: Tab now stops on novel forms
   (report #6). `0004` originally refused to, predicting that in a heavily
   inflected language it would make Tab useless. Nobody has tested that, and
   Russian is the test.

4. **A phone edition** — at least decent compatibility, because several people
   the maintainer knows would use it mainly there. Not planned in detail yet,
   and it collides with something real: this reader is keyboard-first by
   decision (`0004`), and Tab, `1`, `k`, `i` and the rest have no touch
   equivalent. So "responsive CSS" is not the whole job — the interaction model
   needs an answer for a device with no keyboard, and that answer deserves its
   own decision file before anyone starts.

5. **Accounts** — `decisions/0013`, updated 2 September. Leaning to Sign in
   with Google rather than passwords, to avoid storing passwords and building
   reset. Invite-first still holds; invites are about who gets in, which is a
   different question from how they prove who they are.

6. **Export the lessons, and account deletion** — `decisions/0013`. Moved to
   the back of the queue on 2 September. An afternoon each, and still what
   "your data is yours" actually means, but no longer blocking anything.

Alongside all of it: read with the thing. Every real bug so far came from using it, not
from the tests — the Finish button that did nothing, "mark known" eating learning
words, levels rising five times too fast. That is still the highest-yield activity
available.

## Planned in detail, not started

- **German interface, switchable translation target** — `decisions/0012`. The
  Russian/Italian reading path is built (item 3 above); what remains here is UI
  localisation and letting the reader pick an interface language and a
  translation target separately.
- **Multi-user** — `decisions/0013`. The document still recommends an instance per
  reader until that becomes the annoying part; the maintainer's current leaning is
  Sign in with Google, which is item 5 above and not yet a decision.
- **Local-first** — `decisions/0014`. A direction rather than a plan, plus the four small
  things worth preserving now so it stays possible. `decisions/0015` answers a
  zero-cost-hosting proposal and names the fork it implies: going fully static means
  giving up the POS tagger, which is the thing this project exists to have.

## Waiting, deliberately

**Audio**, and that is now the whole list. Russian, a phone client and multi-user
were all held back here so the desktop reader could get good first; as of
2 September all three are in the plan above instead. The line that stays true is
why they waited: nothing here was blocked, and the reader got better for having
had the attention.

## Testing

207 tests: 184 backend (pytest), 23 frontend (vitest). `npm test` in `frontend/`.
Seven of the backend ones need the real French model and skip without it, so
`./scripts/setup-models.sh fr` is part of running the suite, not just the app.

The frontend tests cover `reading.ts` and `morph.ts` — pure functions, no DOM and no
component framework, deliberately. What they pin is the logic that is easy to get
subtly wrong: that laying spans over the text loses no character of it, that Tab
wraps and then stops, and that `Imp` is imperfect under Tense and imperative under
Mood. React rendering is still only checked by driving a browser.

`test_counts.py` earns its place separately: the library's per-lesson counts are cached,
and it compares the stored numbers against counting from scratch after every operation
that could move a word between buckets. A drifted count is worse than a slow one.

## Known, not urgent

Written down so the next session doesn't rediscover them and think they are news.

- **Page open is linear in the length of the lesson.** `_pages()` groups a lesson's
  whole token stream by sentence on every read, every page turn and every
  translation request — the numbers above. A covering index halved it and the shape
  is unchanged. The fix, when it is worth doing, is the same one decision 0016 used
  for the library: derive the boundaries once and keep them, invalidated by
  `pipeline_id`. Not now: 31ms is not felt, and it only bites on whole books.
- **DNS rebinding on URL import.** `decisions/0019` says why it is left open and
  what changes that: accounts.
- **URL import introduces itself honestly**, as `Mozilla/5.0 (compatible;
  LL_textreader)`, and some sites answer a non-browser agent with a 403. If a paper
  you want to read refuses, that is the first thing to check — `UA` in
  `importers/from_url.py`. Left honest on purpose; pretending to be Chrome is a
  decision about how this thing behaves on the web, not a bug fix.
- **`ago()` is written twice**, in `Vocab.tsx` and `LessonList.tsx`, with different
  wording on purpose. Both had the same timestamp-parsing bug. A third copy means
  it is time to merge them.

## Open questions

- Levantine Arabic: MSA-trained analysers mis-handle بدي / عم بكتب / مش. Not a pilot
  problem — see `decisions/0002-arabic-pipeline.md`.
- Does "turn the page" remain the right moment to record met forms, under real use?
- **How often is the lemmatiser simply wrong, and does `o` cover it?** Spot-checking
  `fr_core_news_md` in September 2026: `chanterait` is correctly a conditional, but
  `chantera` came back tagged feminine singular and `marchions` was lemmatised to
  `marchion`. The tense rules are measured (14 right, 0 wrong, 4 silent); the
  lemmatiser underneath them is not. It matters because a wrong lemma is a wrong
  *entry in your lexicon*, not just a wrong colour, and the only defence is noticing
  it and pressing `o`. Worth counting against a page of real prose before Russian,
  where the same question will be sharper.
