# Status & roadmap

**New session? Run `./scripts/check.sh`, then read this file.**

Current state and what's next. Design lives in `../CLAUDE.md`, the data model in
`data-model.md`, and the reasoning behind individual decisions in `decisions/`. Those
change on a decision; this file changes on an event. Don't copy one into the other.

## Where things stand

**Readable, keyboard-first, with definitions.** Paste French, Russian or Italian text,
read it coloured by what you know, Tab between unknown words, and the page
decolourises as you go.

**Live, with accounts, at `https://v2202609408983511171.ultrasrv.de`.** Sign in
with Google is the only door (`decisions/0022`); each reader gets starter texts
in the language they choose, and their own library, lexicon and rate limits.

Working and verified against real text, in the browser:
- French pipeline: spaCy `fr_core_news_md`, POS-tagged lemmas, run at import
- Russian and Italian pipelines, measured before they were trusted (`decisions/0021`)
- a language dropdown in the header, in two groups — the ones you are learning,
  then everything else the server can read — curated in settings; it filters the
  library, and the reader takes its language from the lesson, not from the control
- three starter texts per language — French, Russian and Italian — written for
  the purpose, in a collection, one press to add
- the interface is English or German; English is the default and stays it, and
  German is chosen in settings, never guessed from the browser
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
- 319 tests (284 backend, 35 frontend), ruff and tsc clean

Numbers worth knowing: a 12,000-word chapter imports in 1.3s. Opening a page costs
more the longer the lesson is, because the page boundaries are re-derived from every
token each time: 5ms on a 2,000-word article, 10ms at 20,000, 31ms on a 100,000-word
book. The dictionary is a 573MB download that leaves 12MB in the database.

All three languages have their Wiktionary glosses on the box (fr 126,214,
it 207,759, ru 89,823) and translate to English, verified 4 September.

Not built: audio, EPUB import, sync, a phone *edition* — the reader no longer
breaks on a phone, but Tab, `1`, `k` and `i` still have no touch equivalent.
Translation only targets English.

### Five rules the pilot decided by hand

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
- **What a language adapter may correct.** Only what is certain from the form or
  from a closed class — Russian gets three rules on that basis, Italian none,
  because its faults need a lexicon rather than a rule (`decisions/0021`).

### Pages

~150 tokens, packed greedily and broken between sentences. **Derived at read time, not
stored**, and position is a token index, so changing the page size reflows a book
without losing anyone's place. Position never moves backwards.

## 4 September: the hand-off was done, and the two branches joined

Everything the cloud sessions could not reach is done. Written up here rather
than deleted, because the *why* is the part that would be expensive to rederive.

### Both branches are merged into `main`

There were two, built in parallel against the same `main`, and both had real
work in them:

- `claude/multi-language-support-d7mu26` — Russian and Italian measured, i18n,
  a settings screen, starter texts per language.
- `accounts` — Sign in with Google, sessions, per-account rate limits, legal
  pages, account export and deletion.

**A warning worth keeping.** A session earlier the same day concluded the
sign-in work "does not exist in the repo" and wrote that into this file. It was
wrong: it ran `git branch -a`, which lists *stale remote-tracking refs*, and
never ran `git fetch`. Both branches had been on the remote the whole time. It
then rebuilt Russian and Italian from scratch, worse — a naive pass-through of
whatever spaCy said, against a branch that had measured the models and written
three rules from the results. That work is deleted, not kept beside the better
version. **Fetch before concluding anything is missing.**

Conflicts that were real, and how they were settled:

- `api/lessons.py` — accounts removed `USER_ID` for `user: User = CurrentUser`;
  multi-language added `?lang=` filtering and the starter routes. Both kept.
- `starters.py` — both branches wrote one. Merged to a single implementation:
  the multi-language layout (`<lang>/<collection>/NN-*.txt`, all three
  languages) with the accounts sign-up entry point. `install` raises so the
  button can report a missing model; `give_starters` swallows, because a missing
  model must not cost somebody their account.
