import { useEffect, useState } from 'react'
import Reader from './Reader'
import { deleteLesson, importText, listLessons } from './api'
import type { LessonSummary } from './types'

function Library({ onOpen }: { onOpen: (id: number) => void }) {
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
      const lesson = await importText(text, title, 'fr')
      setText('')
      setTitle('')
      setBusy('')
      onOpen(lesson.id)
    } catch (e) {
      setBusy(String(e))
    }
  }

  const openFile = (file: File) => {
    file.text().then((t) => {
      setText(t)
      if (!title) setTitle(file.name.replace(/\.[^.]+$/, ''))
    })
  }

  return (
    <main>
      <h1>LL_textreader</h1>

      <section className="import">
        <input value={title} placeholder="title (optional)" onChange={(e) => setTitle(e.target.value)} />
        <textarea
          value={text}
          placeholder="Paste French text, or choose a .txt file"
          onChange={(e) => setText(e.target.value)}
        />
        <p className="bar">
          <input
            type="file"
            accept=".txt,text/plain"
            onChange={(e) => e.target.files?.[0] && openFile(e.target.files[0])}
          />
          <button onClick={submit}>Import</button>
        </p>
        {busy && <p className="busy">{busy}</p>}
      </section>

      <ul className="lessons">
        {lessons.map((l) => (
          <li key={l.id}>
            <button className="link" onClick={() => onOpen(l.id)}>
              {l.title}
            </button>
            <span className="meta">{l.n_words} words</span>
            <button onClick={() => deleteLesson(l.id).then(load)}>delete</button>
          </li>
        ))}
      </ul>
    </main>
  )
}

export default function App() {
  const [open, setOpen] = useState<number | null>(null)
  return open === null ? (
    <Library onOpen={setOpen} />
  ) : (
    <Reader id={open} onBack={() => setOpen(null)} />
  )
}
