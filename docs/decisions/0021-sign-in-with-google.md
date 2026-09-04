# 0021 — Sign in with Google

**Status: decided, being built.** Supersedes 0013's recommendation of passwords with
email reset. 0013's *order* survives intact — export and deletion first, the `USER_ID`
removal early, open signup and recovery late — and everything it says about what
ownership means is unchanged. What changes is who issues the identity.

## Four corrections, made while building it

Written the same day, beside the original rather than instead of it. Each made the
thing smaller, and each came from the maintainer rather than from the code.

- **No invites. Open signup, capped at a hundred accounts.** The plan below has a
  whole phase for an invite table, a minting command and a landing page. A number in
  `config.py` does the same job — bound how many strangers can arrive — in one line,
  and `CLAUDE.md` is explicit that a table nobody needs yet is the wrong change. Raise
  the cap when it binds. Phase 6 is deleted, not deferred.
- **No adoption of existing users.** An earlier draft had an "adopting invite" that
  bound a Google identity to a row that already existed, so a pre-accounts database
  would not be orphaned. Cut: the only database that needs it is the maintainer's own,
  once, and a hand-written `UPDATE` run knowingly is safer than a feature that can
  hand one person's whole lexicon to whoever opens a link. **Consequence to remember:
  the existing user 1 on the box has no `google_sub` and nobody can sign in as it.
  That reading is safe but unreachable until the link is made by hand.**
- **One shared database, not one per account.** Considered seriously, and rejected as
  the *less* lean option despite sounding simpler: per-file means attaching the shared
  dictionary or duplicating 8.9MB per reader, running migrations over N files on every
  deploy, and a multi-file backup — while leaving `user_id` on every table as dead
  weight. `0005` put `user_id` in the schema for exactly this, and that groundwork is
  already paid for. Isolation is bought instead with the enumerated test in phase 3.
- **New accounts choose their language and are given starter lessons in it.** Nobody
  should meet an empty library. The texts are original prose in `starters/` — an
  excerpt would break `CLAUDE.md` and `NOTICE` both — and the second French one
  deliberately reuses the first's vocabulary in unmet shapes, so it opens already
  half-legible. That is the lemma-keyed model arguing for itself on a page nobody
  has touched.

## The decision

Google is the only way in. No passwords, no password reset, no outbound mail. Signup
is open to anyone with a Google account until the cap is reached. *(This paragraph
originally said invite-first; see the corrections above.)*

Three things this buys, in the order they matter:

1. **It deletes the expensive third of 0013.** Recovery was a day of work plus a mail
   provider plus deliverability as a permanent support cost. Delegating identity
   deletes that section rather than solving it.
2. **It routes around a wall we do not control.** netcup applies a default policy that
   drops outbound traffic on 25, 465 and 587 — so password reset by email is blocked at
   the provider before any of our decisions apply. Google needs no outbound mail.
3. **A verified email address arrives free.** 0013 wanted an address collected at signup
   and unused, so that reset could be added later without asking every existing account
   for one. Google hands us a verified address as part of the identity. The column 0013
   asked for gets filled in properly rather than hopefully.

What it costs, unchanged from 0013 and still true: anyone without a Google account, or
who loses theirs, is locked out with nothing this project can do. The answer is the same
one 0013 gives — export and deletion make losing an account survivable — which is why
they are built first rather than last.

## Correction: the 100-user cap is a Testing-mode trap, not a plan

An earlier version of this plan proposed staying under Google's 100-user cap so that
verification could be skipped. That misread how the two states work, and building on it
would have hurt.

There are two publishing states, and they differ in more than a headcount:

| | **Testing** | **In production** |
|---|---|---|
| who can sign in | up to 100 users, each added by email in the console by hand | anyone with a Google account |
| consent lifetime | **expires 7 days after it is given** | does not expire |
| verification | not required | **not required for our scopes** |

