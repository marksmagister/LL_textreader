/** The reader's logic, with no React in it, so it can be tested.
 *
 * These three do the work that is easy to get subtly wrong: laying spans over
 * the original text without losing a character of it, finding the next word
 * worth stopping at, and grouping tokens into sentences.
 */
import type { LessonDetail, Token, TokenState } from './types'

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

/** The states Tab stops on: a word you have never judged, and one you have met
 *  often enough that the app is asking (decision 0008). Both want an answer.
 *
 *  Not `novel-form`: that one is telling you something rather than asking, and
 *  there is no key to press. Stopping there would make Tab useless in Russian. */
// Everything that is not plain. Tab used to stop only at blue and at the words
// due a decision, which meant the yellow ones and the novel forms could only be
// reached with the mouse — and those are exactly the words you want to revisit.
const ASKING: TokenState[] = ['new', 'review', 'novel-form', 'learning']

/**
 * The next word that wants a decision, wrapping around the page. -1 when there
 * is none left, which is what makes Tab stop rather than cycle forever.
 */
export function nextAsking(tokens: Token[], cursor: number, dir: 1 | -1): number {
  const n = tokens.length
  if (!n) return -1
  const from = cursor < 0 ? (dir === 1 ? -1 : n) : cursor
  for (let step = 1; step <= n; step++) {
    const i = (((from + dir * step) % n) + n) % n
    if (ASKING.includes(tokens[i].state)) return i
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

/** How far, how flat and how quick a drag must be to count as a page turn. */
export const SWIPE = { distance: 60, flatness: 2, ms: 800 }

/** What a touch that started at `from` and ended at `to` should do.
 *
 * Its own function because the thresholds are the whole feature: a phone has no
 * Tab and no arrow keys (report #19), but it does scroll, and a page that turns
 * itself while you are scrolling is worse than one that never turns at all. So
 * a swipe has to be far enough to be deliberate, flat enough not to be a scroll
 * that drifted, and quick enough not to be a drag or a long press.
 *
 * Left is onward and right is back — the direction the text itself moves, and
 * what every e-reader and carousel already does.
 */
export function swipeAction(
  from: { x: number; y: number; t: number },
  to: { x: number; y: number; t: number },
): 'next' | 'back' | null {
  const dx = to.x - from.x
  const dy = to.y - from.y
  if (Math.abs(dx) < SWIPE.distance) return null
  if (Math.abs(dx) < Math.abs(dy) * SWIPE.flatness) return null
  if (to.t - from.t > SWIPE.ms) return null
  return dx < 0 ? 'next' : 'back'
}
