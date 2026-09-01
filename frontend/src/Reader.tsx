import { useEffect, useState } from 'react'
import { finishPage, readLesson, setTerm } from './api'
import type { LessonDetail, Token } from './types'

const STATUSES: Array<[string, number]> = [
  ['Learning', 1],
  ['Almost', 4],
  ['Known', 5],
  ['Ignore', -1],
]

/** Overlay token spans onto the original text. Never rebuild the text from tokens. */
function render(lesson: LessonDetail, onPick: (t: Token) => void) {
  const out = []
  let cursor = 0
  for (const t of lesson.tokens) {
    // offsets are absolute; this page's body starts at body_offset
    const start = t.char_start - lesson.body_offset
    const end = t.char_end - lesson.body_offset
    if (start < cursor) continue // overlapping segments (Arabic); not a pilot case
    if (start > cursor) out.push(lesson.body.slice(cursor, start))
    out.push(
      <span
        key={t.idx}
        className={`tok tok--${t.state}`}
        onClick={t.lemma ? () => onPick(t) : undefined}
      >
        {lesson.body.slice(start, end)}
      </span>,
    )
    cursor = end
  }
  out.push(lesson.body.slice(cursor))
  return out
}

export default function Reader({ id, onBack }: { id: number; onBack: () => void }) {
  const [lesson, setLesson] = useState<LessonDetail | null>(null)
  const [picked, setPicked] = useState<Token | null>(null)
  const [note, setNote] = useState('')

  // page undefined on first load => the backend resumes where you stopped
  const load = (page?: number) =>
    readLesson(id, page).then((l) => {
      setLesson(l)
      setPicked(null)
      window.scrollTo(0, 0)
    })

  useEffect(() => {
    load()
  }, [id])

  if (!lesson) return <main>…</main>

  const save = async (status: number) => {
    if (!picked?.lemma) return
    await setTerm({
      lang: lesson.lang,
      lemma: picked.lemma,
      pos: picked.pos ?? '',
      status,
      surface: picked.surface,
      note: note || null,
    })
    await load(lesson.page)
  }

  /** Turn the page: record what you've met, save your place, move on.
   *  On the last page there is nowhere to move on to, so finishing the lesson
   *  returns you to the library — otherwise the button silently does nothing. */
  const turn = async (markRestKnown: boolean) => {
    await finishPage(id, lesson.page, markRestKnown)
    if (lesson.page + 1 >= lesson.n_pages) return onBack()
    await load(lesson.page + 1)
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
      <div className="text">{render(lesson, (t) => (setPicked(t), setNote('')))}</div>

      {picked && (
        <aside className="panel">
          <p>
            <strong>{picked.surface}</strong>
            {picked.lemma !== picked.surface.toLowerCase() && <em> → {picked.lemma}</em>}
            <span className="pos"> {picked.pos}</span>
          </p>
          {/* No dictionary yet — see docs/status.md. Your own note is the definition. */}
          <input
            value={note}
            placeholder="what it means"
            onChange={(e) => setNote(e.target.value)}
          />
          <p>
            {STATUSES.map(([label, value]) => (
              <button key={value} onClick={() => save(value)}>
                {label}
              </button>
            ))}
            <button onClick={() => setPicked(null)}>close</button>
          </p>
        </aside>
      )}
    </main>
  )
}
