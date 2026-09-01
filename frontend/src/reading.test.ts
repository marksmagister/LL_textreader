import { describe as group, expect, test } from 'vitest'
import { nextSentence, nextUnknown, segments, sentenceBounds } from './reading'
import type { LessonDetail, Token, TokenState } from './types'

const BODY = "Il marchait le long du quai. Nous marchons."

/** Tokens with real offsets into BODY, the way the importer produces them. */
function tokens(): Token[] {
  const out: Token[] = []
  const re = /[\p{L}']+|[^\p{L}\s]/gu
  let m: RegExpExecArray | null
  let sent = 0
  while ((m = re.exec(BODY))) {
    const surface = m[0]
    out.push({
      idx: out.length,
      surface,
      lemma: /\p{L}/u.test(surface) ? surface.toLowerCase() : null,
      pos: 'X',
      char_start: m.index,
      char_end: m.index + surface.length,
      sent_id: sent,
      morph: '',
      overridden: false,
      state: 'new',
    })
    if (surface === '.') sent++
  }
  return out
}

function lesson(over: Partial<LessonDetail> = {}): LessonDetail {
  return {
    id: 1, lang: 'fr', title: 'x', source: null, pipeline_id: 'stub',
    imported_at: '', n_tokens: 0, n_words: 0, last_token: 0, completed: false, last_read: null,
    n_new: 0, n_learning: 0, n_known: 0, undo_id: null, undo_n: 0,
    page: 0, n_pages: 1, body: BODY, body_offset: 0, tokens: tokens(),
    ...over,
  }
}

group('laying spans over the text', () => {
  test('every character of the body survives, in order', () => {
    // CLAUDE.md rule 2. Losing a space here corrupts the text silently.
    expect(segments(lesson()).map((s) => s.text).join('')).toBe(BODY)
  })

  test('token segments carry the exact text the offsets point at', () => {
    for (const s of segments(lesson())) {
      if (s.token) expect(s.text).toBe(BODY.slice(s.token.char_start, s.token.char_end))
    }
  })

  test('offsets are rebased, so page two is not garbled', () => {
    // A later page's body is a slice, while its offsets stay absolute.
    const full = tokens()
    const cut = 28 // just after the first sentence
    const l = lesson({
      body: BODY.slice(cut),
      body_offset: cut,
      tokens: full.filter((t) => t.char_start >= cut),
    })
    expect(segments(l).map((s) => s.text).join('')).toBe(BODY.slice(cut))
    expect(segments(l).find((s) => s.token)?.text).toBe('Nous')
  })

  test('a slice keeps only the tokens inside it', () => {
    const inside = segments(lesson(), 0, 27).filter((s) => s.token).map((s) => s.text)
    expect(inside).toEqual(['Il', 'marchait', 'le', 'long', 'du', 'quai'])
  })

  test('overlapping tokens are skipped rather than duplicating text', () => {
    // Arabic clitics produce several tokens from one written word.
    const t = tokens()
    const l = lesson({ tokens: [...t, { ...t[1], idx: 99 }] })
    expect(segments(l).map((s) => s.text).join('')).toBe(BODY)
  })
})

group('finding the next word to stop at', () => {
  const known = (states: Record<number, TokenState>) =>
    tokens().map((t, i) => ({ ...t, state: states[i] ?? ('known' as TokenState) }))

  test('Tab goes forward to the next new word', () => {
    expect(nextUnknown(known({ 3: 'new', 5: 'new' }), 0, 1)).toBe(3)
    expect(nextUnknown(known({ 3: 'new', 5: 'new' }), 3, 1)).toBe(5)
  })

  test('Shift-Tab goes back', () => {
    expect(nextUnknown(known({ 3: 'new', 5: 'new' }), 5, -1)).toBe(3)
  })

  test('it wraps, so the end of a page is not a dead end', () => {
    expect(nextUnknown(known({ 1: 'new' }), 5, 1)).toBe(1)
    expect(nextUnknown(known({ 8: 'new' }), 2, -1)).toBe(8)
  })

  test('from no cursor it starts at the beginning', () => {
    expect(nextUnknown(known({ 4: 'new' }), -1, 1)).toBe(4)
  })

  test('a page with nothing blue left returns -1 rather than looping', () => {
    expect(nextUnknown(known({}), 0, 1)).toBe(-1)
    expect(nextUnknown([], -1, 1)).toBe(-1)
  })
})

group('moving by sentence', () => {
  test('forward lands on the first word of the next sentence', () => {
    const t = tokens()
    expect(t[nextSentence(t, 0, 1)].surface).toBe('Nous')
  })

  test('backward lands on the first word of the previous one', () => {
    const t = tokens()
    const inSecond = t.findIndex((x) => x.surface === 'marchons')
    expect(t[nextSentence(t, inSecond, -1)].surface).toBe('Il')
  })

  test('there is nothing past the last sentence', () => {
    const t = tokens()
    expect(nextSentence(t, t.length - 1, 1)).toBe(-1)
    expect(nextSentence(t, 0, -1)).toBe(-1)
  })
})

group('sentence bounds for the English lines', () => {
  test('each sentence spans its own words and no others', () => {
    const bounds = sentenceBounds(lesson())
    expect(bounds.size).toBe(2)
    const [a, b] = bounds.get(0)!
    expect(BODY.slice(a, b)).toBe('Il marchait le long du quai.')
  })
})
