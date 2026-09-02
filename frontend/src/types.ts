/** Mirrors backend/ll_textreader/models.py. Keep the two in step. */
export type TokenState = 'new' | 'learning' | 'review' | 'novel-form' | 'known'

export interface Token {
  idx: number
  surface: string
  lemma: string | null
  pos: string | null
  char_start: number
  char_end: number
  sent_id: number
  /** UD features explaining why this form differs from the lemma. */
  morph: string
  /** You have corrected the lemmatiser on this form. */
  overridden: boolean
  /** Your level for the lemma, 0-5, or null if you have never judged it. */
  status: number | null
  /** Your own note on the lemma. */
  note: string | null
  state: TokenState
}

export interface LessonSummary {
  id: number
  lang: string
  title: string
  source: string | null
  pipeline_id: string
  imported_at: string
  n_tokens: number
  n_words: number
  /** Where you stopped, as a token index. 0 = not started. */
  last_token: number
  completed: boolean
  /** When you last turned a page in it. Null means never opened. */
  last_read: string | null
  collection_id: number | null
  collection: string | null
  position: number
  /** Token counts by state, so the library can show the shape of a text. */
  n_new: number
  n_learning: number
  n_known: number
  /** Set by a bulk action, so it can be taken back. */
  undo_id: number | null
  undo_n: number
}

/** One page. Pages are derived from the token stream, not stored. */
export interface LessonDetail extends LessonSummary {
  page: number
  n_pages: number
  /** This page's slice of the original text. Spans overlay it; never rebuilt. */
  body: string
  /** Where the slice starts, since token offsets stay absolute. */
  body_offset: number
  tokens: Token[]
}

/** A dictionary sense. Mirrors ll_textreader/dictionary.py:lookup. */
export interface Gloss {
  pos: string
  gloss: string
  source: string
}

export interface VocabEntry {
  lemma: string
  pos: string
  status: number
  note: string | null
  /** The sentence you first met it in. */
  context: string | null
  updated_at: string
  /** The inflections you have actually met. */
  forms: string[]
  /** Occurrences on pages you finished. The level counts *pages*, so this is
   *  the larger number of the two. */
  met: number
  /** When you last finished a page containing it. Null means never. */
  last_seen: string | null
}
