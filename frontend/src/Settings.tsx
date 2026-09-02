import { grammarLocale } from './morph'
import { languageName, t, UI_LOCALES, uiLocale } from './i18n'

/** What you are reading, and what the buttons are written in.
 *
 * Two settings, deliberately not one. A German speaker reading French wants a
 * German interface and French text, and welding the two together would make
 * that impossible — 0012 is emphatic about it, and the same argument will apply
 * to the translation target when it arrives.
 *
 * The third thing 0012 wanted here — which language the grammar is named in —
 * is not a setting. It follows from the other two (see `grammarLocale`), and
 * every combination the rule produces is the one you would have picked, so the
 * screen explains it instead of asking.
 */
export default function Settings({
  languages,
  lang,
  onLang,
  onUi,
  onBack,
}: {
  languages: string[]
  lang: string
  onLang: (lang: string) => void
  onUi: (locale: string) => void
  onBack: () => void
}) {
  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>{t('nav.library')}</button>
      </p>

      <h1>{t('settings.title')}</h1>

      <section className="setting">
        <h2>{t('settings.study')}</h2>
        <p className="bar">
          {languages.map((code) => (
            <button
              key={code}
              className={code === lang ? 'on' : ''}
              onClick={() => onLang(code)}
            >
              {languageName(code)}
            </button>
          ))}
        </p>
        <p className="muted">{t('settings.studyHint')}</p>
      </section>

      <section className="setting">
        <h2>{t('settings.interface')}</h2>
        <p className="bar">
          {UI_LOCALES.map((code) => (
            <button
              key={code}
              className={code === uiLocale() ? 'on' : ''}
              onClick={() => onUi(code)}
            >
              {languageName(code)}
            </button>
          ))}
        </p>
        <p className="muted">{t('settings.interfaceHint')}</p>
        <p className="muted">
          {t('settings.grammar')(languageName(grammarLocale(lang, uiLocale())))}
        </p>
      </section>
    </main>
  )
}
