import { useEffect, useRef, useState } from 'react'
import { clearOverride, define, finishPage, readLesson, setOverride, setTerm } from './api'
import { describe } from './morph'
import type { Gloss, LessonDetail, Token } from './types'

/** Overlay token spans onto the original text. Never rebuild the text from tokens. */
function render(lesson: LessonDetail, cursor: number) {
  const out = []
  let cur = 0
  lesson.tokens.forEach((t, i) => {
    const start = t.char_start - lesson.body_offset
    const end = t.char_end - lesson.body_offset
    if (start < cur) return // overlapping segments (Arabic); not a pilot case
    if (start > cur) out.push(lesson.body.slice(cur, start))
    out.push(
      <span
        key={t.idx}
        data-i={i}
        className={`tok tok--${t.state}${i === cursor ? ' tok--cursor' : ''}`}
      >
        {lesson.body.slice(start, end)}
      </span>,
    )
    cur = end
  })
  out.push(lesson.body.slice(cur))
  return out
}

export default function Reader({
  id,
  onBack,
  lang,
}: {
  id: number
  onBack: () => void
  lang: string
}) {
  const [lesson, setLesson] = useState<LessonDetail | null>(null)
  const [cursor, setCursor] = useState(-1)
  const [glosses, setGlosses] = useState<Gloss[]>([])
  const [note, setNote] = useState('')
  const [fixing, setFixing] = useState(false)
  const [fix, setFix] = useState('')
  const text = useRef<HTMLDivElement>(null)
  const noteBox = useRef<HTMLInputElement>(null)
  const fixBox = useRef<HTMLInputElement>(null)

  const load = (page?: number) =>
    readLesson(id, page).then((l) => {
      setLesson(l)
      setCursor(-1)
      window.scrollTo(0, 0)
    })

  useEffect(() => {
    load()
  }, [id])

  const token: Token | null = lesson && cursor >= 0 ? lesson.tokens[cursor] : null

  // Fetch the definition when the cursor lands on a word. The panel appears, but
  // focus stays in the text until you ask for it with Enter.
  useEffect(() => {
    if (!token?.lemma) return setGlosses([])
    setNote('')
    setFixing(false)
    setFix('')
    let live = true
    define(lang, token.lemma, token.pos).then((g) => live && setGlosses(g))
    return () => {
      live = false
    }
  }, [token?.lemma, token?.pos])

  // Esc is handled at the window, not on the text container: after clicking a
  // panel button focus is in the panel, and the spec says Esc must always bring
  // you back to your place in the text. From a field it just returns focus; from
  // anywhere else it also closes the panel.
  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      if (document.querySelector('.scrim')) return // the palette owns Esc while open
      e.preventDefault()
      setFixing(false)
      if (!(e.target instanceof HTMLInputElement)) setCursor(-1)
      text.current?.focus()
    }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [])

  useEffect(() => {
    if (cursor >= 0)
      text.current
        ?.querySelector(`[data-i="${cursor}"]`)
        ?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [cursor])

  if (!lesson) return <main>…</main>

  const toText = () => text.current?.focus()

  /** Tab's whole job: never hunt for blue words. Wraps around the page. */
  const seek = (dir: 1 | -1) => {
    const n = lesson.tokens.length
    const from = cursor < 0 ? (dir === 1 ? -1 : n) : cursor
    for (let step = 1; step <= n; step++) {
      const i = (((from + dir * step) % n) + n) % n
      if (lesson.tokens[i].state === 'new') return setCursor(i)
    }
    setCursor(-1) // nothing blue left on the page
  }

  const seekSentence = (dir: 1 | -1) => {
    const here = token?.sent_id ?? (dir === 1 ? -1 : Infinity)
    const target = lesson.tokens.filter((t) =>
      dir === 1 ? t.sent_id > here : t.sent_id < here,
    )
    const pick = dir === 1 ? target[0] : target[target.length - 1]
    if (pick) setCursor(lesson.tokens.findIndex((t) => t.sent_id === pick.sent_id && t.lemma))
  }

  const save = async (status: number) => {
    if (!token?.lemma) return
    await setTerm({
      lang,
      lemma: token.lemma,
      pos: token.pos ?? '',
      status,
      surface: token.surface,
      note: note || null,
    })
    const keep = cursor
    const l = await readLesson(id, lesson.page)
    setLesson(l)
    setCursor(keep)
  }

  /** Set a status, then jump straight to the next blue word. The core loop. */
  const rate = async (status: number) => {
    await save(status)
    seek(1)
    toText()
  }

  const reload = async () => {
    const keep = cursor
    setLesson(await readLesson(id, lesson.page))
    setCursor(keep)
  }

  /** "This is wrong." Blank detaches the form into its own entry, which is the
   *  common case — you don't want to retype the word, you want the reader to
   *  stop pretending it is something else. CLAUDE.md rule 5. */
  const saveOverride = async () => {
    if (!token?.lemma) return
    await setOverride({
      lang,
      surface: token.surface,
      from_lemma: token.lemma,
      to_lemma: fix.trim() || null,
      to_pos: fix.trim() ? (token.pos ?? 'X') : 'X',
    })
    setFixing(false)
    await reload()
    toText()
  }

  /** Turn the page: record what you've met, save your place, move on.
   *  On the last page there is nowhere to move on to, so finishing the lesson
   *  returns you to the library — otherwise the button silently does nothing. */
  const turn = async (markRestKnown: boolean) => {
    await finishPage(id, lesson.page, markRestKnown)
    if (lesson.page + 1 >= lesson.n_pages) return onBack()
    await load(lesson.page + 1)
  }

  const onKey = (e: React.KeyboardEvent) => {
    const typing = e.target instanceof HTMLInputElement
    if (typing) {
      // Only two keys reach through the note box; everything else is text.
      if (e.key === 'Enter' && e.currentTarget === fixBox.current)
        return (e.preventDefault(), saveOverride())
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) return (e.preventDefault(), rate(1))
      return
    }
    const k = e.key
    if (k === 'Tab') return (e.preventDefault(), seek(e.shiftKey ? -1 : 1))
    if (k === 'Enter') return (e.preventDefault(), noteBox.current?.focus())
    if (k === 'ArrowDown' || k === 'j') return (e.preventDefault(), seekSentence(1))
    if (k === 'ArrowUp') return (e.preventDefault(), seekSentence(-1))
    // Test the modifier rather than trusting the key to arrive uppercased —
    // that varies by layout, and Shift-K clearing the page by accident when it
    // was meant to mark one word known would be a nasty surprise.
    if (k.toLowerCase() === 'k')
      return (e.preventDefault(), e.shiftKey ? turn(true) : rate(5))
    if (k === 'i') return (e.preventDefault(), rate(-1))
    if (k === 'o') return (e.preventDefault(), setFixing(true), void 0)
    // 2/3/4 retired: the level is counted from exposure now, not self-rated.
    if (k === '1') return (e.preventDefault(), rate(1))
  }

  const words = lesson.tokens.filter((t) => t.lemma)
  const unknown = words.filter((t) => t.state === 'new').length
  const last = lesson.page >= lesson.n_pages - 1

  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>← library</button>
        <span>
          page {lesson.page + 1} of {lesson.n_pages} · {unknown} new of {words.length} words
        </span>
        <button disabled={lesson.page === 0} onClick={() => load(lesson.page - 1)}>
          ‹ back
        </button>
        <button onClick={() => turn(true)}>Mark page known</button>
        <button onClick={() => turn(false)}>{last ? 'Finish' : 'Next page ›'}</button>
      </p>

      <h1>{lesson.title}</h1>

      {/* One handler on the container, not one per token. */}
      <div
        className="text"
        ref={text}
        tabIndex={0}
        onKeyDown={onKey}
        onClick={(e) => {
          const el = (e.target as HTMLElement).closest('[data-i]')
          if (el) setCursor(Number(el.getAttribute('data-i')))
        }}
      >
        {render(lesson, cursor)}
      </div>

      {token?.lemma && (
        <aside className="panel">
          <p>
            <strong>{token.surface}</strong>
            {token.lemma !== token.surface.toLowerCase() && <em> → {token.lemma}</em>}
            <span className="pos"> {token.pos}</span>
            {/* why this form differs from the lemma, not just that it belongs to it */}
            {describe(token.morph) && <span className="morph">{describe(token.morph)}</span>}
            <button className="ghost" onClick={() => setFixing(true)} title="o">
              wrong word?
            </button>
            {token.overridden && (
              <button
                className="ghost"
                onClick={async () => {
                  await clearOverride(lang, token.surface)
                  await reload()
                  toText()
                }}
              >
                undo override
              </button>
            )}
          </p>

          <ol className="glosses">
            {glosses.length === 0 && <li className="muted">no dictionary entry</li>}
            {glosses.map((g, i) => (
              <li key={i}>
                <span className="pos">{g.pos}</span> {g.gloss}
              </li>
            ))}
          </ol>

          {fixing && (
            <p>
              <input
                ref={fixBox}
                autoFocus
                value={fix}
                placeholder={`correct lemma for "${token.surface}" — blank to detach it`}
                onChange={(e) => setFix(e.target.value)}
                onKeyDown={onKey}
              />
              <button onClick={saveOverride}>save</button>
              <button onClick={() => (setFixing(false), toText())}>cancel</button>
            </p>
          )}

          <input
            ref={noteBox}
            value={note}
            placeholder="your own note (⌘↵ to save as learning)"
            onChange={(e) => setNote(e.target.value)}
            onKeyDown={onKey}
          />
          <p className="keys">
            <button onClick={() => rate(1)}>1 learning</button>
            <button onClick={() => rate(5)}>k known</button>
            <button onClick={() => rate(-1)}>i ignore</button>
            <button onClick={() => (setCursor(-1), toText())}>esc</button>
            {token.state === 'review' && (
              <span className="muted">met this often — do you know it now?</span>
            )}
          </p>
        </aside>
      )}
    </main>
  )
}
