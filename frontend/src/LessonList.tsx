import { useMemo, useState } from 'react'
import type { LessonSummary } from './types'

/** Sorted and searched here rather than on the server: the whole library is one
 *  small request already, and filtering as you type should not wait on a round
 *  trip. If this ever gets slow it means there are thousands, not fifty.
 *
 *  Each is written in its natural direction; pressing it again reverses it, so
 *  "easiest" and "hardest" are one button rather than two words. */
const SORTS: Array<[string, string, (a: LessonSummary, b: LessonSummary) => number]> = [
  // "Last read" means the last time you did anything here — judging a word
  // counts, not only turning a page. Never touched at all falls back to when it
  // arrived, so the order stays meaningful all the way down.
  ['recent', 'last read', (a, b) => when(b).localeCompare(when(a))],
  ['title', 'title', (a, b) => a.title.localeCompare(b.title)],
  ['known', 'you know', (a, b) => share(b) - share(a)],
  ['length', 'length', (a, b) => b.n_words - a.n_words],
]

/** Last read, or failing that when it arrived. */
function when(l: LessonSummary) {
  return l.last_read ?? l.imported_at ?? ''
}

/** "3 days ago", which is what you want to know about a lesson you half-read. */
function ago(when: string) {
  const days = Math.floor((Date.now() - Date.parse(when + 'Z')) / 86_400_000)
  if (days < 1) return 'today'
  if (days === 1) return 'yesterday'
  return `${days} days ago`
}

/** The detail behind the bar, for hovering. The row itself stays uncluttered. */
function detail(l: LessonSummary) {
  return [
    `${l.n_words} words`,
    `${l.n_known} you know · ${l.n_learning} learning · ${l.n_new} new`,
    l.completed ? 'finished' : l.last_token ? `${progress(l)} of the way through` : 'not started',
    l.last_read ? `last used ${ago(l.last_read!)}` : 'never opened',
  ].join('\n')
}

/** How much of a text you can already read. The one number worth comparing. */
function share(l: LessonSummary) {
  return l.n_words ? l.n_known / l.n_words : 0
}

function progress(l: LessonSummary) {
  if (l.completed) return 'done'
  if (!l.last_token || !l.n_tokens) return '—'
  return `${Math.round((l.last_token / l.n_tokens) * 100)}%`
}

/** Filled you have started, hollow you have not, faded you have finished. One
 *  glyph in a fixed column, so state reads straight down the page. */
function Marker({ lesson }: { lesson: LessonSummary }) {
  // Finished reads as ticked off rather than struck through: still legible,
  // clearly behind you.
  if (lesson.completed) return <span className="tick">✓</span>
  return <span className={`dot ${lesson.last_token ? 'started' : ''}`} />
}

export default function LessonList({
  lessons,
  onOpen,
  onDelete,
}: {
  lessons: LessonSummary[]
  onOpen: (id: number) => void
  onDelete: (id: number) => void
}) {
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('recent')
  const [flipped, setFlipped] = useState(false)
  const [confirming, setConfirming] = useState<number | null>(null)

  const shown = useMemo(() => {
    const compare = SORTS.find(([k]) => k === sort)![2]
    const needle = q.trim().toLowerCase()
    return lessons
      .filter((l) => !needle || l.title.toLowerCase().includes(needle))
      .sort((a, b) => (flipped ? -compare(a, b) : compare(a, b)))
  }, [lessons, q, sort, flipped])

  // What you almost always want: the thing you were last in and have not finished.
  const continuing = useMemo(
    () =>
      lessons
        .filter((l) => l.last_read && !l.completed)
        .sort((a, b) => (b.last_read ?? '').localeCompare(a.last_read ?? ''))[0],
    [lessons],
  )

  if (!lessons.length) return <p className="muted">Nothing here yet. Import something above.</p>

  return (
    <>
      {continuing && (
        <p className="bar continue-line">
          <span className="meta">Continue</span>
          <button className="link" onClick={() => onOpen(continuing.id)}>
            {continuing.title}
          </button>
          <span className="meta">{progress(continuing)} read</span>
        </p>
      )}

      <p className="bar">
        <input
          className="grow"
          value={q}
          placeholder="search titles…"
          onChange={(e) => setQ(e.target.value)}
        />
        {SORTS.map(([key, label]) => (
          <button
            key={key}
            className={key === sort ? 'on' : ''}
            // Pressing the one already chosen turns it around.
            onClick={() => (key === sort ? setFlipped(!flipped) : (setSort(key), setFlipped(false)))}
          >
            {label}
            {key === sort && <span className="arrow">{flipped ? '↑' : '↓'}</span>}
          </button>
        ))}
      </p>

      <div className="lrow heads">
        <span />
        <span>title</span>
        <span className="right">read</span>
        <span className="right">you know</span>
        <span />
      </div>

      {shown.map((l) => (
        <div className={`lrow${l.completed ? ' is-done' : ''}`} key={l.id}>
          <Marker lesson={l} />
          <button className="name" onClick={() => onOpen(l.id)}>
            {l.title}
          </button>
          <span className="pos">{progress(l)}</span>
          <span className="diff" title={detail(l)}>
            {/* One bar, one meaning: how much of this you can already read. */}
            <span className="shape-bar">
              <span className="tok--known" style={{ width: `${share(l) * 100}%` }} />
              <span
                className="tok--learning"
                style={{ width: `${(l.n_words ? l.n_learning / l.n_words : 0) * 100}%` }}
              />
              <span
                className="tok--new"
                style={{ width: `${(l.n_words ? l.n_new / l.n_words : 0) * 100}%` }}
              />
            </span>
            <span className="pct">{Math.round(share(l) * 100)}%</span>
          </span>
          {/* Out of the row until you reach for it: delete used to sit one slip
              from every title. */}
          {confirming === l.id ? (
            <span className="act shown">
              <button
                className="ghost"
                onClick={() => {
                  onDelete(l.id)
                  setConfirming(null)
                }}
              >
                delete?
              </button>
            </span>
          ) : (
            <button className="act" title="remove" onClick={() => setConfirming(l.id)}>
              ×
            </button>
          )}
        </div>
      ))}

      {!shown.length && <p className="muted">Nothing matches “{q}”.</p>}
    </>
  )
}
