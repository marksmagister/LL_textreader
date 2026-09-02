/** Which language you are reading today.
 *
 * Remembered next to the theme, for the same reason: it is a fact about you and
 * your machine, not about the library. It decides what an import is tokenised
 * as, which lexicon the vocabulary page shows, and what the library lists —
 * a Russian lesson among Italian ones is noise.
 *
 * The list of languages comes from `/api/health`, so what is on offer is
 * whatever the server is configured for. Their names are in `i18n.ts`, named in
 * the language of the interface: a German reader chooses "Französisch".
 */

const KEY = 'll_textreader_lang'

export function stored(): string {
  try {
    return localStorage.getItem(KEY) || 'fr'
  } catch {
    return 'fr' // private windows and blocked site data both throw
  }
}

export function remember(lang: string) {
  try {
    localStorage.setItem(KEY, lang)
  } catch {
    // failing to remember the choice is no reason to ignore it
  }
}

/** The tag for speech synthesis. Not the same thing as the study language: the
 *  browser wants a locale, and `fr` alone gets you a French voice on some
 *  systems and an English one reading French on others. */
export function voiceTag(lang: string): string {
  return { fr: 'fr-FR', ru: 'ru-RU', it: 'it-IT', nl: 'nl-NL', de: 'de-DE' }[lang] ?? lang
}
