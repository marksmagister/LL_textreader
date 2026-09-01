import { useEffect, useState } from 'react'
import { exportUrl, listVocab } from './api'
import type { VocabEntry } from './types'

const BUCKETS = ['all', 'new', 'learning', 'known', 'ignored'] as const

// "stale" is the one worth having: words you were learning that then stopped
// appearing. Nothing else in the app would ever show you those.
const SORTS = [
  ['recent', 'last seen'],
  ['stale', 'longest unseen'],
  ['alpha', 'a–z'],
  ['forms', 'most forms'],
] as const

/** "3 days ago" beats a timestamp when the question is "has this gone quiet?" */
function ago(when: string | null) {
  if (!when) return 'never met'
  const days = Math.floor((Date.now() - Date.parse(when + 'Z')) / 86_400_000)
  if (days < 1) return 'today'
  if (days === 1) return 'yesterday'
  return `${days}d ago`
}

function label(status: number) {
  if (status === -1) return 'ignored'
  if (status === 0) return 'new'
  if (status >= 5) return 'known'
  // 4 means "met often enough that you should decide" — not "almost known"
  return status >= 4 ? 'do you know it?' : 'learning'
}

function stateClass(status: number) {
  if (status === -1 || status >= 5) return 'known'
  if (status === 0) return 'new'
  return status >= 4 ? 'review' : 'learning'
}

export default function Vocab({ lang, onBack }: { lang: string; onBack: () => void }) {
  const [entries, setEntries] = useState<VocabEntry[]>([])
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [total, setTotal] = useState(0)
  const [bucket, setBucket] = useState<string>('all')
  const [q, setQ] = useState('')
  const [picked, setPicked] = useState<Set<string>>(new Set())
  const [sort, setSort] = useState('recent')

  useEffect(() => {
    listVocab(lang, bucket === 'all' ? undefined : bucket, q || undefined, sort).then((v) => {
      setEntries(v.entries)
      setCounts(v.by_status)
      setTotal(v.total)
    })
  }, [lang, bucket, q, sort])

  const key = (e: VocabEntry) => `${e.lemma}:${e.pos}`
  const toggle = (k: string) =>
    setPicked((was) => {
      const next = new Set(was)
      if (next.has(k)) next.delete(k)
      else next.add(k)
      return next
    })

  // Ticked words win; otherwise you get whatever the filters are showing.
  const selection = picked.size ? [...picked] : undefined
  const scope = picked.size
    ? `${picked.size} selected`
    : bucket === 'all' && !q
      ? `all ${total}`
      : `${entries.length} shown`

  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>← library</button>
        <span>
          {total} words · {counts.known ?? 0} known
        </span>
      </p>
      <h1>Vocabulary</h1>

      <p className="bar">
        {BUCKETS.map((b) => (
          <button
            key={b}
            className={b === bucket ? 'on' : ''}
            onClick={() => setBucket(b)}
          >
            {b} {b === 'all' ? total : (counts[b] ?? 0)}
          </button>
        ))}
        <input value={q} placeholder="starts with…" onChange={(e) => setQ(e.target.value)} />
      </p>

      <p className="bar">
        <span className="meta">sort:</span>
        {SORTS.map(([key, label]) => (
          <button key={key} className={key === sort ? 'on' : ''} onClick={() => setSort(key)}>
            {label}
          </button>
        ))}
      </p>

      <p className="bar">
        <span className="meta">export {scope}:</span>
        {(['anki', 'csv', 'json'] as const).map((f) => (
          <a
            key={f}
            className="button"
            href={exportUrl(lang, f, { status: bucket, q, keys: selection })}
          >
            {f === 'anki' ? 'Anki deck' : f}
          </a>
        ))}
        {picked.size > 0 && (
          <button className="ghost" onClick={() => setPicked(new Set())}>
            clear selection
          </button>
        )}
      </p>

      {entries.length === 0 && <p className="muted">Nothing here yet.</p>}

      <ul className="vocab">
        {entries.map((e) => (
          <li key={`${e.lemma}/${e.pos}`}>
            <input
              type="checkbox"
              checked={picked.has(key(e))}
              onChange={() => toggle(key(e))}
              aria-label={`select ${e.lemma}`}
            />
            <span className={`tok tok--${stateClass(e.status)}`}>{e.lemma}</span>
            <span className="pos">{e.pos}</span>
            <span className="meta">{label(e.status)}</span>
            {/* occurrences, not pages — the level counts pages, so these differ */}
            {e.met > 0 && <span className="meta">seen {e.met}×</span>}
            <span className="meta">{ago(e.last_seen)}</span>
            {e.note && <span className="note">{e.note}</span>}
            {/* where you met it — often more use than a definition */}
            {e.context && <span className="context">“{e.context}”</span>}
            {/* which shapes of this word you have actually met */}
            <span className="forms">
              {e.forms.length === 0 ? (
                <em className="muted">no forms met yet</em>
              ) : (
                e.forms.map((f) => (
                  <span key={f} className="form">
                    {f}
                  </span>
                ))
              )}
            </span>
          </li>
        ))}
      </ul>
    </main>
  )
}
