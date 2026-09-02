# 0013 — Accounts

**Status: planned, not built.** Rewritten once the goal changed from "let a friend try
it" to "publish it and let people sign up".

**Update, 2 September 2026 — leaning to Sign in with Google, not passwords.** The
maintainer's reasoning: it removes password storage, password reset, and the email
infrastructure that reset needs. That is real — most of the cost this document
attributes to "get back in" is the cost of *recovery*, and delegating identity
deletes that section rather than solving it. Not yet a decision, so nothing here is
rewritten around it, but three things to check before it becomes one:

- It moves the domain requirement rather than removing it. Google wants an https
  redirect URI, which the netcup hostname satisfies, but a public consent screen
  wants a homepage and a privacy policy on a name you own.
- It makes Google the single point of failure for every account. Anyone without a
  Google account, or who loses theirs, is locked out with nothing this project can do.
  A second method later is the usual answer, and "later" tends to mean never.
- The order in this document does not change. Export and deletion are still what
  makes an account survivable, whoever issues the identity.

The invite-first plan below still holds: invites are about *who gets in*, which is a
separate question from *how they prove who they are*.

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

### Why not just keep basic auth

It is already there and it already identifies a username, so the question is fair. Five
limitations, in the order they would bite:

1. **There is no logout.** Browsers cache basic-auth credentials for the life of the tab
   or longer, and no reliable cross-browser way exists to clear them. On a shared or
   borrowed computer you cannot sign out. For one reader on their own laptop that is
   nothing; for strangers it is the first support question.
2. **The login screen is the browser's**, not yours: a native grey dialog, no branding,
   no error you control, no "forgot password" link, and a bare 401 page if they press
   cancel. It is markedly worse on phones.
3. **It can check credentials but not create them.** Signing up needs a form that works
   *without* auth — so the form gets built anyway, and basic auth's whole advantage
   ("no UI to write") evaporates the moment people can join by themselves.
4. **CSRF.** Browsers attach basic auth to same-origin requests automatically, so a
   cross-site form post rides along with the reader's credentials. A `SameSite=Lax`
   cookie is *safer* here, not less safe.
5. **Rate-limiting a login** is awkward when every request is a login.

Basic auth is right for one to five people you know. It is the wrong shape the moment
someone you have never met can arrive.

**So: sessions.**

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

### What sending email actually involves

Not the sending. The sending is fifteen lines.

```python
def send(to: str, subject: str, body: str) -> None:
    httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.email_key}"},
        json={"from": settings.email_from, "to": to, "subject": subject, "text": body},
    ).raise_for_status()
```

Four things around it are the actual work:

1. **A provider.** Sending straight from the VPS does not work — cloud IP ranges are
   blocklisted by default and nobody accepts mail from an unwarmed one. Resend's free
   tier is 3,000 a month (100/day) and Brevo's is 300/day, either of which is thousands
   of sign-ups. Free is genuinely free at this size.

2. **A domain you own.** This is the one that bites, because SPF and DKIM are DNS
   records on the sending domain — and **a DuckDNS subdomain cannot have them**, since
   the domain is not yours. Email means buying a domain, five to ten euros a year. It
   also gives a URL worth putting in a Reddit post, so it is a purchase with two uses.

3. **The reset flow, which is the real cost.** A `password_reset` table with a
   single-use token and a short expiry, an endpoint to request one that is rate-limited
   and **answers the same whether or not the address exists** — otherwise it is a
   quiet way to enumerate who has an account — an endpoint to consume it, and a form.

4. **Deliverability.** Some will land in spam however correctly it is set up, so
   "I never got the email" becomes a thing you answer. Nothing fixes this; it is a cost
   of the feature.

About a day, most of it in the flow rather than the mail.

### The cheap decision to make now

**Collect an email address at sign-up and do nothing with it.** One nullable column.
It costs nothing today, and it is the difference between adding reset later as a purely
additive feature and having to ask every existing account for an address first.

If accounts are keyed on a username with no address anywhere, password reset is not
merely unbuilt — it is impossible without a migration and a round of emails you have no
way to send.

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

## The way from here to there

Open signup is not the first step, and does not have to be. The path that keeps every
option open:

**1. Invite links, not mailed passwords.** Never send someone a password: it sits in
their inbox for ever, it is reused elsewhere, and you end up knowing it. Instead a
single-use token —

```sql
CREATE TABLE invite (
    token      TEXT PRIMARY KEY,
    note       TEXT,                    -- who it was for
    used_by    INTEGER REFERENCES user(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

— generated by a command, pasted into a reply by hand. The link opens a page where
**they** choose a username and password. You never see it, nothing sensitive is emailed,
and growth is bounded by how many links you hand out.

**2. Open signup is then one flag.** The same page, reached without a token, behind
`LL_TEXTREADER_SIGNUP=open`. An hour's work once the invite flow exists, because it is
the same form and the same endpoint.

This means a beta can start with a form that collects an email address and nothing else
— a list you hold — and every account after that is the same machinery whether it came
from an invite or from the open door.

## Order

1. Export and deletion — worth having whether or not accounts ever happen
2. Users, sessions, and the signup page reached by invite token
3. `USER_ID` removal, isolation test
4. Open signup — a flag
5. Password reset by email
6. Rate limits, quotas, terms

Steps 1 and 3 are the ones that would be painful to retrofit; 4 and 5 can arrive late.
Notably **password reset can wait behind invites**: while the list is small, a lost
password is one command to issue a fresh invite, and that buys a whole day back at the
point where the day is least affordable.