- **Both branches numbered their decision 0021**, which `CLAUDE.md` warns about
  by name. Languages kept 0021; sign-in became **0022**, references repointed.
- A merge silently reverted `b7c1da6` — the `PATH` line `deploy.sh` needs to
  find `uv`. Nothing conflicted, so nothing warned. It is commented now, having
  been lost twice.

### Live on the box

`https://v2202609408983511171.ultrasrv.de`, three languages, French, Russian and
Italian, all reading with glosses.

- spaCy `fr`/`ru`/`it_core_news_md`, and `deploy.sh` re-fetches all three because
  `uv sync` prunes them. **Any bare `uv run` on the box re-prunes them** — use
  `uv run --no-sync`. The systemd unit runs `.venv/bin/uvicorn` directly, so
  restarts are safe.
- Glosses: fr 126,214 / it 207,759 / ru 89,823.
- All 48 language-measurement tests pass against the real models on the box.
  Spot-checked on unseen prose: `живёт → жить` and `пьёт → пить` (the ё rule),
  `Меня → я` and `ей → она` (oblique pronouns), `Person=3` normalised,
  `Дети → ребёнок`. The three rules in `ru.py` fire on text they were not
  tuned on.
- **Translation works for all three pairs, run for the first time.**
  `opus-mt-{fr,ru,it}-en` all resolve on Hugging Face — that settles the caveat
  the branch added when it had no network to check. "Она живёт в Москве и пьёт
  чай." → "She lives in Moscow and drinks tea."
- The ~1.6GB of translation weights are now in the box's Hugging Face cache, so
  **report #17's wait is now model load rather than model download**. The report
  stays open: warming at startup is still the real fix.

### SSH is hardened

Done, not handed back. `/etc/ssh/sshd_config.d/harden.conf` sets
`PermitRootLogin prohibit-password`, `PasswordAuthentication no` and
`KbdInteractiveAuthentication no`. Key logins for `llt` and `root` were proven
working *before* the change, `sshd -t` validated the config before the restart,
and both were re-proven on fresh connections after; a password attempt now gets
`Permission denied (publickey)`. The root password netcup emailed in plaintext is
no longer a door.

### The maintainer's own reading is on the box

`scripts/import-lexicon.py` moved it: 15 lessons, 542 words, 682 met forms, 4
lemma overrides, 17 reports, 10,308 tokens. The four demo texts that were there
to show a visitor the product are gone — replaced, which is what `Next` item 1
said to do the moment the box became the maintainer's own reader.

It moves **rows, not identity**. Binding a Google account to that data is still
the separate hand-written `UPDATE` that `0022` argued for.

### Phone: not an edition, but no longer broken

`decisions/0004` makes this reader keyboard-first, and Tab, `1`, `k` and `i`
have no touch equivalent — a real phone edition still needs its own decision
(`Next` item 4). What was fixed is the part that was simply broken, found by
driving it at 375px:

- the per-lesson actions are `opacity: 0` until `:hover`, and **a phone never
  hovers** — delete and collection were invisible and untappable;
- the two floating tabs sat on top of the word panel's buttons;
- `.bar-actions` could not wrap, pushing "Next page" off a screen that does not
  scroll sideways;
- buttons were three different heights, because long labels wrapped inside them.

The theme switch and "something's wrong" now live in the account menu, at the
maintainer's suggestion — which deletes two fixed elements and a z-index layer
rather than hiding them. **Tapping away is what Esc is on a device with no Esc**,
so it closes the word panel and the account menu as it already did the palette.

### Signed in, and the account is joined to the reading — 5 September

Done, and the thing works end to end. The secret went in, the sign-in round trip
completed, and the account now owns the months of French.

