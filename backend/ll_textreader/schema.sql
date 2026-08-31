-- LL_textreader schema. Source of truth; migrations are applied by db.py.
-- SQLite. Single file. Single user for now, but user_id is present everywhere
-- so that assumption is cheap to drop later.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- users

CREATE TABLE IF NOT EXISTS user (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------- lessons

CREATE TABLE IF NOT EXISTS lesson (
    id            INTEGER PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES user(id),
    lang          TEXT    NOT NULL,          -- ISO 639-1: nl, fr, ru, ar
    title         TEXT    NOT NULL,
    source        TEXT,                      -- url / filename / null
    body          TEXT    NOT NULL,          -- the ORIGINAL text, untouched.
                                             -- token offsets index into this.
    audio_path    TEXT,
    -- which pipeline produced this lesson's tokens. A model upgrade makes
    -- stored streams stale; this is how you find what to reprocess.
    pipeline_id   TEXT    NOT NULL,          -- e.g. "spacy/fr_core_news_md@3.8.0"
    imported_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_lesson_user_lang ON lesson(user_id, lang);

-- One row per token, produced once at import. Never at render.
-- Arabic clitic segmentation makes several tokens from one whitespace word,
-- so (char_start,char_end) may overlap between siblings and need not cover the text.
CREATE TABLE IF NOT EXISTS token (
    lesson_id   INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    idx         INTEGER NOT NULL,            -- position within the lesson
    surface     TEXT    NOT NULL,            -- as written, before normalisation
    norm        TEXT    NOT NULL,            -- case-folded, diacritics handled
    lemma       TEXT,                        -- NULL = not a lexical token
    pos         TEXT,                        -- UD tag: VERB, NOUN, ...
    char_start  INTEGER NOT NULL,            -- char offset into lesson.body
    char_end    INTEGER NOT NULL,
    sent_id     INTEGER NOT NULL,
    confidence  REAL    NOT NULL DEFAULT 1.0, -- < threshold => treat as surface form
    PRIMARY KEY (lesson_id, idx)
);

CREATE INDEX IF NOT EXISTS idx_token_lemma ON token(lemma, pos);

-- ---------------------------------------------------------------- the lexicon
-- The entire product is these two tables.

-- 0 new · 1-4 learning (4 = nearly there) · 5 known · -1 ignored (names, numbers)
CREATE TABLE IF NOT EXISTS lemma_status (
    user_id     INTEGER NOT NULL REFERENCES user(id),
    lang        TEXT    NOT NULL,
    lemma       TEXT    NOT NULL,
    pos         TEXT    NOT NULL,            -- '' when the language has no useful POS
    status      INTEGER NOT NULL DEFAULT 1,
    note        TEXT,                        -- the user's own definition
    context     TEXT,                        -- the sentence it was first met in
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, lang, lemma, pos)
);

-- Which inflections have actually been met. Drives the "known lemma, novel
-- form" highlight, and doubles as free data on inflectional coverage.
CREATE TABLE IF NOT EXISTS form_seen (
    user_id     INTEGER NOT NULL REFERENCES user(id),
    lang        TEXT    NOT NULL,
    lemma       TEXT    NOT NULL,
    pos         TEXT    NOT NULL,
    surface     TEXT    NOT NULL,
    count       INTEGER NOT NULL DEFAULT 1,
    first_seen  TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, lang, lemma, pos, surface)
);

-- The escape hatch. When the lemmatiser is wrong, the user detaches a surface
-- form; pipeline output is joined against this and the override wins.
CREATE TABLE IF NOT EXISTS lemma_override (
    user_id      INTEGER NOT NULL REFERENCES user(id),
    lang         TEXT    NOT NULL,
    surface      TEXT    NOT NULL,           -- normalised
    from_lemma   TEXT,                       -- what the pipeline said (audit)
    to_lemma     TEXT    NOT NULL,           -- what it should be; may = surface
    to_pos       TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, lang, surface)
);

-- ---------------------------------------------------------------- dictionary
-- Populated from downloaded data (see NOTICE). Not user data; safe to rebuild.

CREATE TABLE IF NOT EXISTS hint (
    id          INTEGER PRIMARY KEY,
    lang        TEXT NOT NULL,
    target_lang TEXT NOT NULL,               -- language of the gloss
    lemma       TEXT NOT NULL,
    pos         TEXT,
    gloss       TEXT NOT NULL,
    rank        INTEGER NOT NULL DEFAULT 0,  -- lower sorts first
    source      TEXT NOT NULL                -- 'wiktionary', 'user', ...
);

CREATE INDEX IF NOT EXISTS idx_hint_lookup ON hint(lang, lemma, target_lang);

-- Arabic only: secondary index for a "related words" panel.
-- NEVER used as a status key — ك-ت-ب is five different vocabulary items.
CREATE TABLE IF NOT EXISTS root_index (
    lang   TEXT NOT NULL,
    lemma  TEXT NOT NULL,
    root   TEXT NOT NULL,
    PRIMARY KEY (lang, lemma, root)
);

CREATE INDEX IF NOT EXISTS idx_root ON root_index(lang, root);

-- ---------------------------------------------------------------- reading state

CREATE TABLE IF NOT EXISTS reading_progress (
    user_id     INTEGER NOT NULL REFERENCES user(id),
    lesson_id   INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    last_token  INTEGER NOT NULL DEFAULT 0,
    completed   INTEGER NOT NULL DEFAULT 0,
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, lesson_id)
);
