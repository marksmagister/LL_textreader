/** The reader's logic, with no React in it, so it can be tested.
 *
 * These three do the work that is easy to get subtly wrong: laying spans over
 * the original text without losing a character of it, finding the next word
 * worth stopping at, and grouping tokens into sentences.
 */
import type { LessonDetail, Token } from './types'

export interface Segment {
  text: string
  /** Absent for the plain text between tokens. */
  token?: Token
  /** Index into `lesson.tokens`, which is what the cursor counts in. */
  at?: number
}

/**
 * Cut a page into alternating plain text and token spans.
 *
 * Offsets are absolute into the whole lesson, while `body` is only this page's
 * slice, so everything is rebased by `body_offset`. Text is always *sliced from
 * the body*, never rebuilt from tokens — Arabic segmentation is one-to-many and
 * anything else would silently corrupt the text (CLAUDE.md rule 2).
 */
export function segments(lesson: LessonDetail, from = 0, to = Infinity): Segment[] {
  const out: Segment[] = []
  let cur = from
  lesson.tokens.forEach((t, at) => {
    const start = t.char_start - lesson.body_offset
    const end = t.char_end - lesson.body_offset
    if (start < cur || start >= to) return // outside this slice, or overlapping
    if (start > cur) out.push({ text: lesson.body.slice(cur, start) })
    out.push({ text: lesson.body.slice(start, end), token: t, at })
    cur = end
  })
  const tail = lesson.body.slice(cur, to === Infinity ? undefined : to)
  if (tail) out.push({ text: tail })
  return out
}

/**
 * The next word still marked new, wrapping around the page. -1 when there is
 * none left, which is what makes Tab stop rather than cycle forever.
 */
export function nextUnknown(tokens: Token[], cursor: number, dir: 1 | -1): number {
  const n = tokens.length
  if (!n) return -1
  const from = cursor < 0 ? (dir === 1 ? -1 : n) : cursor
  for (let step = 1; step <= n; step++) {
    const i = (((from + dir * step) % n) + n) % n
    if (tokens[i].state === 'new') return i
  }
  return -1
}

/** The first lexical token of the next or previous sentence, or -1. */
export function nextSentence(tokens: Token[], cursor: number, dir: 1 | -1): number {
  const here = cursor >= 0 ? tokens[cursor].sent_id : dir === 1 ? -1 : Infinity
  const reachable = tokens.filter((t) => (dir === 1 ? t.sent_id > here : t.sent_id < here))
  const pick = dir === 1 ? reachable[0] : reachable[reachable.length - 1]
  if (!pick) return -1
  return tokens.findIndex((t) => t.sent_id === pick.sent_id && t.lemma)
}

/** Character bounds of each sentence, for laying English under the French. */
export function sentenceBounds(lesson: LessonDetail): Map<number, [number, number]> {
  const bounds = new Map<number, [number, number]>()
  for (const t of lesson.tokens) {
    const a = t.char_start - lesson.body_offset
    const b = t.char_end - lesson.body_offset
    const seen = bounds.get(t.sent_id)
    bounds.set(t.sent_id, seen ? [Math.min(seen[0], a), Math.max(seen[1], b)] : [a, b])
  }
  return bounds
}
