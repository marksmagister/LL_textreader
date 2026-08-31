/** Mirrors backend/ll_textreader/models.py. Keep the two in step. */
export type TokenState = 'new' | 'learning' | 'novel-form' | 'known'

export interface Token {
  idx: number
  surface: string
  lemma: string | null
  pos: string | null
  char_start: number
  char_end: number
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
