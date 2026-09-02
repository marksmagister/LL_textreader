/** Turn UD feature strings into something a learner can read.
 *
 * spaCy gives "Mood=Ind|Number=Sing|Person=3|Tense=Imp" for `marchait`; what you
 * want to see is "indicatif imparfait · 3e personne du singulier". Keyed per
 * feature, never per value — Imp is imperfect under Tense and imperative under
 * Mood.
 *
 * Named in the language you are reading, on the maintainer's instruction: the
 * grammar of French is discussed in French everywhere else you will meet it.
 * English is kept below because it is the second locale that proves the shape is
 * right — a settings switch only has to change LOCALE.
 */
interface Locale {
  names: Record<string, Record<string, string>>
  /** "3rd person singular" in English, "3e personne du singulier" in French. */
  personNumber: (person?: string, number?: string) => string
}

const LOCALES: Record<string, Locale> = {
  fr: {
    names: {
      VerbForm: { Inf: 'infinitif', Part: 'participe', Ger: 'gérondif' },
      Mood: { Ind: 'indicatif', Sub: 'subjonctif', Cnd: 'conditionnel', Imp: 'impératif' },
      Tense: { Pres: 'présent', Imp: 'imparfait', Past: 'passé', Fut: 'futur' },
      Person: { '1': '1re personne', '2': '2e personne', '3': '3e personne' },
      Number: { Sing: 'singulier', Plur: 'pluriel' },
      Gender: { Masc: 'masculin', Fem: 'féminin' },
      Definite: { Def: 'défini', Ind: 'indéfini' },
      Polarity: { Neg: 'négatif' },
      NumType: { Card: 'cardinal', Ord: 'ordinal' },
      Poss: { Yes: 'possessif' },
      Reflex: { Yes: 'réfléchi' },
    },
    personNumber: (p, n) => (p && n ? `${p} du ${n}` : p || n || ''),
  },
  en: {
    names: {
      VerbForm: { Inf: 'infinitive', Part: 'participle', Ger: 'gerund' },
      Mood: { Ind: 'indicative', Sub: 'subjunctive', Cnd: 'conditional', Imp: 'imperative' },
      Tense: { Pres: 'present', Imp: 'imperfect', Past: 'past', Fut: 'future' },
      Person: { '1': '1st person', '2': '2nd person', '3': '3rd person' },
      Number: { Sing: 'singular', Plur: 'plural' },
      Gender: { Masc: 'masculine', Fem: 'feminine' },
      Definite: { Def: 'definite', Ind: 'indefinite' },
      Polarity: { Neg: 'negative' },
      NumType: { Card: 'cardinal', Ord: 'ordinal' },
      Poss: { Yes: 'possessive' },
      Reflex: { Yes: 'reflexive' },
    },
    personNumber: (p, n) => [p, n].filter(Boolean).join(' '),
  },
}

/** Which language the grammar is named in. French, because you are reading
 *  French and "imparfait" is the word you will meet everywhere else.
 *
 *  This is the only line the settings screen has to reach when it lands with
 *  the Russian and Italian work — see docs/decisions/0012. Deliberately not a
 *  setting yet: there is nothing to switch between until a second language of
 *  study exists. */
export const LOCALE = 'fr'

const NAMES = LOCALES[LOCALE].names

// Read in the order you would say it, not the alphabetical order UD emits.
const ORDER = [
  'VerbForm',
  'Mood',
  'Tense',
  'Polarity',
  'Person',
  'Number',
  'Gender',
  'Definite',
  'NumType',
  'Poss',
  'Reflex',
]

export function describe(morph: string): string {
  if (!morph) return ''
  const got: Record<string, string> = {}
  for (const pair of morph.split('|')) {
    const [k, v] = pair.split('=')
    if (NAMES[k]?.[v]) got[k] = NAMES[k][v]
  }
  // "3rd person singular" reads better than "3rd person · singular", and the
  // French runs it together differently again.
  const person = LOCALES[LOCALE].personNumber(got.Person, got.Number)
  // "conditional present" is redundant — the conditional présent is just the
  // conditional. Same for the subjunctive, which reads better tense-first.
  const cnd = got.Mood === NAMES.Mood.Cnd
  const sub = got.Mood === NAMES.Mood.Sub
  const mood = sub ? [got.Tense, got.Mood] : cnd ? [got.Mood] : [got.Mood, got.Tense]
  const verb = [got.VerbForm, ...mood, got.Polarity].filter(Boolean).join(' ')
  const rest = ORDER.filter((k) => !['VerbForm', 'Mood', 'Tense', 'Polarity', 'Person', 'Number'].includes(k))
    .map((k) => got[k])
    .filter(Boolean)
  return [verb, person, ...rest].filter(Boolean).join(' · ')
}