**What signing in looked like, which is worth knowing because it alarms people.**
Google issued a `google_sub` nothing matched, so the app did the correct thing
and made a *new* reader: user 2, three starter texts, an empty lexicon. The 542
words were not lost, they were on user 1, which had no way to be signed in as.
That gap is what `0022` accepted when it cut adoption, and it is closed by hand,
once, knowingly.

**The join moved the identity, not the reading.** One row changes instead of
nine tables, and nothing large is copied:

```sql
BEGIN IMMEDIATE;
-- google_sub is uniquely indexed, so the new row has to let go before the old
-- one can take it. Same transaction, so there is no moment where nobody holds it.
CREATE TEMP TABLE ident AS SELECT google_sub, email, picture, name FROM user WHERE id = 2;
UPDATE user SET google_sub = NULL WHERE id = 2;
UPDATE user SET google_sub = (SELECT google_sub FROM ident),
                email      = (SELECT email      FROM ident),
                picture    = (SELECT picture    FROM ident),
                name       = (SELECT name       FROM ident)
 WHERE id = 1;
-- then carry across everything the new row had acquired, session included, and
-- drop it. UPDATE ... SET user_id = 1 on every table that has a user_id.
DELETE FROM user WHERE id = 2;
COMMIT;
```

Two details that made it painless and would not have been obvious:

- **The live session was carried across too** (`UPDATE session SET user_id = 1`),
  so the browser that was signed in stayed signed in. Deleting the new user
  instead would have forced a second sign-in for no reason.
- **The three starter lessons were carried across rather than deleted.** They are
  ordinary lessons and can be removed in the UI; reassigning is the less
  destructive of two one-line choices.

Checked afterwards: no orphaned rows in any of the eleven tables carrying a
`user_id`, `PRAGMA foreign_key_check` clean, and the cached per-lesson counts
recomputed, because three lessons had arrived from another owner.

**If this ever has to be done again** — a second machine, a re-imported laptop —
the shape is: `scripts/import-lexicon.py` to move rows between databases, then
this transaction to move an identity onto them. They are deliberately separate.

### Where it stands now

One user, `bisinger.noah@gmail.com`, signed in, owning 21 lessons (18 French,
3 Italian) and 696 lexicon entries — 543 French known, 70 learning, and 63
Italian known inside the first day. Which is the answer to the open question
0012 raised: a second language got read, not just built.

## Hand-off, 5 September

The box is the reader now, and it works. What is left, most urgent first.

### 1. The backups are the one real risk, and they got riskier

`LL_TEXTREADER_BACKUP_TO` is still unset, so `backup.sh` writes beside the
database and `decisions/0006` is blunt about that not being a backup. This was
already the launch blocker. It is worse now for a reason that is easy to miss:
**the box holds reading that exists nowhere else.** Until 4 September the laptop
had a full copy, so a dead disk cost a day. Since then the Italian has been read,
the French has moved on, and none of that is anywhere but `/var/lib/ll-textreader`.

`backup.sh` already does the work — one `rsync` to whatever
`LL_TEXTREADER_BACKUP_TO` names. What it needs is a destination, and that is a
choice rather than a task:

- another host over ssh (`user@host:/path`) — needs a key on the box;
- object storage with an rclone or s3 remote — needs a credential in `.env`;
- **a pull from the laptop instead**, which needs nothing new: the laptop already
  has the key, and `rsync` from the box on a schedule inverts the direction so no
  inbound access to the laptop is required. Probably the cheapest correct answer.

An hour, and it is the only loss here that cannot be undone.

### 2. Read with it, in Russian

Sixty-three Italian words in the first day is the first real evidence a second
language gets *used*. Russian has the models, the glosses and the starters and
has still not been read. It is also the open question `0004` raised and nobody
has answered: Tab now stops on novel forms, and a Russian starter page shows
sixteen at once, which is the density the original argument was about. Reading
one page settles it either way.

### 3. Three reports still open

