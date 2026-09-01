# 0005 — Architecture, clients, and deployment

From a design conversation that predates the repo. Recorded here because it settles
questions the code keeps running into.

## The decision everything else follows from

Lemmatisation needs Python. Reading needs to work on a phone. Those don't fit in one
binary — but they don't have to, because **lemmatisation is import-time only**. Once a
lesson is processed, reading is rendering spans against a status map, which any client
can do.

One Python service does import, tokenisation, lemmatisation and lookup. Thin clients
read pre-processed token streams and mutate statuses. Everything below is consequence.

## Web app, not a native Mac app

A native macOS app means either embedding Python — spaCy models are 50–500MB, and
notarising a Python-bundling app is miserable — or running a local server anyway, at
which point the native shell buys nothing but a second codebase. Web-first gives macOS
and iOS from one implementation. If it should later feel more app-like on the Mac,
wrap the same frontend in Tauri: a few hundred lines, native menu bar, real global
hotkeys, no second UI codebase.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python + FastAPI | spaCy/Stanza are Python; no debate |
| DB | SQLite, WAL | Single user. Postgres is ceremony |
| Frontend | TypeScript + Vite | Small, standard, no build archaeology in two years |
| NLP | spaCy `fr_core_news_md`; Stanza for Russian | Stanza's morphology is better and import is offline anyway |
| Dictionaries | kaikki.org Wiktionary extracts | Offline, no API keys, no rate limits, no vendor |
| Network | Tailscale | See below |
| Deploy | Docker Compose on a €5 Hetzner box | Always-on, so the phone syncs when the laptop is shut |

**Tailscale is the highest-leverage infrastructure choice here.** The service binds to
the tailnet only. No public exposure, no TLS certs, no login screen, no sessions, no
password reset, no rate limiting, no worrying that your reading history is one CVE from
the open internet. Solid iOS client. It deletes an entire category of work.

## Sync — where projects like this die

Don't build CRDTs. The data is almost monotonic, which is a gift:

- **Status**: merge with `max()`, tiebreak on `updated_at`. Statuses go up; the rare
  downgrade is handled by timestamp and losing one doesn't matter.
- **Notes**: last-write-wins on timestamp.
- **Lessons**: server-authoritative; import only happens online.

Offline on the phone: IndexedDB caches the last N lessons, status changes go to a local
mutation queue, and on reconnect you POST the queue and GET `/sync?since=`. ~150 lines,
correct because the merge function is commutative.

## Rendering

One container of spans with a single delegated click handler — not 2,000 listeners.
Status changes mutate a class name, not DOM structure. Should stay under 16ms.

## Import — friction here kills the habit

Paste text · URL via trafilatura (better than Readability here) · EPUB via ebooklib ·
`.srt`/`.vtt` · YouTube transcripts via yt-dlp. Plus an **iOS Share Sheet shortcut**: a
Shortcuts action that POSTs the current Safari page or selection to `/import` over
Tailscale. Twenty minutes of setup, and anything you meet on your phone lands in the
reader.

## iOS

Install the PWA to the home screen; since iOS 16.4 that gets service workers and decent
offline behaviour. Caveat: Safari evicts storage from sites unused for 7 days, and
installed PWAs are safer but not exempt. Since the server holds truth and the phone only
caches, eviction costs a re-download, not data. Acceptable.

If the PWA disappoints, phase 3 is a SwiftUI reader against the same API — the
token-stream-plus-status-map design makes a native client small, not a rewrite.

## Deliberately out of v1

- **SRS/flashcards.** Re-encounter in context is the mechanism; flashcards double scope.
- **Shared/crowdsourced definitions.** Single user. Kaikki plus your own notes is enough.
- **Multi-user auth.** Tailscale is the auth.
- **Statistics dashboards.** One number — known lemmas — is enough, and it is more
  motivating when it isn't gamified.

Build the import pipeline and the reader. If the Tab-and-rate loop feels good after a
week of real reading, everything else is optional.

## Where the built code differs, and why

- **Schema keys carry `user_id`.** The doc's schema is single-user. Ours has `user_id`
  everywhere so dropping that assumption stays cheap; it is always 1 today.
- **`lemma_override` is keyed `(user, lang, surface)`**, not `(lang, surface, pos_hint)`.
  A per-POS override needs a POS the user can see and choose, and the pilot's override
  action is "this word is not that word" — one decision per surface form.
- **Status is set one word at a time**, not batched. The batch endpoint is worth having
  when the phone client and its mutation queue exist; today it would be an untested code
  path with no caller.
- **Pages** are not in the doc but are needed for the pressure valve to be usable on a
  book. See `../data-model.md`.
