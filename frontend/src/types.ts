/** Mirrors backend/ll_textreader/models.py. Keep the two in step. */
export type TokenState = 'new' | 'learning' | 'novel-form' | 'known'

export interface Token {
  idx: number
  surface: string
  lemma: string | null
  pos: string | null
  charStart: number
  charEnd: number
  state: TokenState
}
