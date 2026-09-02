/** Turn UD feature strings into something a learner can read.
 *
 * spaCy gives "Mood=Ind|Number=Sing|Person=3|Tense=Imp" for `marchait`; what you
 * want to see is "indicatif imparfait · 3e personne du singulier". Keyed per
 * feature, never per value — Imp is imperfect under Tense and imperative under
 * Mood.
 *
 * Which language the grammar is named in is decided by `grammarLocale` below,
 * not by a setting: see the note there.
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
      Gender: { Masc: 'masculin', Fem: 'féminin', Neut: 'neutre' },
      Definite: { Def: 'défini', Ind: 'indéfini' },
      Polarity: { Neg: 'négatif' },
      NumType: { Card: 'cardinal', Ord: 'ordinal' },
      Poss: { Yes: 'possessif' },
      Reflex: { Yes: 'réfléchi' },
      Case: {
        Nom: 'nominatif',
        Gen: 'génitif',
        Dat: 'datif',
        Acc: 'accusatif',
        Ins: 'instrumental',
        Loc: 'prépositionnel',
        Voc: 'vocatif',
      },
      Aspect: { Imp: 'imperfectif', Perf: 'perfectif' },
      Animacy: { Anim: 'animé' },
      Voice: { Pass: 'passif' },
      StyleVariant: { Short: 'forme courte' },
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
      Gender: { Masc: 'masculine', Fem: 'feminine', Neut: 'neuter' },
      Definite: { Def: 'definite', Ind: 'indefinite' },
      Polarity: { Neg: 'negative' },
      NumType: { Card: 'cardinal', Ord: 'ordinal' },
      Poss: { Yes: 'possessive' },
      Reflex: { Yes: 'reflexive' },
      Case: {
        Nom: 'nominative',
        Gen: 'genitive',
        Dat: 'dative',
        Acc: 'accusative',
        Ins: 'instrumental',
        // Called the prepositional in every Russian course a learner will meet.
        Loc: 'prepositional',
        Voc: 'vocative',
      },
      Aspect: { Imp: 'imperfective', Perf: 'perfective' },
      Animacy: { Anim: 'animate' },
      Voice: { Pass: 'passive' },
      StyleVariant: { Short: 'short form' },
    },
    personNumber: (p, n) => [p, n].filter(Boolean).join(' '),
  },
  de: {
    names: {
      VerbForm: { Inf: 'Infinitiv', Part: 'Partizip', Ger: 'Gerundium' },
      Mood: { Ind: 'Indikativ', Sub: 'Konjunktiv', Cnd: 'Konditional', Imp: 'Imperativ' },
      Tense: { Pres: 'Präsens', Imp: 'Imperfekt', Past: 'Vergangenheit', Fut: 'Futur' },
      Person: { '1': '1. Person', '2': '2. Person', '3': '3. Person' },
      Number: { Sing: 'Singular', Plur: 'Plural' },
      Gender: { Masc: 'maskulin', Fem: 'feminin', Neut: 'neutrum' },
      Definite: { Def: 'bestimmt', Ind: 'unbestimmt' },
      Polarity: { Neg: 'verneint' },
      NumType: { Card: 'Grundzahl', Ord: 'Ordnungszahl' },
      Poss: { Yes: 'Possessiv' },
      Reflex: { Yes: 'reflexiv' },
      Case: {
        Nom: 'Nominativ',
        Gen: 'Genitiv',
        Dat: 'Dativ',
        Acc: 'Akkusativ',
        Ins: 'Instrumental',
        Loc: 'Präpositiv',
        Voc: 'Vokativ',
      },
      Aspect: { Imp: 'unvollendet', Perf: 'vollendet' },
      Animacy: { Anim: 'belebt' },
      Voice: { Pass: 'Passiv' },
      StyleVariant: { Short: 'Kurzform' },
    },
    personNumber: (p, n) => [p, n].filter(Boolean).join(' '),
  },
}

/** Which language to name the grammar in.
 *
 * The language you are reading, when there is a table for it — the grammar of
 * French is discussed in French everywhere else you will meet it, and
 * "imparfait" is the word you want. Failing that, the language the interface is
 * in: Russian case names in Russian would be a wall at A2, which is exactly the
 * level this reader is for.
 *
 * Deliberately not a setting. It was going to be one (0012), and then there was
 * nothing left for the reader to decide: every combination the rule produces is
 * the one they would have chosen.
 */
export function grammarLocale(studyLang: string, ui: string): string {
  if (LOCALES[studyLang]) return studyLang
  return LOCALES[ui] ? ui : 'en'
}

// Read in the order you would say it, not the alphabetical order UD emits.
const ORDER = [
  'Gender',
  'Animacy',
  'Definite',
  'NumType',
  'Poss',
  'Reflex',
  'StyleVariant',
]

// These are said as phrases rather than listed, so they are handled by name.
const PHRASED = ['VerbForm', 'Aspect', 'Mood', 'Tense', 'Polarity', 'Voice', 'Person', 'Number', 'Case']

export function describe(morph: string, locale: string): string {
  if (!morph) return ''
  const { names, personNumber } = LOCALES[locale] ?? LOCALES.en
  const got: Record<string, string> = {}
  for (const pair of morph.split('|')) {
    const [k, v] = pair.split('=')
    // Anything unmapped is dropped rather than printed raw, which is also how a
    // feature is deliberately hidden: Voice=Act and Animacy=Inan are the unmarked
    // cases and sit on nearly every Russian word, so only their opposites appear.
    if (names[k]?.[v]) got[k] = names[k][v]
  }
  // "conditional present" is redundant — the conditional présent is just the
  // conditional. Same for the subjunctive, which reads better tense-first.
  const cnd = got.Mood === names.Mood.Cnd
  const sub = got.Mood === names.Mood.Sub
  const mood = sub ? [got.Tense, got.Mood] : cnd ? [got.Mood] : [got.Mood, got.Tense]
  const verb = [got.Aspect, got.VerbForm, ...mood, got.Polarity, got.Voice].filter(Boolean).join(' ')
  // "genitive plural", not "plural · genitive": a case-marked word is said as one
  // phrase, the same way person and number are. This is most of what there is to
  // say about a Russian noun, so getting the order wrong is very visible.
  const inflection = got.Case
    ? [got.Case, got.Number].filter(Boolean).join(' ')
    : personNumber(got.Person, got.Number)
  const rest = ORDER.filter((k) => !PHRASED.includes(k))
    .map((k) => got[k])
    .filter(Boolean)
  return [verb, inflection, ...rest].filter(Boolean).join(' · ')
}
