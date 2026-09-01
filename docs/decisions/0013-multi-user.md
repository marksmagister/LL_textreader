# 0013 — Multi-user

**Status: planned, not built.** With a recommendation to think twice first.

## The argument against doing this

The stated long-term direction is that each reader's storage and compute should be
theirs — local, or at least personal. Multi-user on one server is the opposite of that:
it puts everyone's reading history in one database, which then has to be kept separate
by code that is correct on all 34 call sites, forever.

There is already a way to give a person their own data with **no code at all**: a second
instance. A systemd template unit, a second data directory, a second hostname in Caddy.
Twenty minutes, no auth logic, no isolation bugs possible, and it *is* the local-first
end state — a personal server is local-first in the way that matters, since the data is
not pooled with strangers'.

So: **for two to five readers, run instances.** Build the below when running instances
becomes the annoying part, which is somewhere around five to ten people — and know that
building it makes the local-first direction harder, not easier.

The rest of this is the plan for when that day comes.

## The design

Deliberately not a login page, not sessions, not registration.

**Basic auth already identifies a username.** It is in the header on every request, the
browser stores and re-sends it, and there is no session state to expire, leak or
invalidate. What is missing is only that the username is currently ignored.

```sql
ALTER TABLE user ADD COLUMN password TEXT NOT NULL DEFAULT '';  -- scrypt output
ALTER TABLE user ADD COLUMN name_lower TEXT;                    -- unique, case-folded
```

`hashlib.scrypt` from the standard library. No new dependency, and password hashing is
not somewhere to be clever.

**Users are made by a command**, not a form:

```
uv run python -m ll_textreader.users add ami
uv run python -m ll_textreader.users passwd ami
```

A self-hosted reader for a handful of people does not need a registration flow, and not
having one removes an entire category of abuse.

## The part that must not go wrong

Thirty-four call sites read `USER_ID`. Missing one means one reader seeing another's
vocabulary — the worst failure this application could have.

**Delete the constant.** Do not leave `USER_ID = 1` in `db.py` as a fallback. Replace it
with a dependency:

```python
def current_user(request: Request) -> int: ...   # from the basic-auth header
```

and thread it through as `user: int = Depends(current_user)`. With the constant gone,
any site that was missed **fails to import** rather than silently serving user 1's
words. A compile-time guarantee beats a code review.

Then the test that actually matters: create two users, and for every endpoint that
reads or writes, assert that each sees only their own. Not a spot check — a loop over
the endpoint list, so a new endpoint added later without isolation fails it.

## What stays shared

`hint` and `root_index` are reference data — dictionaries, not history — and have no
`user_id` on purpose. `token` and `sentence_gloss` belong to a lesson, and a lesson
belongs to a user, so they inherit isolation.

One consequence worth accepting: two readers importing the same article each get their
own copy and each translation is computed twice. That is the right trade against a
shared lesson library, which `CLAUDE.md` rules out for copyright reasons.

## Migration

The existing reader becomes user 1 with the password from `LL_TEXTREADER_PASSWORD`. No
data moves. `LL_TEXTREADER_PASSWORD` then only bootstraps the first account.

## Cost

Half a day for the change, and the isolation test is most of it. The risk is not the
writing; it is that a leak is silent and would not be noticed until someone saw a word
they had never met marked as known.