`./scripts/reports.sh`. #10 multi-word units and #11 LLM-generated lessons both
want a decision file before any code. #17 improved sideways rather than being
fixed: the translation weights are now cached on the box, so the wait is model
*load* and not a 300MB *download*. Warming at startup is still the real fix.

### 4. Smaller, and none of them blocking

- **`morph.ts` was extended for Russian** (Case, Aspect, Animacy) and names
  grammar in the language you are reading. Italian has not been looked at with
  the same eye; it may be fine, but "may be fine" is what was said about Russian
  before it was measured.
- **The German interface and a switchable translation target** — `0012`. The
  interface strings exist in both languages; the translation target is still
  English only, and the two are deliberately separate settings.
- **A phone edition** is still its own decision (`Next` item 4). What was fixed
  on 4 September is that it is no longer *broken* on a phone — not that the
  keyboard-first interaction model has a touch answer.
- **The laptop still holds ~1.7GB of Hugging Face weights, two spaCy models and
  a 14MB database.** The maintainer asked to be reminded to delete these once the
  server is the only thing that matters, and to have the removal confirmed rather
  than assumed. That moment has essentially arrived — but see item 1 first, since
  the laptop's copy is currently the only off-box copy that exists.

## Next

1. **It is live, with two things left undone on purpose.** The box serves the
   reader at `https://v2202609408983511171.ultrasrv.de` — netcup Vienna, Debian
   13, app under systemd on `127.0.0.1:8000`, Caddy in front, database in
   `/var/lib/ll-textreader/`. Deploys are
   `ssh llt@159.195.244.92 '/opt/ll-textreader/scripts/deploy.sh'`.

   Verified on 2 September, through the public URL and not just on the box —
   under the shared password, which has since been retired for accounts:
   401 without it and 200 with it, the frontend and the font served,
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

   ~~**There is demo content on the box**~~ — **gone, 4 September.** Four short
   French texts stood in the library so a visitor saw the product rather than an
   empty page. The box is now the maintainer's own reader, which is exactly the
   condition this file said to clear them under, and their place is taken by the
   15 lessons and 542 words carried over from the laptop. New accounts meet the
   starter texts in `starters/` instead, which is the same job done properly.

   Left undone:

   - **Backups still have nowhere to go.** The timer runs daily and `backup.sh`
     works, but `LL_TEXTREADER_BACKUP_TO` is unset, so every copy lands on the
     same disk as the database, which `decisions/0006` is blunt about not being
     a backup. Skipped for now with the risk understood: one disk failure takes
     the lexicon, and the lexicon is the months of reading that cannot be
     regenerated. Setting it is an hour whenever it stops being acceptable.
   - ~~**SSH still accepts passwords**~~ — **hardened 4 September.** The box now
     offers `publickey` only; the plaintext-emailed root password is dead. See
     the September 4 section above for how it was done safely.

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

