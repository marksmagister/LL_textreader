import { useEffect, useState } from 'react'
import { listVocab } from './api'
import type { VocabEntry } from './types'

const BUCKETS = ['all', 'new', 'learning', 'known', 'ignored'] as const

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

  useEffect(() => {
    listVocab(lang, bucket === 'all' ? undefined : bucket, q || undefined).then((v) => {
      setEntries(v.entries)
      setCounts(v.by_status)
      setTotal(v.total)
    })
  }, [lang, bucket, q])

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

      {entries.length === 0 && <p className="muted">Nothing here yet.</p>}

      <ul className="vocab">
        {entries.map((e) => (
          <li key={`${e.lemma}/${e.pos}`}>
            <span className={`tok tok--${stateClass(e.status)}`}>{e.lemma}</span>
            <span className="pos">{e.pos}</span>
            <span className="meta">{label(e.status)}</span>
            {/* occurrences, not pages — the level counts pages, so these differ */}
            {e.met > 0 && <span className="meta">seen {e.met}×</span>}
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
