import { describe as group, expect, test } from 'vitest'
import { nextAsking, nextSentence, segments, sentenceBounds, swipeAction } from './reading'
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
      status: null,
      note: null,
      state: 'new',
    })
    if (surface === '.') sent++
  }
  return out
}

function lesson(over: Partial<LessonDetail> = {}): LessonDetail {
  return {
    id: 1, lang: 'fr', title: 'x', source: null, pipeline_id: 'stub',
    imported_at: '', n_tokens: 0, n_words: 0, last_token: 0, completed: false, last_read: null, collection_id: null, collection: null, position: 0,
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
    expect(nextAsking(known({ 3: 'new', 5: 'new' }), 0, 1)).toBe(3)
    expect(nextAsking(known({ 3: 'new', 5: 'new' }), 3, 1)).toBe(5)
  })

  test('Shift-Tab goes back', () => {
    expect(nextAsking(known({ 3: 'new', 5: 'new' }), 5, -1)).toBe(3)
  })

  test('it wraps, so the end of a page is not a dead end', () => {
    expect(nextAsking(known({ 1: 'new' }), 5, 1)).toBe(1)
    expect(nextAsking(known({ 8: 'new' }), 2, -1)).toBe(8)
  })

  test('from no cursor it starts at the beginning', () => {
    expect(nextAsking(known({ 4: 'new' }), -1, 1)).toBe(4)
  })

  test('a page with nothing blue left returns -1 rather than looping', () => {
    expect(nextAsking(known({}), 0, 1)).toBe(-1)
    expect(nextAsking([], -1, 1)).toBe(-1)
  })

  test('it stops on every word that is not plain', () => {
    // Reported from real use: yellow words and unmet shapes were reachable only
    // with the mouse, and those are exactly the ones worth going back to.
    expect(nextAsking(known({ 3: 'learning' }), 0, 1)).toBe(3)
    expect(nextAsking(known({ 3: 'novel-form' }), 0, 1)).toBe(3)
    expect(nextAsking(known({ 2: 'learning', 5: 'new' }), 0, 1)).toBe(2)
  })

  test('it still refuses to stop on a word you know', () => {
    expect(nextAsking(known({}), 0, 1)).toBe(-1)
  })

  test('it stops on a word the app is asking about, not only on a new one', () => {
    // Decision 0008's whole point: at level 4 the word asks to be decided. It
    // used to be reachable only by spotting the rule under it and clicking.
    expect(nextAsking(known({ 5: 'review' }), 0, 1)).toBe(5)
    expect(nextAsking(known({ 3: 'review', 5: 'new' }), 0, 1)).toBe(3)
  })

  test('it now does stop on a novel form, which it used to skip', () => {
    // This test asserted the opposite until 2 September, and the old reasoning
    // was defensible: a novel form asks nothing, you already know the word. Real
    // use disagreed — an unmet shape is precisely what you want to look at, and
    // reaching it only with the mouse broke the keyboard loop. Kept rather than
    // deleted so the reversal is visible.
    expect(nextAsking(known({ 3: 'novel-form' }), 0, 1)).toBe(3)
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

group('swipeAction', () => {
  const at = (x: number, y: number, t = 0) => ({ x, y, t })

  test('forward on a left swipe, back on a right one', () => {
    expect(swipeAction(at(300, 400), at(180, 405, 120))).toBe('next')
    expect(swipeAction(at(180, 400), at(300, 405, 120))).toBe('back')
  })

  test('a scroll does not turn the page, which is the point of the thresholds', () => {
    expect(swipeAction(at(200, 200), at(205, 600, 200))).toBe(null) // straight down
    expect(swipeAction(at(200, 200), at(300, 600, 200))).toBe(null) // drifted sideways
  })

  test('a short flick is a tap that slipped, not a swipe', () => {
    expect(swipeAction(at(200, 400), at(150, 402, 60))).toBe(null)
  })

  test('a slow drag is a selection, not a swipe', () => {
    expect(swipeAction(at(300, 400), at(150, 405, 2000))).toBe(null)
  })

  test('a diagonal that is still mostly sideways counts', () => {
    expect(swipeAction(at(300, 400), at(160, 440, 150))).toBe('next')
  })
})