3. **Russian and Italian — done, and what is left of it.** `decisions/0021` has
   the measurements and the four surprises. Both languages read, the interface is
   English or German, and every language ships three starter texts. Left over,
   all small and all named at the end of 0021:

   - **The dictionaries.** `./scripts/setup-dictionary.sh ru` and `it` — ~940MB
     and ~500MB to download, leaving ~15MB each. Until then a Russian word gives
     grammar and a note field but no gloss.
   - **German as a translation target.** One `MODELS` entry per pair, plus
     somewhere to choose it. Not done because the network it was built on could
     not reach Hugging Face to confirm the model names.
   - **`ru→en` and `it→en` are added but unrun**, for the same reason. If a name
     is wrong the symptom is a download error on the first press of the button.

   The thing to actually watch, and the reason to read with it rather than reason
   about it: **Tab now stops on novel forms** (report #6). `0004` originally
   refused to, predicting that in a heavily inflected language that would make Tab
   useless — and 0021 measured 19 unmet shapes in a 126-word Russian text against
   4 in an Italian one, which is exactly the density `0004` was worried about.
   Nobody has read a long Russian text this way yet. That is the test.

4. **A phone edition** — at least decent compatibility, because several people
   the maintainer knows would use it mainly there. Not planned in detail yet,
   and it collides with something real: this reader is keyboard-first by
   decision (`0004`), and Tab, `1`, `k`, `i` and the rest have no touch
   equivalent. So "responsive CSS" is not the whole job — the interaction model
   needs an answer for a device with no keyboard, and that answer deserves its
   own decision file before anyone starts.

5. **Accounts — built on the `accounts` branch, 3 September. Not merged, not
   deployed.** Sign in with Google, open signup capped at 100, no passwords and
   no invites. `decisions/0021` carries the decision and four corrections made
   while building it. The suite is 235 backend + 25 frontend, all passing;
   `ruff` and `tsc` clean.

   What works, verified by running it rather than only by tests: the app boots,
   `/api/auth/me` answers `null` before sign-in, every reader route answers 401
   without a session, `/privacy` and `/terms` serve, and the sign-in screen
   renders in both themes.

   - **`USER_ID` is gone from all 41 call sites.** Deleted rather than
     defaulted, so a route that forgets fails to import. Two tests guard it:
     one enumerates every route from the app's own OpenAPI schema and asserts a
     stranger gets 401 — so a route added later without a user fails the day it
     is written — and one drives two accounts through the same database checking
     neither can see, open, delete, finish, undo or export the other's work.
   - **Limits on everything exploitable**, per account per hour: import 40,
     URL fetch 30, translate 60, reports 20, term updates 3000, page turns 600;
     plus 500 lessons and 2M characters an account. `limits.py`.
   - **The DNS-rebinding hole is closed**, which `0019` said would become
     must-fix the day accounts arrived — and open signup made it worse than
     `0019` anticipated. There is now one DNS lookup instead of two, done by the
     connection itself, and TLS still verifies against the name.
   - **Privacy policy and terms** at `/privacy` and `/terms`, readable without
     signing in. Honest about what is stored, and the contact is the Google
     Group rather than anyone's inbox.

     **Done, 3 September.** The operator is Noah Bisinger, the contact is the
     group address, and there is no postal address — the pages carry a standing
     note that this instance is not open to the public and has had no legal
     review, rather than a "draft" banner. The test that asserted the pages
     still said `[OPERATOR NAME]` has been flipped: it now asserts no bracketed
     placeholder can ever reach a reader again.

     The Google project stays in *Testing* status, so only addresses on its
     test-user list can sign in. That is both the access control and the reason
     the postal address is not needed: the GDPR wants the controller's identity
     and a way to reach them (Art. 13), which a name and an address satisfy; the
     *postal* line comes from the Impressum duty, which bites on a service
     offered to the public, and a hand-kept list of people is not that.

     **If this is ever opened up, do not use the maintainer's work address.**
     It was offered and is the wrong instrument: it belongs to an employer who
     has not agreed to appear as the contact for a personal project, legal post
     about it would arrive in a company post room, and it stops being an address
     where anyone can be reached the day the job changes. A rented service
     address is five to fifteen euros a month and is the thing actually designed
     for this. Not legal advice.

   - **The sign-in flow is verified as far as it can be without a browser.**
     `/api/auth/google/start` redirects to the right endpoint with the right
     client id, `openid email profile`, S256 PKCE and a 32-character state in an
     `HttpOnly` ten-minute cookie. The callback rejects a missing state cookie
     and a mismatched state (both land on `?error=expired`, no session created),
     and reports a cancelled consent as `?error=cancelled`. The exchange itself
     reaches Google: with a deliberately wrong secret it comes back
     `401 invalid_client`, which proves the client id is real, egress works and
     Google's own message survives to the log. **What is still unproven is one
     real sign-in** — a valid code, a session cookie, a user row. That needs a
     browser and an address on the test-user list.
   - **New accounts pick a language and get starter lessons** — two original
     French texts in `starters/fr/`, the second reusing the first's vocabulary
     in unmet shapes.

   Three things it did not do, all of them now settled — see the 5 September
   section above for how, and keep them in mind when a *second* reader arrives:

   - ~~**Nobody can sign in as the existing user 1.**~~ **Joined by hand,
     5 September.** Adoption stays cut, and that is still right: a feature that
     hands one person's lexicon to whoever opens a link is worse than one
     `UPDATE` run knowingly. The `UPDATE` is written out above so the next one
     is not rederived.
   - ~~**Google is wired but not yet proven end to end.**~~ **Proven
     5 September**: real Google account, real consent, session cookie, user row,
     starter texts. The client secret lives only in `/opt/ll-textreader/.env`.
   - ~~**Nothing is deployed.**~~ **Deployed 4 September.** Both branches are
     merged and the box runs the merged build; the shared password is gone with
     `0022`, so Google is genuinely the only door now.

6. **Export the lessons, and account deletion** — `decisions/0013`. No longer
   at the back of the queue: they are phase 1 of the accounts work, because
   `0013` is right that they are what makes losing an account survivable, and
   because Google sign-in has no recovery story of its own.

Alongside all of it: read with the thing. Every real bug so far came from using it, not
from the tests — the Finish button that did nothing, "mark known" eating learning
words, levels rising five times too fast. That is still the highest-yield activity
available.

## Planned in detail, not started

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

319 tests: 284 backend (pytest), 35 frontend (vitest). `npm test` in `frontend/`.
Some backend tests need a real spaCy model and skip without it, so
`./scripts/setup-models.sh` — no argument, meaning every configured language — is
part of running the suite, not just the app.

`test_russian.py` and `test_italian.py` hold the measurement tables from
`decisions/0021` as **floors**, not exact expectations: the models get a few of
them wrong, and a test that pretended otherwise would be the lie the table exists
to prevent. An upgrade that scores better should raise the floor with it.

The frontend tests cover `reading.ts` and `morph.ts` — pure functions, no DOM and no
component framework, deliberately. What they pin is the logic that is easy to get
subtly wrong: that laying spans over the text loses no character of it, that Tab
wraps and then stops, and that `Imp` is imperfect under Tense and imperative under
Mood. React rendering is still only checked by driving a browser.

`test_counts.py` earns its place separately: the library's per-lesson counts are cached,
and it compares the stored numbers against counting from scratch after every operation
that could move a word between buckets. A drifted count is worse than a slow one.

## Known, not urgent

- **The setup scripts read configuration, so they can now fail in new ways.**
  Two did, and both failed silently — a `sed` on a missing `.env` under
  `set -e` taking a whole script down without printing, and a `sqlite3` probe
  whose absence read as a real answer. Fixed, and written up in `0021` under
  "Two bugs in the setup scripts", because the shape will recur. `_config.sh`
  is the one place that reads `.env` now; keep it that way.

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
- **The three language adapters share a twenty-five-line spaCy walk**, and it is
  not extracted. Deliberate: pulling it out means touching `fr.py`, and any change
  to its `pipeline_id` marks every French lesson on the box stale and forces a
  reprocess. A fourth language, or the next change `fr.py` needs anyway, is when
  to do it (`decisions/0021`).
- **Reading `LL_TEXTREADER_LANGUAGES` out of `.env` is written twice**, in
  `check.sh` and `setup-models.sh`, because neither may source `.env` safely. Same
  rule as `ago()`: a third copy means merge them.
- **Russian and Italian have no glosses until the extracts are downloaded.** The
  word panel looks broken-but-working: grammar, no definition.
- **Italian invents lemmas for some first-person and future forms, and does it
  inconsistently**: `chiamo` is `chiamo` in one sentence and `chare` — not a word
  — in another, so one verb can become two lexicon entries depending on where you
  met it. Measured in `decisions/0021`; the defence is `o`.

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
