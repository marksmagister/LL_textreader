/** Light or dark, chosen or inherited.
 *
 * Three states, not two: 'light', 'dark', and no choice at all — in which case
 * the CSS follows prefers-color-scheme. A toggle that knows only two states can
 * never give the system default back once it has been touched.
 */

export type Theme = 'light' | 'dark' | 'system'

const KEY = 'll_textreader_theme'

export function stored(): Theme {
  try {
    const value = localStorage.getItem(KEY)
    return value === 'light' || value === 'dark' ? value : 'system'
  } catch {
    return 'system' // private windows and blocked site data both throw
  }
}

export function apply(theme: Theme) {
  const root = document.documentElement
  if (theme === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', theme)
  try {
    if (theme === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, theme)
  } catch {
    // failing to remember the choice is no reason to ignore it
  }
}

/** What the page is actually showing right now. */
export function effective(theme: Theme): 'light' | 'dark' {
  if (theme !== 'system') return theme
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}
