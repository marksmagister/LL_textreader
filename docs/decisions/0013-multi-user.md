# 0013 — Accounts

**Status: planned, not built.** Rewritten once the goal changed from "let a friend try
it" to "publish it and let people sign up".

## "Ownership" is three things, and only one of them is accounts

The instinct — people should be able to get back into their stuff — is right, but it
bundles three separate problems that have different answers and very different costs:

1. **Get back in.** Recovery. The expensive one.
2. **Take it with you.** Export. Half-built already.
3. **Leave.** Deletion. Not built.

Worth saying plainly: an account on someone else's server is the *weakest* form of
ownership there is. What actually makes reading history yours is that a copy of it sits
on your machine, in a format that outlives this project. That is 2 and 3, not 1.

So the order below builds them in the order of what they are worth, not the order they
are usually built in.

## First: make losing an account survivable

Cheap, and it changes how frightening everything else is.

- **Export the lessons too.** `export.py` covers the lexicon — the irreplaceable part —
  but there is no way to get the texts out. One endpoint returning a zip of `.txt`
  files plus the lexicon JSON is an afternoon.
- **Automatic periodic export.** Drop the JSON into Downloads every so often, with an
  obvious restore. Inelegant; it is also what has saved a lot of Anki users.
- **Account deletion that actually deletes.** Not a flag. `ON DELETE CASCADE` already
  covers the lesson-owned tables; the lexicon tables need the same.

With those, a forgotten password costs you an account and not six months of reading. That
is a better guarantee than any reset flow, because it holds even if this project stops
existing.

## Then: accounts

**Sessions, not basic auth.** 0013's earlier draft leaned on basic auth because the
browser stores the credentials and there is no session state to get wrong. Self-signup
kills that: signing up needs a form, a form needs a login page, and once there is a
login page, basic auth's one advantage — no UI — is gone. It also has no logout worth
the name.

So: a `session` table in SQLite, a random token in an `HttpOnly; Secure; SameSite=Lax`
cookie. Server-side rather than signed-and-stateless, because that makes logout and
revocation real rather than decorative.

```sql
CREATE TABLE session (
    token      TEXT PRIMARY KEY,        -- secrets.token_urlsafe(32)
    user_id    INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    seen_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Passwords with `hashlib.scrypt` from the standard library. Password hashing is not a
place to be clever, and it is not a place to add a dependency either.

## Recovery, and why it is the expensive part

This is the piece that changes the character of the project, because it is the first
thing that needs infrastructure having nothing to do with reading.

| | what it costs | what it gives |
|---|---|---|
| **Email reset** | an email provider, deliverability, reset tokens, rate limits | what everyone expects |
| **Recovery code at signup** | almost nothing | works until they lose the code |
| **OAuth (Google/GitHub)** | an OAuth app; awkward for self-hosters | no passwords at all, recovery is someone else's problem |
| **Nothing, plus export** | nothing | the account is lost, the reading is not |

**Recommendation: email reset, and build the export first anyway.** Free tiers (Resend,
Brevo) cover thousands of sign-ups a month at zero cost, and "forgot password" missing
reads as broken however good the export is. But the export is what actually delivers
the ownership, and it is a tenth of the work.

Self-hosters get `LL_TEXTREADER_SIGNUP=off` and no mail configuration.

## What self-signup adds that a command-line user list did not

Strangers change three things:

- **Rate limits** on signup and login. Not sophisticated — a per-IP counter in SQLite is
  enough to stop the boring attacks.
- **Quotas.** A lesson is 53.5 kB; unbounded is still unbounded. A cap on lessons or
  total words per account, generous enough that nobody real notices.
- **A copyright posture.** `CLAUDE.md` rules out a shared lesson library deliberately:
  hosting other people's copyrighted text is the line. Accounts do not cross it, since
  each person's imports stay theirs — but hosting a thousand strangers' imports is a
  different risk from hosting your own. A terms page and a way to receive a takedown
  should exist before a Reddit post, not after one.

## The part that must not go wrong

Unchanged from the earlier draft, and still the only genuinely dangerous piece.

Thirty-four sites read `USER_ID`. Missing one means a reader seeing another's
vocabulary. **Delete the constant** rather than leaving it as a fallback, so anything
missed fails to import instead of silently serving user 1's words. A compile-time
guarantee beats a code review.

Then a test that creates two accounts and loops over every endpoint asserting each sees
only its own — so an endpoint added later without isolation fails it.

## Honest cost

Not the half-day the earlier draft claimed; that assumed no signup and no recovery.

| | |
|---|---|
| export lessons, auto-export, deletion | ~1 day |
| users, sessions, signup, login, logout | ~1 day |
| password reset by email | ~1 day |
| `USER_ID` removal and the isolation test | ~½ day |

Call it **three to four days**, and note that almost none of it is about reading. That
is the real cost of publishing, and it is worth knowing before starting rather than
halfway through.

## Order

1. Export and deletion — worth having whether or not accounts ever happen
2. Users, sessions, signup
3. `USER_ID` removal, isolation test
4. Password reset
5. Rate limits, quotas, terms

Steps 1 and 3 are the ones that would be painful to retrofit. The rest can arrive late.
