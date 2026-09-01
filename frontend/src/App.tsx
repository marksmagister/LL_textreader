import { useEffect, useState } from 'react'
import Reader from './Reader'
import Report from './Report'
import { apply, effective, stored, type Theme } from './theme'
import Legend from './Legend'
import LessonList from './LessonList'
import Vocab from './Vocab'
import { deleteLesson, fetchUrl, importText, listLessons, undoBulk } from './api'
import type { LessonSummary } from './types'

const LANG = 'fr'

/** How long the offer to take back a bulk change stays on screen. */
export const UNDO_LINGERS = 60_000

type View =
  | { at: 'library' }
  | { at: 'reader'; id: number }
  | { at: 'vocab' }
  | { at: 'legend' }

function Library({
  onOpen,
  onVocab,
  onLegend,
}: {
  onOpen: (id: number) => void
  onVocab: () => void
  onLegend: () => void
}) {
  const [lessons, setLessons] = useState<LessonSummary[]>([])
  const [text, setText] = useState('')
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState('')
  const [file, setFile] = useState('')
  const [source, setSource] = useState('')

  const load = () => listLessons().then(setLessons)
  useEffect(() => {
    load()
  }, [])

  /** Fill the boxes from a web page. Nothing is stored until you press Import,
   *  so a bad extraction is something you fix rather than something you undo. */
  const pull = async () => {
    if (!url.trim()) return
    setBusy('reading the page…')
    try {
      const got = await fetchUrl(url.trim())
      setText(got.text)
      if (!title) setTitle(got.title)
      setSource(got.source)
      setBusy('check it over, then import')
    } catch (e) {
      setBusy(String(e))
    }
  }

  const submit = async () => {
    if (!text.trim()) return
    setBusy('importing — lemmatising, this takes a moment…')
    try {
      const lesson = await importText(text, title, LANG, source)
      setText('')
      setUrl('')
      setTitle('')
      setFile('')
      setSource('')
      // Added to the list rather than opened: importing several in a row is the
      // common case, and being thrown into the reader interrupts it.
      setBusy(`added “${lesson.title}”`)
      load()
    } catch (e) {
      setBusy(String(e))
    }
  }

  return (
    <main className="library">
      <p className="bar">
        <strong>LL_textreader</strong>
        <button onClick={onVocab}>vocabulary</button>
        <button onClick={onLegend}>legend</button>
        <span className="muted">press / for commands</span>
      </p>

      <section className="import">
        {/* Above the others because it fills them in, and a separate press
            because extraction gets formatting wrong often enough that you want
            to see it before it becomes a lesson. */}
        <p className="bar">
          <input
            className="grow"
            value={url}
            placeholder="paste the address of an article…"
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && pull()}
          />
          <button disabled={!url.trim()} onClick={pull}>
            fetch
          </button>
        </p>

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
          {/* The browser's own file input cannot be styled, so it is hidden and
              the label is the button. The label still opens the picker. */}
          <label className="button">
            {file || 'choose a .txt file'}
            <input
              type="file"
              accept=".txt,text/plain"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (!f) return
                setFile(f.name)
                f.text().then(setText)
                if (!title) setTitle(f.name.replace(/\.[^.]+$/, ''))
              }}
            />
          </label>
          <button onClick={submit}>Import</button>
        </p>
        {busy && <p className="busy">{busy}</p>}
      </section>

      <LessonList
        lessons={lessons}
        onOpen={onOpen}
        onDelete={(id) => deleteLesson(id).then(load)}
        onChanged={load}
      />
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
  const [theme, setTheme] = useState<Theme>(stored)

  useEffect(() => {
    apply(theme)
  }, [theme])

  // The offer expires. It exists so a misclick is not final, and after a minute
  // you have either noticed or you have not — leaving it there turns a safety
  // net into furniture. Turning the page clears it sooner, because the reader
  // hands up a fresh value every time.
  useEffect(() => {
    if (!undo) return
    const t = setTimeout(() => setUndo(null), UNDO_LINGERS)
    return () => clearTimeout(t)
  }, [undo])

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

  // Toggling flips to the opposite of what is on screen, so the first press
  // always visibly changes something whatever the system is set to.
  const flip = () => setTheme(effective(theme) === 'dark' ? 'light' : 'dark')

  const commands: [string, () => void][] = [
    ['library — import or open a text', () => setView({ at: 'library' })],
    ['vocabulary — everything you know', () => setView({ at: 'vocab' })],
    ['legend — what the colours and keys mean', () => setView({ at: 'legend' })],
    ['dark / light — switch the theme', flip],
    ['follow the system theme', () => setTheme('system')],
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
          onLegend={() => setView({ at: 'legend' })}
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
      {view.at === 'legend' && <Legend onBack={() => setView({ at: 'library' })} />}
      {palette && <Palette commands={commands} onClose={() => setPalette(false)} />}
      <Report lessonId={view.at === 'reader' ? view.id : undefined} />
      <button className="theme-tab" onClick={flip} title="light or dark">
        {effective(theme) === 'dark' ? 'light mode' : 'dark mode'}
      </button>
    </>
  )
}