The cap is real but it is not the thing that would have bitten. **In Testing, a user's
authorization expires seven days after they grant it** — every reader would be signed
out and re-consenting weekly, in a reading app they open daily. Adding each person's
address to a Google Cloud console by hand is the smaller half of the problem.

And the reason to accept that never existed: **verification is not required for the
scopes we use.** We ask for `openid`, `email` and `profile` — Google classes these as
non-sensitive, and an app using only non-sensitive scopes may publish to production
without review. Verification buys one thing we do not need yet: showing an app name and
logo on the consent screen, through a lighter-weight brand review that can happen any
time later.

**So: press "Publish app" and go to production on day one.** No cap, no weekly
re-consent, no verification queue. Testing mode is for the few minutes before the first
real sign-in works.

The consequence for the roadmap is that Google's limits stop being a reason to keep the
beta small. Something else has to bound it, since the box's capacity is real even when
Google's is not — and that is `max_users`, plus the per-account limits in `limits.py`.

Sources checked September 2026: [when verification is not
needed](https://support.google.com/cloud/answer/13464323),
[managing app audience](https://support.google.com/cloud/answer/15549945).

### Correction, 3 September: stay in Testing, and the seven days barely matter here

The paragraph above is reversed, on the maintainer's decision, and the reasoning that
made publishing look urgent was **wrong for this application specifically**.

"Consent expires after seven days" means the *OAuth grant* expires — which matters
enormously to an app holding a refresh token so it can call Google's APIs on your
behalf while you are away. That app really would break weekly.

**We hold no refresh token.** `google.py` asks for no `access_type=offline`, stores no
refresh token, and never calls Google again after the one code exchange at sign-in. It
reads the ID token's claims, and from then on the reader is carried by *our* session
cookie, which lasts `session_days` — ninety of them. Google's grant expiring changes
nothing about a signed-in reader.

What the seven days actually cost: somebody who signs in again more than a week after
they last consented sees the consent screen one extra time. One click, on a re-login.
That is the whole of it.

So Testing is the better state for now, and not merely an acceptable one:

- **It is the access-control mechanism**, for free. Only addresses on the test-user
  list can sign in at all, so the list *is* the invite system that the corrections at
  the top of this file deleted — without a table, a token or a landing page.
- **It keeps the instance non-public**, which is what the legal reasoning in
  `status.md` turns on: the Impressum duty bites on a service offered to the public,
  and a hand-kept list of people is not that. Publishing would create the postal-address
  problem that staying in Testing avoids entirely.
- **The logo can be uploaded after all.** Google requires verification for a logo
  *unless* the status is Testing. That was the reason to leave branding blank; it no
  longer applies.

The cost is the 100-place ceiling and adding each address by hand, both of which are
fine at this size, and neither of which is permanent — publishing later is one button
and the corrections above still describe what happens when it is pressed.

**The test-user list stays in the Google console and must not be mirrored into this
repo.** The repo is public: a file of testers' email addresses would publish the
addresses of people who agreed to try a reading app, which is precisely the exposure
the Google Group exists to avoid.

## The flow, and the crypto we do not write

Authorization code flow, exchanged server-side. The browser never handles a token.

```
/api/auth/google/start     -> redirect to Google, with state + PKCE challenge
/api/auth/google/callback  -> code arrives; we POST it to Google's token endpoint
                              over TLS, read the claims, set our own session cookie
```

**We do not verify the ID token's signature, and that is correct rather than lazy.**
Signature verification exists for tokens that reach you through the browser, where
anyone could have written them. Ours comes back in the body of a TLS response from
`oauth2.googleapis.com`, to a request we made, authenticated with our client secret —
the channel is the proof. Google documents this exemption. What we do check is `aud`
against our client id, so a token minted for a different app cannot be replayed at us.

That removes a JWT library, a JWKS cache, and a whole class of key-rotation bugs. If
this ever needs to work offline from Google, local verification is the swap.

**The identity key is `sub`, never the email address.** Google's `sub` is stable for the
life of the account; an address can be changed by its owner and reassigned within a
Workspace domain. Keying on email means someone else's new address can inherit a
lexicon. Email is stored for display and for a possible future fallback, and is never
looked up.

`state` is a random value in a short-lived cookie, checked on return — without it a
third party can hand a reader a callback URL and land them in the wrong account.

## Schema

0013's tables, plus what Google needs. `user` gains four columns and `session` is new.
No `invite` table — see the corrections above.

Note on the ALTER below: SQLite **cannot** add a `UNIQUE` column to a table that
already exists, so `google_sub` is added plain and a unique index does that job. It is
created in `db.py` after the columns rather than in `schema.sql`, which runs first
against a table that may not have them yet. The index permits many NULLs, which is
what an un-linked legacy row needs.

```sql
ALTER TABLE user ADD COLUMN google_sub TEXT;         -- the identity. never email.
ALTER TABLE user ADD COLUMN lang       TEXT;         -- chosen at sign-up
ALTER TABLE user ADD COLUMN email      TEXT;         -- display, and a future fallback
ALTER TABLE user ADD COLUMN picture    TEXT;

CREATE TABLE session (
    token      TEXT PRIMARY KEY,        -- secrets.token_urlsafe(32)
    user_id    INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    seen_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

```

Server-side sessions rather than a signed stateless cookie, for 0013's reason: it makes
logout and revocation real rather than decorative. `seen_at` is touched on use and
sessions unused for 90 days are swept, so a forgotten tab on a borrowed laptop expires
on its own.

Cookie: `HttpOnly; Secure; SameSite=Lax; Path=/`. `Lax` rather than `Strict` because the
Google callback is a cross-site navigation back into the app, and `Strict` would drop the
cookie exactly there.

## The order of work

Eight phases. Each is a commit that leaves the app working, and the risky one is third
and isolated on purpose.

### 1 — Survivability first (0013's step 1, unchanged)

Worth having whether or not accounts ever ship, and it makes every later phase less
frightening.

- `GET /api/export` — a zip: every lesson as `.txt`, plus the lexicon as JSON.
  `export.py` already produces the lexicon half.
- `DELETE /api/account` — deletes a user and everything of theirs.

**Deletion is explicit `DELETE` statements in one transaction, not a schema rebuild.**
The lexicon tables reference `user(id)` without `ON DELETE CASCADE`, and SQLite cannot
add a constraint to an existing table — it means rebuilding twelve tables to change one
word each. Twelve explicit deletes in a transaction are boring, readable, and provable
by a test that creates a user, fills it, deletes it, and counts rows in every table.

### 2 — The user table becomes real

`google_sub`, `email`, `picture` added through `db.py`'s `ADDED_COLUMNS`, which already
does exactly this job idempotently. No behaviour change; nothing reads them yet.

### 3 — Multi-tenancy, with no login anywhere near it

**The dangerous phase, and it must not be entangled with OAuth.** `USER_ID` is read at
41 sites across five modules — 21 in `lessons.py`, 12 in `terms.py`, 3 each in
`vocab.py` and `reports.py`, 2 in `db.py`. Missing one means a reader seeing another
reader's vocabulary.

- **Delete the constant.** 0013 is right and it is the whole safety story: a fallback
  would let a missed site silently serve user 1's words, where deletion makes it fail to
  import. A compile-time guarantee beats a code review, and `lessons.py:169` — where the
  arguments are built as `(USER_ID, lang) * 3` — is exactly the kind of site a reviewer's
  eye slides over.
- A `current_user` FastAPI dependency, whose implementation in this phase is a **stub**
  returning user 1. The dependency is the real mechanism; only what is behind it is
  temporary.
- Thread `user.id` through all 41 sites.
- **The isolation test enumerates routes from `app.routes` rather than listing them.**
  Two accounts, every user-scoped route, each asserting it sees only its own. Derived
  from the router, a route added next year without isolation fails this test; hand-listed,
  it silently would not.

Fourteen of the sixteen routes are user-scoped. `GET /api/dictionary` and `GET
/api/health` are not — the dictionary is shared data, and the test's allowlist of
exemptions is two entries long and should stay that way.

Checked rather than assumed: **`lesson.n_new/n_learning/n_known` need no change.**
`data-model.md` warns they are only safe because a lesson belongs to exactly one user.
That stays true — each reader imports their own — so `counts.py` is untouched.

### 4 — Sessions and the door

`session` table, cookie, `require_user` replacing the stub, and a real logout.

**The shared password is retired here, not kept as an outer gate.** Two auth systems is
the bloat `CLAUDE.md` warns about, and sign-in is already the thing deciding who gets
in. This has one consequence to handle rather than discover: `scripts/serve.sh --share`
refuses to start without a password today. It should refuse to start unless *Google is
configured* instead — a public tunnel nobody can sign in to reads as a broken app
rather than a closed one.

### 5 — Google

Start, callback, `state`, PKCE, the `aud` check, first sign-in creating a user against
the cap. Config: `LL_TEXTREADER_GOOGLE_CLIENT_ID`, `..._SECRET`, `..._REDIRECT_URI`.

### 6 — ~~Invites~~ — cut, see the corrections above

Replaced by `LL_TEXTREADER_MAX_USERS`. `LL_TEXTREADER_SIGNUP` survives with two
values, `open` and `off`, because closing the door without locking out the people
already inside is a real thing to want.

### 7 — The front end

There is no concept of a signed-out reader today: `api.ts`'s `call()` throws the body of
any non-2xx as an error string, so a 401 currently surfaces as a stray message. It needs
to mean "show the sign-in screen". Plus the screen itself, an account menu with sign
out, export and delete, and the invite landing page.

### 8 — Close what accounts open

- **DNS rebinding on URL import.** `0019` says plainly that this moves from acceptable
  to must-fix on the day accounts land, because the set of people who can make the
  server fetch things stops being a set you chose. Not optional, and not in 0013's
  costing. Pin the resolved address and carry the hostname separately.
- **Rate limits** on the callback and the invite endpoint. A per-IP counter in SQLite.
- **Quotas.** A lesson is 53.5 kB and unbounded is still unbounded.
- **A terms page and a way to receive a takedown**, before anyone but invitees arrives.

## What a session cannot do, and you must

Four things need a human at a keyboard. Phases 1–4 and most of 6–7 do not wait on them;
phase 5 does.

1. **Create the Google Cloud project and OAuth client**, set the redirect URI to
   `https://<host>/api/auth/google/callback`, and **press "Publish app"** so the project
   is In production rather than Testing. Then put the client id and secret in the box's
   `.env`.
2. **Decide about a domain.** Not needed for TLS any more (0020) and not needed for the
   consent screen to function. It is needed if the consent screen should say something
   better than a bare netcup hostname, and for any future non-Google fallback. Five euros,
   still worth it, no longer blocking.
3. **Harden SSH.** The box advertises `publickey,password`, so the root password netcup
   emailed in plaintext is a live door and it is not known whether it was ever rotated.
   `deploying.md` has the two lines. It stays a human's job because getting it wrong
   locks you out and it wants a second terminal open — and it becomes materially more
   urgent the moment the box holds someone else's reading.
4. **Decide what happens to the demo content.** Four French texts and a lexicon of about
   170 words currently belong to user 1 on the box. Once user 1 is a real account —
   probably yours — that reading history is mixed into it. Either give the demo its own
   account, or clear it before the first invite goes out.

## Out of scope, deliberately

- **A second sign-in method.** 0013 notes that "later" tends to mean never, and that is
  a fair warning. It stays out anyway: one method that works beats two half-built, and
  export is what makes the risk survivable.
- **Sharing anything between accounts.** `CLAUDE.md` rules out a shared lesson library
  for copyright reasons. Accounts do not change that line and must not be read as
  softening it.
- **Everything phase 8 does not name.** Analytics, roles, admin screens, teams.
