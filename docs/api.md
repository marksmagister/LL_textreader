# The API

Twenty-five endpoints. Everything the frontend does goes through one of them, and
FastAPI serves the live schema at `/docs` if you'd rather read it there.

**Every route below needs a session except three**, and the three are listed first:
`/api/health`, `/api/dictionary` and the sign-in flow. Everything else answers 401
without one. That list is enforced by a test that reads the routes off the app's own
schema, so a new endpoint is guarded unless it is deliberately added to the exemptions
(`test_auth.py`).

| | | |
|---|---|---|
| `GET` | `/api/health` | version and configured languages — **open** |
| `GET` | `/api/auth/me` | who is signed in, or `null`; also whether signup is open |
| `GET` | `/api/auth/google/start` | begin sign-in; `?lang=` is what they will learn |
| `GET` | `/api/auth/google/callback` | Google returns here; sets the session cookie |
| `POST` | `/api/auth/logout` | delete the session, server-side |
| `GET` | `/api/account/export` | a zip: every text you imported, plus the lexicon as JSON |
| `DELETE` | `/api/account` | delete the account and every row belonging to it |
| `POST` | `/api/lessons/fetch` | read a web page and hand back its text — imports nothing |
| `POST` | `/api/lessons` | import plain text — **tokenises and lemmatises here, once** |
| `GET` | `/api/lessons` | the library, with per-lesson counts by state; `?lang=` narrows it |
| `GET` | `/api/lessons/starters` | the texts a language starts with, and whether you have them |
| `POST` | `/api/lessons/starters` | put the ones you don't have in the library |
| `GET` | `/api/lessons/{id}` | one page, resuming where you stopped unless `?page=` says otherwise |
| `DELETE` | `/api/lessons/{id}` | delete a lesson and its tokens |
| `PUT` | `/api/lessons/{id}/collection` | put it in a collection by name; empty takes it out |
| `POST` | `/api/lessons/{id}/finish` | turn a page: record met forms, raise levels, save position, optionally clear the blue |
| `POST` | `/api/lessons/undo/{undo_id}` | put back what a bulk action changed |
| `GET` | `/api/lessons/{id}/translation` | English per sentence for a page; translates and caches on first ask |
| `PUT` | `/api/terms` | set one word's status — where clicking a blue word lands |
| `PUT` | `/api/terms/override` | detach a surface form from the lemma the pipeline gave it |
| `DELETE` | `/api/terms/override` | undo that; the pipeline's answer applies again |
| `GET` | `/api/dictionary` | Wiktionary senses for a lemma, matching part of speech first |
| `GET` | `/api/vocab` | the lexicon, with counts by bucket and the forms you have met |
| `GET` | `/api/vocab/export` | download it: `format=anki\|csv\|json`, narrowed by `status`, `q` or `keys` |
| `POST` | `/api/reports` | a reader says something is wrong |

## Things that are easy to get wrong

- **Reading a lesson is a join and nothing else.** All the analysis happened at
  import. If you find yourself calling the NLP pipeline in a GET, stop.
- **Token offsets are absolute** into `lesson.body`, but `GET /api/lessons/{id}`
  returns only one page's slice of that body plus `body_offset`. The frontend
  subtracts. Don't rebuild text from tokens; slice the body.
- **`undo_id` is only set** on a response to `finish` with `mark_rest_known`, and
  only when something actually changed.
- **Every route carries a user, and there is no default.** `USER_ID` is gone from
  `db.py` (0022). Routes take `user: User = CurrentUser` and pass `user.id` into the
  query; a route that forgets fails to import rather than serving user 1's words.
- **Asking for someone else's lesson is a 404, not a 403.** Whether a lesson exists is
  itself somebody else's business.
- **The door is Google, and the shared password is gone.** There is no basic auth and
  no `LL_TEXTREADER_PASSWORD`.
- **Expensive actions are rate-limited per account, per hour** — import, URL fetch,
  translation, reports, term updates, page turns — and an account holds at most 500
  lessons. `limits.py` has the numbers and the reasoning. Over the line is a 429.
- **The starter routes are declared before `/{lesson_id}`.** Routes match in
  declaration order and "starters" is not an integer, so the other way round
  `GET /api/lessons/starters` is a 422 rather than a listing.
- **The language menu is built from the server, not the bundle.** `/api/auth/me`
  carries `languages` (and `/api/health` reports the same list), so what you can
  read is a fact about which models the server has.
- **`POST /api/lessons/fetch` makes the server fetch a URL**, so it validates the
  address *and every redirect it leads to* — see `decisions/0019`. Anything that
  changes that path needs to keep the redirect guard.
