import { useEffect, useState } from 'react'
import Reader from './Reader'
import Report from './Report'
import { apply, effective, stored as storedTheme, type Theme } from './theme'
import { mine as myLangs, remember as rememberLang, rememberMine, stored as storedLang } from './lang'
import { languageName, setUiLocale, t, uiLocale } from './i18n'
import Legend from './Legend'
import LessonList from './LessonList'
import Settings from './Settings'
import Vocab from './Vocab'
import {
  accountExportUrl,
  addStarters,
  deleteAccount,
  deleteLesson,
  fetchUrl,
  importText,
  listLessons,
  listStarters,
  NotSignedIn,
  signOut,
  undoBulk,
  whoami,
} from './api'
import SignIn from './SignIn'
import type { Me } from './api'
import type { LessonSummary } from './types'

/** How long the offer to take back a bulk change stays on screen. */
export const UNDO_LINGERS = 60_000

type View =
  | { at: 'library' }
  | { at: 'reader'; id: number; page?: number }
  | { at: 'vocab' }
  | { at: 'legend' }
  | { at: 'settings' }

function Library({
  lang,
  yours,
  rest,
  onLang,
  onOpen,
  onVocab,
  onLegend,
  onSettings,
}: {
  lang: string
  /** The languages you are learning; the dropdown's first group. */
  yours: string[]
  /** Everything else the server offers; the second group. */
  rest: string[]
  onLang: (lang: string) => void
  onOpen: (id: number) => void
  onVocab: () => void
  onLegend: () => void
  onSettings: () => void
}) {
  const [lessons, setLessons] = useState<LessonSummary[]>([])
  const [offered, setOffered] = useState(0)
  const [text, setText] = useState('')
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState('')
  const [file, setFile] = useState('')
  const [source, setSource] = useState('')

  // Both keyed on the language: switching it is switching library.
  const load = () => listLessons(lang).then(setLessons)
  useEffect(() => {
    load()
    listStarters(lang)
      .then((all) => setOffered(all.filter((s) => !s.imported).length))
      .catch(() => setOffered(0))
  }, [lang])

  /** Fill the boxes from a web page. Nothing is stored until you press Import,
   *  so a bad extraction is something you fix rather than something you undo. */
  const pull = async () => {
    if (!url.trim()) return
    setBusy(t('import.reading'))
    try {
      const got = await fetchUrl(url.trim())
      setText(got.text)
      if (!title) setTitle(got.title)
      setSource(got.source)
      setBusy(t('import.check'))
    } catch (e) {
      setBusy(String(e))
    }
  }

  const submit = async () => {
    if (!text.trim()) return
    setBusy(t('import.importing'))
    try {
      const lesson = await importText(text, title, lang, source)
      setText('')
      setUrl('')
      setTitle('')
      setFile('')
      setSource('')
      // Added to the list rather than opened: importing several in a row is the
      // common case, and being thrown into the reader interrupts it.
      setBusy(t('import.added')(lesson.title))
      load()
    } catch (e) {
      setBusy(String(e))
    }
  }

  /** The starter texts. Offered only while there are any you don't have, so the
   *  button leaves once it has done its job rather than sitting there for ever. */
  const start = async () => {
    setBusy(t('starters.adding'))
    try {
      const made = await addStarters(lang)
      setBusy(made.length ? t('starters.added')(made.length) : '')
      setOffered(0)
      load()
    } catch (e) {
      setBusy(String(e))
    }
  }

  return (
    <main className="library">
      <p className="bar">
        <strong>LL_textreader</strong>
        {/* The language you are reading, where you can see it and change it
            without going anywhere: it is the one thing here that changes daily.
            A dropdown rather than a row of buttons, because nobody learns every
            language a server offers and a row stops being a control at about
            four — so yours come first and the rest are one group further down. */}
        <select
          className="lang-select"
          title={t('lang.pick')}
          value={lang}
          onChange={(e) => onLang(e.target.value)}
        >
          <optgroup label={t('lang.yours')}>
            {yours.map((code) => (
              <option key={code} value={code}>
                {languageName(code)}
              </option>
            ))}
          </optgroup>
          {rest.length > 0 && (
            <optgroup label={t('lang.available')}>
              {rest.map((code) => (
                <option key={code} value={code}>
                  {languageName(code)}
                </option>
              ))}
            </optgroup>
          )}
        </select>
        <button onClick={onVocab}>{t('nav.vocabulary')}</button>
        <button onClick={onLegend}>{t('nav.legend')}</button>
        <button onClick={onSettings}>{t('nav.settings')}</button>
        <span className="muted">{t('app.paletteHint')}</span>
      </p>

      <section className="import">
        {/* Above the others because it fills them in, and a separate press
            because extraction gets formatting wrong often enough that you want
            to see it before it becomes a lesson. */}
        <p className="bar">
          <input
            className="grow"
            value={url}
            placeholder={t('import.urlPlaceholder')}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && pull()}
          />
          <button disabled={!url.trim()} onClick={pull}>
            {t('import.fetch')}
          </button>
        </p>

        <input
          value={title}
          placeholder={t('import.titlePlaceholder')}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          value={text}
          placeholder={t('import.textPlaceholder')(languageName(lang))}
          onChange={(e) => setText(e.target.value)}
        />
        <p className="bar">
          {/* The browser's own file input cannot be styled, so it is hidden and
              the label is the button. The label still opens the picker. */}
          <label className="button">
            {file || t('import.file')}
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
          <button onClick={submit}>{t('import.import')}</button>
        </p>
        {busy && <p className="busy">{busy}</p>}
      </section>

      {offered > 0 && (
        <p className="bar starters">
          <button onClick={start}>{t('starters.add')(offered)}</button>
          <span className="muted">{t('starters.hint')}</span>
        </p>
      )}

      <LessonList
        lessons={lessons}
        language={languageName(lang)}
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
          placeholder={t('palette.placeholder')}
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

/** Sign out, export, or leave. Small enough to live here; it is three buttons
 *  and a confirmation, and a file of its own would be ceremony. */
/** The account menu, and the home for the two controls that used to float in the
 *  bottom corners. Both were pinned over the word panel — harmless in the margins
 *  of a wide screen, and squarely on top of its buttons on a phone. They are not
 *  things you reach for while reading a sentence, so they belong behind a menu;
 *  the palette still opens both without the mouse (0004). */
function Account({
  me,
  onSignedOut,
  themeLabel,
  onFlipTheme,
  onReport,
}: {
  me: Me
  onSignedOut: () => void
  themeLabel: string
  onFlipTheme: () => void
  onReport: () => void
}) {
  const [open, setOpen] = useState(false)
  const [confirming, setConfirming] = useState(false)

  // Clicking anywhere else closes it, which is what every other menu does and
  // what people try first — pressing the name again was the only way out.
  useEffect(() => {
    if (!open) return
    const away = (e: MouseEvent) => {
      if (!(e.target as Element)?.closest?.('.account')) setOpen(false)
    }
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', away)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('mousedown', away)
      document.removeEventListener('keydown', esc)
    }
  }, [open])

  if (!me.user) return null
  return (
    <div className="account">
      <button className="ghost" onClick={() => setOpen(!open)}>
        {me.user.name || me.user.email || 'account'}
      </button>
      {open && (
        <div className="account-menu">
          <p className="meta">{me.user.email}</p>
          {/* On a phone these two live here; on a desktop they are back in the
              bottom corners where they were, and CSS picks. Rendered in both
              places rather than switched in JS, so there is no width in the
              component and no resize listener. */}
          <button
            className="only-narrow"
            onClick={() => {
              setOpen(false)
              onFlipTheme()
            }}
          >
            {themeLabel}
          </button>
          <button
            className="only-narrow"
            onClick={() => {
              setOpen(false)
              onReport()
            }}
          >
            {t('report.tab')}
          </button>
          {/* A plain link so Content-Disposition does the saving. */}
          <a className="button" href={accountExportUrl()}>
            export everything
          </a>
          <button
            onClick={async () => {
              await signOut()
              onSignedOut()
            }}
          >
            sign out
          </button>
          {confirming ? (
            <p className="warn">
              This deletes your texts and every word you have learned. It cannot be undone —
              export first if you might want it.
              <button
                onClick={async () => {
                  await deleteAccount()
                  onSignedOut()
                }}
              >
                delete it all
              </button>
              <button className="ghost" onClick={() => setConfirming(false)}>
                keep it
              </button>
            </p>
          ) : (
            <button className="ghost" onClick={() => setConfirming(true)}>
              delete account
            </button>
          )}
          <p className="meta">
            <a href="/privacy">privacy</a> · <a href="/terms">terms</a>
          </p>
        </div>
      )}
    </div>
  )
}

