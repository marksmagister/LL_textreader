# 0011 — Organising the library

**Status: built**, as draft 2 with one change — the import field stays visible rather
than folding behind a button, because it is the core of the thing.

Collections landed too: named rather than managed. There is no screen for creating or
editing one; typing the same name on two lessons is how you put them together, and a
collection nobody is in disappears. That keeps the feature to one table, two columns
and one endpoint.

## The problem

The library is a flat list. At ten lessons it already fills the screen; at fifty it
stops being usable. Specifically: nothing is searchable, nothing is sortable, there is
no way to see what you have started or how far in you are, and an EPUB would arrive as
a dozen unrelated chapters with no relation between them.

## The data model, either way

One table and two columns. Deliberately not tags, not folders inside folders.

```sql
CREATE TABLE collection (
    id INTEGER PRIMARY KEY, user_id INTEGER, lang TEXT,
    title TEXT, kind TEXT,            -- 'book' | 'series'
    created_at TEXT
);
ALTER TABLE lesson ADD COLUMN collection_id INTEGER;  -- null: a loose article
ALTER TABLE lesson ADD COLUMN position INTEGER;       -- chapter order
```

A lesson belongs to at most one collection, which is what "a folder" means and what an
EPUB actually is. Tags would be more expressive and are a second concept; if the need
appears, it appears later.

## Draft 1 — roomy and grouped

A Continue card, then search and sort, then books as expandable groups with chapters
indented, then everything else.

Reads well and is closest to what is there now. Its problems, from looking at it:

- **Two progress signals per row, competing.** The vocabulary bar and "page 3 of 6"
  sit side by side and neither wins your eye.
- **Nothing lines up.** The bar starts after the title, so its position moves on every
  row and you cannot scan a column.
- **The Continue card is a second copy of a row** that also appears below.
- **"Everything else"** puts loose articles under books, when loose articles are what
  you read most.
- Roughly six rows on a screen, which is not enough at fifty.

## Draft 2 — a dense, aligned list

The same information as one grid: marker · title · meta · read · you know · actions.

- **One glyph for reading state** in a fixed column — filled started, hollow untouched,
  faded done — so state is scannable straight down the page.
- **One bar, one meaning.** The bar is only ever "how much of this can you already
  read". Position is words, in its own column.
- **Everything aligns**, because the columns are fixed rather than following the title.
- **Books are rows** that expand in place; a chapter is the same row shape, indented.
- **Actions appear on hover**, so `delete` is not sitting one slip from every title —
  which it currently is.
- Nine rows in the space draft 1 used for six.

## Recommendation

**Draft 2**, with Continue kept as the one line above the list. It is denser without
being cramped, and the alignment is what makes fifty rows searchable by eye rather than
only by the search box.

The risk is that it reads as a spreadsheet rather than a reading app. If that turns out
to be true, the fix is spacing and weight, not structure.

## Not in this

Reordering by dragging, nested collections, tags, covers, per-collection settings.
