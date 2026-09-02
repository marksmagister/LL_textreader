import { grammarLocale } from './morph'
import { languageName, t, UI_LOCALES, uiLocale } from './i18n'

/** The languages you are learning, and what the buttons are written in.
 *
 * Two settings, deliberately not one. A German speaker reading French wants a
 * German interface and French text, and welding the two together would make that
 * impossible — 0012 is emphatic about it, and the same argument will apply to the
 * translation target when it arrives.
 *
 * The third thing 0012 wanted here — which language the grammar is named in — is
 * not a setting. It follows from the other two (see `grammarLocale`), and every
 * combination the rule produces is the one you would have picked, so the screen
 * explains it instead of asking.
 *
 * This is also where the header dropdown's first group is curated. Nobody learns
 * every language a server offers, so the short list is yours to keep and the rest
 * stay available without being in the way.
 */
export default function Settings({
  languages,
  learning,
  lang,
  onLang,
  onLearning,
  onUi,
  onBack,
}: {
  /** Everything this server has a model for, from /api/health. */
  languages: string[]
  /** The ones you are learning — the header dropdown's first group. */
  learning: string[]
  lang: string
  onLang: (lang: string) => void
  onLearning: (langs: string[]) => void
  onUi: (locale: string) => void
  onBack: () => void
}) {
  const rest = languages.filter((code) => !learning.includes(code))

  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>{t('nav.library')}</button>
      </p>

      <h1>{t('settings.title')}</h1>

      <section className="setting">
        <h2>{t('settings.study')}</h2>
        <ul className="langs-list">
          {learning.map((code) => (
            <li key={code}>
              <span className={`lang-name${code === lang ? ' on' : ''}`}>
                {languageName(code)}
              </span>
              {code === lang ? (
                <span className="meta">{t('settings.reading')}</span>
              ) : (
                <>
                  <button className="ghost" onClick={() => onLang(code)}>
                    {t('settings.read')}
                  </button>
                  {/* The one you are reading has no remove button: taking it away
                      would leave the library showing a language you are not in. */}
                  <button
                    className="ghost"
                    onClick={() => onLearning(learning.filter((c) => c !== code))}
                  >
                    {t('settings.drop')}
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
        <p className="muted">{t('settings.studyHint')}</p>
      </section>

      <section className="setting">
        <h2>{t('settings.available')}</h2>
        {rest.length === 0 ? (
          <p className="muted">{t('settings.allYours')}</p>
        ) : (
          <ul className="langs-list">
            {rest.map((code) => (
              <li key={code}>
                <span className="lang-name">{languageName(code)}</span>
                <button className="ghost" onClick={() => onLearning([...learning, code])}>
                  {t('settings.take')}
                </button>
              </li>
            ))}
          </ul>
        )}
        <p className="muted">{t('settings.availableHint')}</p>
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
