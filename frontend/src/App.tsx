import { useEffect, useState } from 'react'
import Reader from './Reader'
import Vocab from './Vocab'
import { deleteLesson, importText, listLessons, undoBulk } from './api'
import type { LessonSummary } from './types'

const LANG = 'fr'

type View = { at: 'library' } | { at: 'reader'; id: number } | { at: 'vocab' }

/** The shape of a text: what share of its words are new, learning, known. */
function Shape({ lesson }: { lesson: LessonSummary }) {
  const total = lesson.n_words || 1
  const parts = [
    ['new', lesson.n_new],
    ['learning', lesson.n_learning],
    ['known', lesson.n_known],
  ] as const
  return (
    <span className="shape" title={parts.map(([k, n]) => `${n} ${k}`).join(' · ')}>
      <span className="shape-bar">
        {parts.map(([k, n]) => (
          <span key={k} className={`tok--${k}`} style={{ width: `${(n / total) * 100}%` }} />
        ))}
      </span>
      <span className="meta">
        {Math.round((lesson.n_known / total) * 100)}% known · {lesson.n_new} new
      </span>
    </span>
  )
}

function Library({ onOpen, onVocab }: { onOpen: (id: number) => void; onVocab: () => void }) {
  const [lessons, setLessons] = useState<LessonSummary[]>([])
  const [text, setText] = useState('')
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState('')

  const load = () => listLessons().then(setLessons)
  useEffect(() => {
    load()
  }, [])

  const submit = async () => {
    if (!text.trim()) return
    setBusy('importing — lemmatising, this takes a moment…')
    try {
      const lesson = await importText(text, title, LANG)
      setText('')
      setTitle('')
      setBusy('')
      onOpen(lesson.id)
    } catch (e) {
      setBusy(String(e))
    }
  }

  return (
    <main>
      <p className="bar">
        <strong>LL_textreader</strong>
        <button onClick={onVocab}>vocabulary</button>
        <span className="muted">press / for commands</span>
      </p>

      <section className="import">
        <input
          value={title}
          placeholder="title (optional)"
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          value={text}
          placeholder="Paste French text, or choose a .txt file"
          onChange={(e) => setText(e.target.value)}
        />
        <p className="bar">
          <input
            type="file"
            accept=".txt,text/plain"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (!f) return
              f.text().then(setText)
              if (!title) setTitle(f.name.replace(/\.[^.]+$/, ''))
            }}
          />
          <button onClick={submit}>Import</button>
        </p>
        {busy && <p className="busy">{busy}</p>}
      </section>

      <ul className="lessons">
        {lessons.map((l) => (
          <li key={l.id}>
            <span className="row">
              <button className="link" onClick={() => onOpen(l.id)}>
                {l.title}
              </button>
              <span className="meta">
                {l.n_words} words
                {l.completed
                  ? ' · done'
                  : l.last_token > 0 &&
                    ` · ${Math.round((l.last_token / l.n_tokens) * 100)}% read`}
              </span>
              <button onClick={() => deleteLesson(l.id).then(load)}>delete</button>
            </span>
            {/* how much of it you can already read, before you open it */}
            <Shape lesson={l} />
          </li>
        ))}
      </ul>
    </main>
  )
}

/** `/` — jump anywhere without leaving the keyboard. */
function Palette({ commands, onClose }: { commands: [string, () => void][]; onClose: () => void }) {
  const [q, setQ] = useState('')
  const hits = commands.filter(([name]) => name.toLowerCase().includes(q.toLowerCase()))
  return (
    <div className="scrim" onClick={onClose}>
      <div className="palette" onClick={(e) => e.stopPropagation()}>
        <input
          autoFocus
          value={q}
          placeholder="command…"
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') onClose()
            if (e.key === 'Enter' && hits[0]) {
              onClose()
              hits[0][1]()
            }
          }}
        />
        <ul>
          {hits.map(([name, run], i) => (
            <li key={name}>
              <button
                className="link"
                onClick={() => {
                  onClose()
                  run()
                }}
              >
                {i === 0 ? '↵ ' : '  '}
                {name}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState<View>({ at: 'library' })
  const [palette, setPalette] = useState(false)
  // A bulk action can change a hundred words, and finishing the last page of a
  // lesson leaves the reader — so the offer to take it back lives up here,
  // above whichever screen you end up on.
  const [undo, setUndo] = useState<{ id: number; n: number } | null>(null)
  const [refresh, setRefresh] = useState(0)

  // `/` opens the palette from anywhere — unless you are typing.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing =
        e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement
      if (e.key === '/' && !typing) {
        e.preventDefault()
        setPalette(true)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const commands: [string, () => void][] = [
    ['library — import or open a text', () => setView({ at: 'library' })],
    ['vocabulary — everything you know', () => setView({ at: 'vocab' })],
  ]

  return (
    <>
      {undo && (
        <p className="undo">
          Marked {undo.n} words known.
          <button
            onClick={async () => {
              await undoBulk(undo.id)
              setUndo(null)
              setRefresh((n) => n + 1) // remount the view so it reloads
            }}
          >
            undo
          </button>
          <button className="ghost" onClick={() => setUndo(null)}>
            dismiss
          </button>
        </p>
      )}
      {view.at === 'library' && (
        <Library
          key={refresh}
          onOpen={(id) => setView({ at: 'reader', id })}
          onVocab={() => setView({ at: 'vocab' })}
        />
      )}
      {view.at === 'reader' && (
        <Reader
          key={refresh}
          id={view.id}
          lang={LANG}
          onBack={() => setView({ at: 'library' })}
          onBulk={setUndo}
        />
      )}
      {view.at === 'vocab' && (
        <Vocab key={refresh} lang={LANG} onBack={() => setView({ at: 'library' })} />
      )}
      {palette && <Palette commands={commands} onClose={() => setPalette(false)} />}
    </>
  )
}