export default function App() {
  // undefined while we are still asking. Rendering the reader before the answer
  // arrives would flash the library at somebody who is not signed in.
  const [me, setMe] = useState<Me | undefined>()
  const [view, setView] = useState<View>({ at: 'library' })
  const [palette, setPalette] = useState(false)
  const [reporting, setReporting] = useState(false)
  // A bulk action can change a hundred words, and finishing the last page of a
  // lesson leaves the reader — so the offer to take it back lives up here,
  // above whichever screen you end up on.
  const [undo, setUndo] = useState<{ id: number; n: number } | null>(null)
  const [refresh, setRefresh] = useState(0)
  const [theme, setTheme] = useState<Theme>(storedTheme)
  const [lang, setLang] = useState(storedLang)
  // Held as state only so that changing it re-renders; `t` reads the module.
  const [ui, setUi] = useState(uiLocale)
  const [languages, setLanguages] = useState<string[]>([lang])
  const [learning, setLearning] = useState<string[]>(myLangs)

  useEffect(() => {
    apply(theme)
  }, [theme])

  useEffect(() => {
    whoami().then(setMe)
  }, [])

  // A session can expire between one page turn and the next, so any call may
  // come back 401. Catching it here — once, at the window — turns that into the
  // sign-in screen rather than an error message on whatever screen you were on.
  useEffect(() => {
    const onRejection = (e: PromiseRejectionEvent) => {
      if (e.reason instanceof NotSignedIn) {
        e.preventDefault()
        setMe((m) => (m ? { ...m, user: null } : m))
      }
    }
    window.addEventListener('unhandledrejection', onRejection)
    return () => window.removeEventListener('unhandledrejection', onRejection)
  }, [])

  // What this server can actually read. `whoami` already carries it — it is the
  // one call that answers before you are signed in — so the menu costs no extra
  // round trip. Until it answers, the menu is just the language you had last
  // time, which is the one you are about to use anyway.
  useEffect(() => {
    if (me?.languages?.length) setLanguages(me.languages)
  }, [me])

  // What the dropdown shows, in two groups. Anything you are learning that this
  // server cannot read is dropped rather than offered — and the language you are
  // reading is always in the first group, even if it got there by being picked
  // out of the second one a moment ago.
  const yours = languages.filter((code) => learning.includes(code) || code === lang)
  const rest = languages.filter((code) => !yours.includes(code))

  const chooseLang = (next: string) => {
    setLang(next)
    rememberLang(next)
    // Reading something is how a language gets into your list. Picking one out
    // of "also available" is the moment you started learning it.
    if (!learning.includes(next)) keepLangs([...learning, next])
  }

  const keepLangs = (next: string[]) => {
    setLearning(next)
    rememberMine(next)
  }

  const chooseUi = (next: string) => {
    setUiLocale(next)
    setUi(next) // nothing is memoised, so this re-renders the whole tree in the new language
  }

  // The offer expires. It exists so a misclick is not final, and after a minute
  // you have either noticed or you have not — leaving it there turns a safety
  // net into furniture. Turning the page clears it sooner, because the reader
  // hands up a fresh value every time.
  useEffect(() => {
    if (!undo) return
    const timer = setTimeout(() => setUndo(null), UNDO_LINGERS)
    return () => clearTimeout(timer)
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
    [t('cmd.library'), () => setView({ at: 'library' })],
    [t('cmd.vocab'), () => setView({ at: 'vocab' })],
    [t('cmd.legend'), () => setView({ at: 'legend' })],
    [t('cmd.settings'), () => setView({ at: 'settings' })],
    [t('cmd.theme'), flip],
    // Both of these lost their floating tab; the palette keeps them one press
    // away without the mouse, which is what 0004 asks of everything here.
    [t('report.tabTitle'), () => setReporting(true)],
    [t('cmd.system'), () => setTheme('system')],
    // Switching language is a command too, so the core loop never needs the
    // mouse — the same argument as 0004 makes for everything else. Only the ones
    // you are learning: the palette is for what you do daily.
    ...yours.map(
      (code): [string, () => void] => [languageName(code), () => chooseLang(code)],
    ),
  ]

  if (!me) return <main>…</main>
  if (!me.user) {
    // The callback sends failures back here as ?error=, since it is reached by
    // the browser navigating and a JSON error would be a dead end.
    const error = new URLSearchParams(window.location.search).get('error') ?? undefined
    return <SignIn me={me} error={error} />
  }

  return (
    // Keyed on the interface language so that anything holding a translated
    // string in its own state is rebuilt rather than left in the old one.
    <div key={ui}>
      <Account
        me={me}
        onSignedOut={() => setMe({ ...me, user: null })}
        themeLabel={effective(theme) === 'dark' ? t('app.themeToLight') : t('app.themeToDark')}
        onFlipTheme={flip}
        onReport={() => setReporting(true)}
      />
      {undo && (
        <p className="undo">
          {t('undo.marked')(undo.n)}
          <button
            onClick={async () => {
              await undoBulk(undo.id)
              setUndo(null)
              setRefresh((n) => n + 1) // remount the view so it reloads
            }}
          >
            {t('undo.undo')}
          </button>
          <button className="ghost" onClick={() => setUndo(null)}>
            {t('undo.dismiss')}
          </button>
        </p>
      )}
      {view.at === 'library' && (
        <Library
          key={refresh}
          lang={lang}
          yours={yours}
          rest={rest}
          onLang={chooseLang}
          onOpen={(id) => setView({ at: 'reader', id })}
          onVocab={() => setView({ at: 'vocab' })}
          onLegend={() => setView({ at: 'legend' })}
          onSettings={() => setView({ at: 'settings' })}
        />
      )}
      {view.at === 'reader' && (
        <Reader
          key={refresh}
          id={view.id}
          onBack={() => setView({ at: 'library' })}
          onBulk={setUndo}
          // So "the colours are wrong here" arrives with a page number. The
          // column has always existed; nothing ever filled it.
          onPage={(page) => setView((v) => (v.at === 'reader' ? { ...v, page } : v))}
        />
      )}
      {view.at === 'vocab' && (
        <Vocab key={refresh} lang={lang} onBack={() => setView({ at: 'library' })} />
      )}
      {view.at === 'legend' && (
        <Legend lang={lang} onBack={() => setView({ at: 'library' })} />
      )}
      {view.at === 'settings' && (
        <Settings
          languages={languages}
          learning={yours}
          lang={lang}
          onLang={chooseLang}
          onLearning={keepLangs}
          onUi={chooseUi}
          onBack={() => setView({ at: 'library' })}
        />
      )}
      {/* The corner tabs, for screens with corners to spare. Below 640px they
          are hidden and the account menu carries them instead: they used to sit
          on top of the word panel's buttons on a phone, which is what took them
          out of the corners in the first place. */}
      <button className="theme-tab only-wide" onClick={flip} title={t('app.themeTitle')}>
        {effective(theme) === 'dark' ? t('app.themeToLight') : t('app.themeToDark')}
      </button>
      <button
        className="report-tab only-wide"
        onClick={() => setReporting(true)}
        title={t('report.tabTitle')}
      >
        {t('report.tab')}
      </button>
      {palette && <Palette commands={commands} onClose={() => setPalette(false)} />}
      {reporting && (
        <Report
          lessonId={view.at === 'reader' ? view.id : undefined}
          page={view.at === 'reader' ? view.page : undefined}
          onClose={() => setReporting(false)}
        />
      )}
    </div>
  )
}
