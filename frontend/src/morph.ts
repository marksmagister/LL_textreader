/** Turn UD feature strings into something a learner can read.
 *
 * spaCy gives "Mood=Ind|Number=Sing|Person=3|Tense=Imp" for `marchait`; what you
 * want to see is "indicative imperfect · 3rd person singular". Keyed per feature,
 * never per value — Imp is imperfect under Tense and imperative under Mood.
 */
const NAMES: Record<string, Record<string, string>> = {
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
}

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
  // "3rd person singular" reads better than "3rd person · singular"
  const person = [got.Person, got.Number].filter(Boolean).join(' ')
  const verb = [got.VerbForm, got.Mood, got.Tense, got.Polarity].filter(Boolean).join(' ')
  const rest = ORDER.filter((k) => !['VerbForm', 'Mood', 'Tense', 'Polarity', 'Person', 'Number'].includes(k))
    .map((k) => got[k])
    .filter(Boolean)
  return [verb, person, ...rest].filter(Boolean).join(' · ')
}
