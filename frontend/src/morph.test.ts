import { describe as group, expect, test } from 'vitest'
import { describe, grammarLocale } from './morph'

group('reading UD features back as grammar', () => {
  test('Imp means different things under Tense and Mood', () => {
    // The trap this module exists to avoid: imperfect vs imperative.
    expect(describe('Mood=Ind|Tense=Imp|Person=3|Number=Sing', 'fr')).toContain('imparfait')
    expect(describe('Mood=Imp|Person=2|Number=Sing', 'fr')).toContain('impératif')
  })

  test('person and number read as one phrase', () => {
    expect(describe('Mood=Ind|Tense=Imp|Person=3|Number=Sing', 'fr')).toBe(
      'indicatif imparfait · 3e personne du singulier',
    )
  })

  test('the conditional is not called "conditional present"', () => {
    expect(describe('Mood=Cnd|Tense=Pres|Person=1|Number=Sing', 'fr')).toBe(
      'conditionnel · 1re personne du singulier',
    )
  })

  test('the subjunctive reads tense first', () => {
    expect(describe('Mood=Sub|Tense=Pres|Person=3|Number=Sing', 'fr')).toBe(
      'présent subjonctif · 3e personne du singulier',
    )
  })

  test('nouns get gender and number', () => {
    expect(describe('Gender=Fem|Number=Plur', 'fr')).toBe('pluriel · féminin')
  })

  test('nothing to say stays silent rather than inventing', () => {
    expect(describe('', 'fr')).toBe('')
    expect(describe('Typo=Yes|NounClass=Wol3', 'fr')).toBe('')
  })

  test('unknown values are dropped, not printed raw', () => {
    expect(describe('Tense=Fut|Mood=Zzz', 'fr')).toBe('futur')
  })
})

group('the features Russian is made of', () => {
  test('case and number are one phrase, in that order', () => {
    // "genitive plural", never "plural genitive" — 0012 is specific about this,
    // and it is most of what there is to say about a Russian noun.
    expect(describe('Animacy=Inan|Case=Gen|Gender=Masc|Number=Plur', 'en')).toBe(
      'genitive plural · masculine',
    )
  })

  test('a Russian word with no case shown would be a word with nothing shown', () => {
    expect(describe('Animacy=Inan|Case=Loc|Gender=Masc|Number=Sing', 'en')).toContain(
      'prepositional',
    )
  })

  test('aspect leads the verb, because it is what the verb is', () => {
    expect(
      describe('Aspect=Perf|Gender=Fem|Mood=Ind|Number=Sing|Tense=Past|VerbForm=Fin|Voice=Act', 'en'),
    ).toBe('perfective indicative past · singular · feminine')
  })

  test('the unmarked half of a feature is not printed on every word', () => {
    // Voice=Act and Animacy=Inan are on nearly every Russian word; saying so each
    // time is noise, so only the marked value has a name.
    const active = describe('Aspect=Imp|Mood=Ind|Tense=Pres|Voice=Act', 'en')
    expect(active).not.toContain('active')
    expect(describe('Aspect=Perf|Tense=Past|VerbForm=Part|Voice=Pass', 'en')).toContain('passive')
    expect(describe('Animacy=Inan|Case=Nom|Number=Sing', 'en')).not.toContain('inanimate')
    expect(describe('Animacy=Anim|Case=Acc|Number=Sing', 'en')).toContain('animate')
  })

  test('the short form of an adjective is worth saying', () => {
    expect(describe('Gender=Fem|Number=Sing|StyleVariant=Short', 'en')).toContain('short form')
  })
})

group('the interface language reaches the grammar', () => {
  test('German names the cases in German', () => {
    expect(describe('Case=Dat|Number=Sing', 'de')).toBe('Dativ Singular')
    expect(describe('Aspect=Imp|Mood=Ind|Tense=Past', 'de')).toBe('unvollendet Indikativ Vergangenheit')
  })

  test('an unknown locale falls back to English rather than showing nothing', () => {
    expect(describe('Case=Gen|Number=Sing', 'xx')).toBe('genitive singular')
  })
})

group('choosing which language the grammar is named in', () => {
  test('the language you are reading, when there is a table for it', () => {
    // "imparfait" is the word you will meet everywhere else in French.
    expect(grammarLocale('fr', 'en')).toBe('fr')
    expect(grammarLocale('fr', 'de')).toBe('fr')
  })

  test('otherwise the language the interface is in', () => {
    // Russian case names in Russian would be a wall at A2.
    expect(grammarLocale('ru', 'de')).toBe('de')
    expect(grammarLocale('ru', 'en')).toBe('en')
    expect(grammarLocale('it', 'de')).toBe('de')
  })

  test('and English when neither is known', () => {
    expect(grammarLocale('ru', 'xx')).toBe('en')
  })
})
