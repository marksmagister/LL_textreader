import { useEffect, useState } from 'react'
import { listVocab } from './api'
import type { VocabEntry } from './types'

const BUCKETS = ['all', 'new', 'learning', 'known', 'ignored'] as const

function label(status: number) {
  if (status === -1) return 'ignored'
  if (status === 0) return 'new'
  return status >= 5 ? 'known' : `learning ${status}`
}

function stateClass(status: number) {
  if (status === -1 || status >= 5) return 'known'
  return status === 0 ? 'new' : 'learning'
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
            {e.note && <span className="note">{e.note}</span>}
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
