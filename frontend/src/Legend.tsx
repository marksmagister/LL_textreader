import { t } from './i18n'

/** What the colours mean and which key does what.
 *
 * Shown, not described: every sample below carries the same CSS class the reader
 * uses, so the legend cannot drift from the thing it explains.
 *
 * The samples are in the language you are reading. A French sentence explaining
 * the colours to someone learning Russian teaches them nothing, and the
 * novel-form state in particular is only convincing in a language where forms
 * actually change.
 */

/** A demonstration sentence, cut into the five states, and the five words the
 *  parts list uses. Each entry is [state, text] and they are concatenated, so
 *  the sentence reads normally while every word carries its own colour. */
const SAMPLES: Record<string, { sentence: Array<[string, string]>; words: string[] }> = {
  fr: {
    sentence: [
      ['known', 'Le '],
      ['learning', 'brouillard'],
      ['known', ' se '],
      ['novel-form-learning', 'levait'],
      ['known', ' sur le '],
      ['new', 'quai'],
      ['known', ', et nous '],
      ['novel-form', 'marcherons'],
      ['known', ' vers la '],
      ['review', 'lanterne'],
      ['known', '.'],
    ],
    // in STATES order; the two dashed ones sit together so the contrast shows
    words: ['quai', 'marcherons', 'levait', 'brouillard', 'lanterne', 'maison'],
  },
  ru: {
    sentence: [
      ['known', 'На '],
      ['learning', 'улице'],
      ['known', ' было темно, и мы '],
      ['novel-form', 'пошли'],
      ['known', ' к '],
      ['new', 'реке'],
      ['known', ', где '],
      ['novel-form-learning', 'горел'],
      ['known', ' '],
      ['review', 'фонарь'],
      ['known', '.'],
    ],
    words: ['реке', 'пошли', 'горел', 'улице', 'фонарь', 'дом'],
  },
  it: {
    sentence: [
      ['known', 'La '],
      ['learning', 'nebbia'],
      ['known', ' '],
      ['novel-form-learning', 'saliva'],
      ['known', ' sul '],
      ['new', 'molo'],
      ['known', ', e noi '],
      ['novel-form', 'cammineremo'],
      ['known', ' verso la '],
      ['review', 'lanterna'],
      ['known', '.'],
    ],
    words: ['molo', 'cammineremo', 'saliva', 'nebbia', 'lanterna', 'casa'],
  },
}

// The two dashed states are adjacent on purpose: the dash means "shape you have
// not met" in both, and the only difference is whose the word is. Side by side,
// that reads in one glance; separated, it looks like two unrelated things.
const STATES = [
  'new',
  'novel-form',
  'novel-form-learning',
  'learning',
  'review',
  'known',
] as const
const MEANINGS = [
  'legend.new',
  'legend.novelForm',
  'legend.novelFormLearning',
  'legend.learning',
  'legend.review',
  'legend.known',
] as const

const KEYS: Array<[string, 'key.tab' | 'key.shiftTab' | 'key.1' | 'key.k' | 'key.i'
  | 'key.shiftK' | 'key.sentence' | 'key.enter' | 'key.esc' | 'key.o' | 'key.space'
  | 'key.slash']> = [
  ['Tab', 'key.tab'],
  ['⇧ Tab', 'key.shiftTab'],
  ['1', 'key.1'],
  ['k', 'key.k'],
  ['i', 'key.i'],
  ['⇧ K', 'key.shiftK'],
  ['j  ↓  ↑', 'key.sentence'],
  ['Enter', 'key.enter'],
  ['Esc', 'key.esc'],
  ['o', 'key.o'],
  ['Space', 'key.space'],
  ['/', 'key.slash'],
]

export default function Legend({ lang, onBack }: { lang: string; onBack: () => void }) {
  const sample = SAMPLES[lang] ?? SAMPLES.fr
  const buttons: Array<[string, 'btn.translate' | 'btn.markOnClick' | 'btn.markPage'
    | 'btn.next' | 'btn.undo' | 'btn.report']> = [
    [t('lang.en'), 'btn.translate'],
    [t('reader.markOnClick'), 'btn.markOnClick'],
    [t('reader.markPage'), 'btn.markPage'],
    [t('reader.next'), 'btn.next'],
    [t('undo.undo'), 'btn.undo'],
    [t('report.tab'), 'btn.report'],
  ]

  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>{t('nav.library')}</button>
      </p>

      <h1>{t('legend.title')}</h1>

      {/* The assembled picture first, the parts list after. */}
      <p className="legend-demo">
        {sample.sentence.map(([state, text], i) => (
          <span key={i} className={`tok tok--${state}`}>
            {text}
          </span>
        ))}
      </p>

      <ul className="legend">
        {STATES.map((state, i) => (
          <li key={state}>
            <span className={`tok tok--${state}`}>{sample.words[i]}</span>
            <span>{t(MEANINGS[i])}</span>
          </li>
        ))}
      </ul>

      <p className="muted">{t('legend.blueNote')}</p>

      <h1>{t('legend.loopTitle')}</h1>
      <p className="legend-loop">
        <kbd>Tab</kbd> → <kbd>k</kbd> / <kbd>1</kbd> → <kbd>Tab</kbd>
      </p>
      <p className="muted">{t('legend.loopNote')}</p>

      <h1>{t('legend.keysTitle')}</h1>
      <ul className="legend keys-list">
        {KEYS.map(([key, what]) => (
          <li key={key}>
            <kbd>{key}</kbd>
            <span>{t(what)}</span>
          </li>
        ))}
      </ul>

      <h1>{t('legend.buttonsTitle')}</h1>
      <ul className="legend keys-list">
        {buttons.map(([label, what]) => (
          <li key={label}>
            <span className="legend-btn">{label}</span>
            <span>{t(what)}</span>
          </li>
        ))}
      </ul>

      <h1>{t('legend.surprisesTitle')}</h1>
      <ul className="legend-notes">
        <li>
          {t('legend.surprise1a')}
          <em>{t('legend.surprise1b')}</em>
          {t('legend.surprise1c')}
          <span className="tok tok--known">{sample.words[1]}</span>
          {t('legend.surprise1d')}
        </li>
        <li>{t('legend.surprise2')}</li>
      </ul>
    </main>
  )
}
