# The API

Fifteen endpoints. Everything the frontend does goes through one of them, and
FastAPI serves the live schema at `/docs` if you'd rather read it there.

| | | |
|---|---|---|
| `GET` | `/api/health` | version and configured languages |
| `POST` | `/api/lessons/fetch` | read a web page and hand back its text — imports nothing |
| `POST` | `/api/lessons` | import plain text — **tokenises and lemmatises here, once** |
| `GET` | `/api/lessons` | the library, with per-lesson counts by state |
| `GET` | `/api/lessons/{id}` | one page, resuming where you stopped unless `?page=` says otherwise |
| `DELETE` | `/api/lessons/{id}` | delete a lesson and its tokens |
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
- **Everything is one user.** `USER_ID = 1` in `db.py`, threaded through 28 call
  sites. The schema is ready for more; the API is not.
- **A password locks all of it**, including `/api/health`, when
  `LL_TEXTREADER_PASSWORD` is set. Empty means no door.
