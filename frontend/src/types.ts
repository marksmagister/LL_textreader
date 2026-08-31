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
}

export interface LessonDetail extends LessonSummary {
  /** The original text. Token spans are overlaid onto this; never rebuilt from tokens. */
  body: string
  tokens: Token[]
}
