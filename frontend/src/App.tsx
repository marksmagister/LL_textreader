import { useEffect, useState } from 'react'
import type { Token, TokenState } from './types'

/** Placeholder until the lessons API exists — shows the four render states. */
const DEMO: Array<[string, TokenState]> = [
  ['Il', 'known'], ['marchait', 'novel-form'], ['le', 'known'], ['long', 'known'],
  ['du', 'known'], ['quai', 'learning'], ['et', 'known'], ['regardait', 'novel-form'],
  ['le', 'known'], ['reflet', 'new'], ['dans', 'known'], ["l'eau", 'known'],
]

function Word({ token }: { token: Token }) {
  return <span className={`tok tok--${token.state}`}>{token.surface}</span>
}

export default function App() {
  const [health, setHealth] = useState<string>('…')

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setHealth(`${d.status} · ${d.languages.join(', ')}`))
      .catch(() => setHealth('backend not running'))
  }, [])

  const tokens: Token[] = DEMO.map(([surface, state], idx) => ({
    idx, surface, lemma: null, pos: null, charStart: 0, charEnd: 0, state,
  }))

  return (
    <main>
      <p style={{ fontSize: '0.8rem', opacity: 0.5 }}>LL_textreader — api: {health}</p>
      <p>
        {tokens.map((t, i) => (
          <span key={t.idx}>
            {i > 0 && ' '}
            <Word token={t} />
          </span>
        ))}
      </p>
    </main>
  )
}
