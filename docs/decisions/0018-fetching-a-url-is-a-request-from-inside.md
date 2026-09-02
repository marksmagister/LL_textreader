# 0018 — Fetching a URL is a request from inside the server

**Status: accepted and implemented.**

URL import means the *server* makes an HTTP request to an address someone typed into
the box. Behind a tunnel or on the netcup box, that is a way to reach everything the
app can reach and the reader cannot: localhost, the private network, and — the one
that actually costs money — the cloud metadata endpoint at 169.254.169.254, which
hands out credentials to anything that asks from the right machine.

`from_url.check()` has always refused those addresses. It was not enough.

## What was wrong

`check()` ran on the address you typed. trafilatura then did the fetching, and
trafilatura follows redirects. So:

```
https://a-page-i-control.example/  ->  302  ->  http://169.254.169.254/latest/meta-data/
```

passed the check, was fetched anyway, and came back as a lesson you could read. The
guard was in the right place and looked at the wrong requests.

## What it does now

The download is ours (`_download`, twenty lines of `urllib.request`) rather than
trafilatura's, for one reason: a redirect handler that calls `check()` on every hop
before following it. trafilatura still does the extraction, which is the part worth
having a library for.

While the fetch was being written by hand anyway, two things it lacked:

- a 20-second timeout, so a slow page cannot hold a worker open,
- a 4MB cap, read as `read(MAX + 1)` — the body lands in memory before anything
  looks at it, and "the article" is never four megabytes.

## The one thing this changes about behaviour

Owning the request means owning how the app introduces itself: `Mozilla/5.0
(compatible; LL_textreader)`. Some sites answer anything that isn't a browser with a
403, so a page that imported before might now refuse. That is the first thing to
check when a URL fails — `UA` in `importers/from_url.py`, one line.

It stays honest rather than pretending to be Chrome. That is a choice about how this
behaves on other people's servers, and it should be made on purpose if it is made.

## What is still open, deliberately

**DNS rebinding.** `check()` resolves the name, then urllib resolves it again to
connect; a domain whose record flips between the two answers gets through. Closing
it properly means pinning the resolved address and carrying the hostname separately,
which fights TLS verification for the rest of the file's life.

It stays open because of who can reach this. There are no accounts: whoever is
importing a URL already has the password, which means they are someone you invited.
A person in that position who wants to read your metadata endpoint has easier
routes than timing a DNS record. Redirects were different — a redirect needs no
cooperation from the person pasting the link, so any page they read could spring it.

If accounts ever arrive (0013), this moves from "acceptable" to "must fix" on the
same day, because the set of people who can make the server fetch things stops being
a set you chose.
