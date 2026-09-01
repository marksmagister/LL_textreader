# 0006 — Managing lessons: a watched folder

**Question.** Lessons should be easy to import, export and manage. On a desktop app
they'd be plain text files in a folder. Does that make sense for a web app?

**Yes, and it's the right instinct.** This is a single-instance, single-user, self-hosted
app, so "a folder of text files" is available — it just belongs to the *server*, not to
the browser.

## The split

- **The text belongs in files.** `data/library/*.txt`, one per lesson. Plain, greppable,
  diffable, syncable with git or Dropbox, editable in any editor.
- **The lexicon belongs in SQLite.** `lemma_status` and `form_seen` are relational, hot,
  and read on every page open. They are not documents.

The database keeps the *derived* token stream, which is a cache of the file plus the
pipeline. Files are the source of truth for text; the DB is the source of truth for you.

## What that buys, in one mechanism

- **Import**: drop a file in the folder.
- **Export**: it is already a folder of `.txt`.
- **Edit and re-import**: change the file. The server hashes each file on scan and
  re-tokenises the ones that changed. That is the "fix a bad import from page 3"
  request, for free.
- **Backup**: `cp` the folder.

Paste-and-import stays; it just writes a file too.

## Sketch

```
lesson.source_path  TEXT     -- relative to data/library/, NULL for pasted text
lesson.content_hash TEXT     -- sha256 of the cleaned body
```

Scan on startup and on demand: for each file, hash it; insert if unseen, re-tokenise if
the hash moved, leave alone otherwise. Deleting a file does *not* delete the lesson —
too easy to lose reading history to a stray `rm`; it marks it missing.

## The thing actually worth backing up

Not the lessons — they're replaceable. `lemma_status` and `form_seen` are six months of
reading and cannot be reconstructed. SQLite being one file makes that story short:

```
cp data/ll_textreader.db backup.db
```

A JSON/CSV export of the lexicon is worth adding anyway, so the asset isn't hostage to
one schema version.
