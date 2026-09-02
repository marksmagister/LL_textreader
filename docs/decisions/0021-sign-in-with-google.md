# 0021 — Sign in with Google

**Status: decided, being built.** Supersedes 0013's recommendation of passwords with
email reset. 0013's *order* survives intact — export and deletion first, the `USER_ID`
removal early, open signup and recovery late — and everything it says about what
ownership means is unchanged. What changes is who issues the identity.

## The decision

Google is the only way in. No passwords, no password reset, no outbound mail.
Invite-first: an account is created by following an invite link and signing in with
Google, and the invite is what decides who gets in.

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
beta small. Invites stay, because *we* want to choose who gets in while the box has no
quotas and no terms page — not because Google is counting.

Sources checked September 2026: [when verification is not
needed](https://support.google.com/cloud/answer/13464323),
[managing app audience](https://support.google.com/cloud/answer/15549945).

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

0013's tables, plus what Google needs. `user` gains three columns; `session` and
`invite` are new.

```sql
ALTER TABLE user ADD COLUMN google_sub TEXT UNIQUE;  -- the identity. never email.
ALTER TABLE user ADD COLUMN email      TEXT;         -- display, and a future fallback
ALTER TABLE user ADD COLUMN picture    TEXT;

CREATE TABLE session (
    token      TEXT PRIMARY KEY,        -- secrets.token_urlsafe(32)
    user_id    INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    seen_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE invite (
    token      TEXT PRIMARY KEY,
    note       TEXT,                    -- who it was for
    used_by    INTEGER REFERENCES user(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
the bloat `CLAUDE.md` warns about, and the invite is already the thing deciding who gets
in. This has one consequence to handle rather than discover: `scripts/serve.sh --share`
refuses to start without a password today. It should refuse to start unless signup is
invite-only instead — the tunnel stays as safe as it was, guarded by the thing that now
does the guarding.

### 5 — Google

Start, callback, `state`, PKCE, the `aud` check, first sign-in creating a user against
an invite. Config: `LL_TEXTREADER_GOOGLE_CLIENT_ID`, `..._SECRET`, `..._REDIRECT_URI`.

### 6 — Invites

The table, a command that mints one and prints the link, and `LL_TEXTREADER_SIGNUP`
taking `invite` (the default), `open` or `off`. Open signup is then the flag 0013
promised, not a rewrite.

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
