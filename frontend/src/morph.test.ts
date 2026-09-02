import { describe as group, expect, test } from 'vitest'
import { describe } from './morph'

group('reading UD features back as grammar', () => {
  test('Imp means different things under Tense and Mood', () => {
    // The trap this module exists to avoid: imperfect vs imperative.
    expect(describe('Mood=Ind|Tense=Imp|Person=3|Number=Sing')).toContain('imparfait')
    expect(describe('Mood=Imp|Person=2|Number=Sing')).toContain('impératif')
  })

  test('person and number read as one phrase', () => {
    expect(describe('Mood=Ind|Tense=Imp|Person=3|Number=Sing')).toBe(
      'indicatif imparfait · 3e personne du singulier',
    )
  })

  test('the conditional is not called "conditional present"', () => {
    expect(describe('Mood=Cnd|Tense=Pres|Person=1|Number=Sing')).toBe(
      'conditionnel · 1re personne du singulier',
    )
  })

  test('the subjunctive reads tense first', () => {
    expect(describe('Mood=Sub|Tense=Pres|Person=3|Number=Sing')).toBe(
      'présent subjonctif · 3e personne du singulier',
    )
  })

  test('nouns get gender and number', () => {
    expect(describe('Gender=Fem|Number=Plur')).toBe('pluriel · féminin')
  })

  test('nothing to say stays silent rather than inventing', () => {
    expect(describe('')).toBe('')
    expect(describe('Typo=Yes|NounClass=Wol3')).toBe('')
  })

  test('unknown values are dropped, not printed raw', () => {
    expect(describe('Tense=Fut|Mood=Zzz')).toBe('futur')
  })
})
