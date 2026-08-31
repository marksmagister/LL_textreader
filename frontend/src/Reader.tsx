import { useEffect, useState } from 'react'
import { finishLesson, readLesson, setTerm } from './api'
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
    if (t.char_start < cursor) continue // overlapping segments (Arabic); not a pilot case
    if (t.char_start > cursor) out.push(lesson.body.slice(cursor, t.char_start))
    out.push(
      <span
        key={t.idx}
        className={`tok tok--${t.state}`}
        onClick={t.lemma ? () => onPick(t) : undefined}
      >
        {lesson.body.slice(t.char_start, t.char_end)}
      </span>,
    )
    cursor = t.char_end
  }
  out.push(lesson.body.slice(cursor))
  return out
}

export default function Reader({ id, onBack }: { id: number; onBack: () => void }) {
  const [lesson, setLesson] = useState<LessonDetail | null>(null)
  const [picked, setPicked] = useState<Token | null>(null)
  const [note, setNote] = useState('')

  const load = () => readLesson(id).then(setLesson)
  useEffect(() => {
    load()
  }, [id])

  if (!lesson) return <main>…</main>

  const pick = (t: Token) => {
    setPicked(t)
    setNote('')
  }

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
    setPicked(null)
    await load()
  }

  const finish = async (markRestKnown: boolean) => {
    await finishLesson(id, markRestKnown)
    await load()
  }

  const words = lesson.tokens.filter((t) => t.lemma)
  const unknown = words.filter((t) => t.state === 'new').length

  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>← library</button>
        <span>
          {unknown} new of {words.length} words
        </span>
        <button onClick={() => finish(false)}>Done reading</button>
        <button onClick={() => finish(true)}>Mark rest known</button>
      </p>

      <h1>{lesson.title}</h1>
      <div className="text">{render(lesson, pick)}</div>

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
