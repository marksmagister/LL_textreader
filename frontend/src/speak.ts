/** Sentence audio, the cheap way.
 *
 * The browser's own speech synthesis: no model, no server, no download. macOS
 * ships good French and Italian voices; Russian depends on what is installed,
 * and `voiceFor` finds nothing rather than reading Cyrillic in English.
 *
 * This is not the same feature as playing a recording with the text aligned to
 * it — see docs/decisions/0009 — but it answers "how does this sound", which is
 * most of what a reader wants.
 */

import { voiceTag } from './lang'

/** Prefer a voice that actually speaks the language, not the system default
 *  reading French with an English accent. */
function voiceFor(lang: string): SpeechSynthesisVoice | undefined {
  const voices = window.speechSynthesis?.getVoices() ?? []
  return voices.find((v) => v.lang.toLowerCase().startsWith(lang)) ?? undefined
}

export function available(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

export function speak(text: string, lang: string) {
  if (!available() || !text.trim()) return
  // Always cancel first: pressing Space twice should re-read, not queue up a
  // second reading behind the first.
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = voiceTag(lang)
  const voice = voiceFor(lang)
  if (voice) utterance.voice = voice
  utterance.rate = 0.95 // a shade under natural; this is for learners
  window.speechSynthesis.speak(utterance)
}

export function stop() {
  if (available()) window.speechSynthesis.cancel()
}
