import { useMemo, useState } from 'react'
import { setCollection } from './api'
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

/** "3 days ago", which is what you want to know about a lesson you half-read.
 *  SQLite's "2026-09-02 10:06:12" needs the T to be portably parseable. */
function ago(when: string) {
  const days = Math.floor((Date.now() - Date.parse(when.replace(' ', 'T') + 'Z')) / 86_400_000)
  if (days < 1) return 'today'
  if (days === 1) return 'yesterday'
  return `${days} days ago`
}

/** What the bar is made of, on hover.
 *
 * Its own element rather than a `title` attribute: a native tooltip waits about
 * a second, cannot be styled, and on a hundred-pixel target most people never
 * see it at all. The swatches are the bar's own colours, so the numbers and the
 * picture are obviously the same thing. */
function Detail({ lesson: l }: { lesson: LessonSummary }) {
  const pct = (n: number) => (l.n_words ? Math.round((n / l.n_words) * 100) : 0)
  return (
    <span className="detail">
      <strong>{l.n_words} words</strong>
      <span className="detail-row">
        <i className="tok--known" /> {l.n_known} you know <em>{pct(l.n_known)}%</em>
      </span>
      <span className="detail-row">
        <i className="tok--learning" /> {l.n_learning} learning <em>{pct(l.n_learning)}%</em>
      </span>
      <span className="detail-row">
        <i className="tok--new" /> {l.n_new} never seen <em>{pct(l.n_new)}%</em>
      </span>
      <span className="detail-foot">
        {l.completed
          ? 'finished'
          : l.last_token
            ? `${progress(l)} of the way through`
            : 'not started'}
        {' · '}
        {l.last_read ? `used ${ago(l.last_read)}` : 'never opened'}
      </span>
    </span>
  )
}

/** A collection's difficulty is its words all together, not the mean of its
 *  chapters — a long hard chapter should weigh more than a short easy one. */
function aggregate(rows: LessonSummary[]) {
  const words = rows.reduce((n, r) => n + r.n_words, 0)
  return words ? rows.reduce((n, r) => n + r.n_known, 0) / words : 0
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

/** A row, whether it stands alone or sits inside a collection. */
function Row({
  lesson: l,
  onOpen,
  onDelete,
  onMove,
  names,
  inside,
}: {
  lesson: LessonSummary
  onOpen: (id: number) => void
  onDelete: (id: number) => void
  onMove: (id: number, name: string | null) => void
  names: string[]
  inside?: boolean
}) {
  const [act, setAct] = useState<'' | 'delete' | 'move'>('')
  const [name, setName] = useState(l.collection ?? '')

  return (
    <div className={`lrow${l.completed ? ' is-done' : ''}${inside ? ' chap' : ''}`}>
      <Marker lesson={l} />
      {act === 'move' ? (
        <span className="bar">
          <input
            autoFocus
            className="grow"
            list="collection-names"
            value={name}
            placeholder="collection name — blank to take it out"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onMove(l.id, name.trim() || null)
                setAct('')
              }
              if (e.key === 'Escape') setAct('')
            }}
          />
          <datalist id="collection-names">
            {names.map((n) => (
              <option key={n} value={n} />
            ))}
          </datalist>
        </span>
      ) : (
        <button className="name" onClick={() => onOpen(l.id)}>
          {l.title}
        </button>
      )}
      <span className="pos">{progress(l)}</span>
      <span className="diff">
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
        <Detail lesson={l} />
      </span>
      <span className="acts">
        {act === 'delete' ? (
          <button
            className="ghost"
            onClick={() => {
              onDelete(l.id)
              setAct('')
            }}
          >
            delete?
          </button>
        ) : (
          <>
            <button className="act" title="put in a collection" onClick={() => setAct('move')}>
              ⊞
            </button>
            <button className="act" title="remove" onClick={() => setAct('delete')}>
              ×
            </button>
          </>
        )}
      </span>
    </div>
  )
}

export default function LessonList({
  lessons,
  onOpen,
  onDelete,
  onChanged,
}: {
  lessons: LessonSummary[]
  onOpen: (id: number) => void
  onDelete: (id: number) => void
  onChanged: () => void
}) {
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('recent')
  const [flipped, setFlipped] = useState(false)
  const [open, setOpen] = useState<Set<string>>(new Set())

  const names = useMemo(
    () => [...new Set(lessons.map((l) => l.collection).filter(Boolean))] as string[],
    [lessons],
  )

  const move = (id: number, name: string | null) => setCollection(id, name).then(onChanged)

  const shown = useMemo(() => {
    const compare = SORTS.find(([k]) => k === sort)![2]
    const needle = q.trim().toLowerCase()
    return lessons
      .filter((l) => !needle || l.title.toLowerCase().includes(needle))
      .sort((a, b) => (flipped ? -compare(a, b) : compare(a, b)))
  }, [lessons, q, sort, flipped])

  /** Collections keep their internal order; loose lessons follow the chosen sort.
   *  A collection sits where its most recently used member would have sat, so
   *  sorting still means something with books in the list. */
  const groups = useMemo(() => {
    const out: Array<[string | null, LessonSummary[]]> = []
    const seen = new Map<string, LessonSummary[]>()
    for (const l of shown) {
      if (!l.collection) {
        out.push([null, [l]])
        continue
      }
      let rows = seen.get(l.collection)
      if (!rows) {
        rows = []
        seen.set(l.collection, rows)
        out.push([l.collection, rows])
      }
      rows.push(l)
    }
    for (const rows of seen.values()) rows.sort((a, b) => a.position - b.position)
    return out
  }, [shown])

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

      {groups.map(([name, rows]) =>
        name === null ? (
          rows.map((l) => (
            <Row key={l.id} lesson={l} onOpen={onOpen} onDelete={onDelete} onMove={move} names={names} />
          ))
        ) : (
          // Collapsed by default: a book should be one line until you want it.
          <details className="group" key={name} open={open.has(name)}>
            <summary
              className="lrow"
              onClick={(e) => {
                e.preventDefault()
                setOpen((was) => {
                  const next = new Set(was)
                  if (next.has(name)) next.delete(name)
                  else next.add(name)
                  return next
                })
              }}
            >
              <span className="caret">{open.has(name) ? '▾' : '▸'}</span>
              <span className="name group-name">
                {name} <span className="meta">{rows.length} parts</span>
              </span>
              <span className="pos">{rows.filter((r) => r.completed).length} read</span>
              <span className="diff">
                <span className="shape-bar">
                  <span className="tok--known" style={{ width: `${aggregate(rows) * 100}%` }} />
                </span>
                <span className="pct">{Math.round(aggregate(rows) * 100)}%</span>
              </span>
              <span />
            </summary>
            {rows.map((l) => (
              <Row key={l.id} lesson={l} onOpen={onOpen} onDelete={onDelete} onMove={move} names={names} inside />
            ))}
          </details>
        ),
      )}

      {!shown.length && <p className="muted">Nothing matches “{q}”.</p>}
    </>
  )
}
