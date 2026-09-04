import { useEffect, useState } from 'react'
import { exportUrl, listVocab } from './api'
import { t } from './i18n'
import type { VocabEntry } from './types'

const BUCKETS = ['all', 'new', 'learning', 'known', 'ignored'] as const

const BUCKET_NAMES = {
  all: 'vocab.all',
  new: 'vocab.new',
  learning: 'vocab.learning',
  known: 'vocab.known',
  ignored: 'vocab.ignored',
} as const

// "stale" is the one worth having: words you were learning that then stopped
// appearing. Nothing else in the app would ever show you those.
const SORTS = [
  ['recent', 'vocab.sortRecent'],
  ['stale', 'vocab.sortStale'],
  ['alpha', 'vocab.sortAlpha'],
  ['forms', 'vocab.sortForms'],
] as const

/** "3 days ago" beats a timestamp when the question is "has this gone quiet?"
 *
 *  SQLite writes "2026-09-02 10:06:12"; only "…T10:06:12Z" is a format every
 *  browser must parse. Chrome takes the space, others are free not to. */
function ago(when: string | null) {
  if (!when) return t('time.never')
  const days = Math.floor((Date.now() - Date.parse(when.replace(' ', 'T') + 'Z')) / 86_400_000)
  if (days < 1) return t('time.today')
  if (days === 1) return t('time.yesterday')
  return t('time.daysAgoShort')(days)
}

function label(status: number) {
  if (status === -1) return t('vocab.ignored')
  if (status === 0) return t('vocab.new')
  if (status >= 5) return t('vocab.known')
  // 4 means "met often enough that you should decide" — not "almost known"
  return status >= 4 ? t('vocab.doYouKnow') : t('vocab.learning')
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
    ? t('vocab.selected')(picked.size)
    : bucket === 'all' && !q
      ? t('vocab.allOf')(total)
      : t('vocab.shown')(entries.length)

  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>{t('nav.library')}</button>
        <span>{t('vocab.summary')(total, counts.known ?? 0)}</span>
      </p>
      <h1>{t('vocab.title')}</h1>

      <p className="bar">
        {BUCKETS.map((b) => (
          <button
            key={b}
            className={b === bucket ? 'on' : ''}
            onClick={() => setBucket(b)}
          >
            {t(BUCKET_NAMES[b])} {b === 'all' ? total : (counts[b] ?? 0)}
          </button>
        ))}
        <input
          value={q}
          placeholder={t('vocab.startsWith')}
          onChange={(e) => setQ(e.target.value)}
        />
      </p>

      <p className="bar">
        <span className="meta">{t('vocab.sort')}</span>
        {SORTS.map(([key, name]) => (
          <button key={key} className={key === sort ? 'on' : ''} onClick={() => setSort(key)}>
            {t(name)}
          </button>
        ))}
      </p>

      <p className="bar">
        <span className="meta">{t('vocab.export')(scope)}</span>
        {(['anki', 'csv', 'json'] as const).map((f) => (
          <a
            key={f}
            className="button"
            href={exportUrl(lang, f, { status: bucket, q, keys: selection })}
          >
            {f === 'anki' ? t('vocab.anki') : f}
          </a>
        ))}
        {picked.size > 0 && (
          <button className="ghost" onClick={() => setPicked(new Set())}>
            {t('vocab.clearSelection')}
          </button>
        )}
      </p>

      {entries.length === 0 && <p className="muted">{t('vocab.empty')}</p>}

      <ul className="vocab">
        {entries.map((e) => (
          <li key={`${e.lemma}/${e.pos}`}>
            <input
              type="checkbox"
              checked={picked.has(key(e))}
              onChange={() => toggle(key(e))}
              aria-label={t('vocab.select')(e.lemma)}
            />
            <span className={`tok tok--${stateClass(e.status)}`}>{e.lemma}</span>
            <span className="pos">{e.pos}</span>
            <span className="meta">{label(e.status)}</span>
            {/* occurrences, not pages — the level counts pages, so these differ */}
            {e.met > 0 && <span className="meta">{t('vocab.seen')(e.met)}</span>}
            <span className="meta">{ago(e.last_seen)}</span>
            {e.note && <span className="note">{e.note}</span>}
            {/* where you met it — often more use than a definition */}
            {e.context && <span className="context">“{e.context}”</span>}
            {/* which shapes of this word you have actually met */}
            <span className="forms">
              {e.forms.length === 0 ? (
                <em className="muted">{t('vocab.noForms')}</em>
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
