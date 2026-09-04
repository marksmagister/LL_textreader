import { useState } from 'react'
import type { Me } from './api'

/** What went wrong, in words rather than a code. The callback redirects here
 *  with ?error= rather than showing a bare error page, because it is reached by
 *  the browser navigating and there would be no way back from one. */
const REASONS: Record<string, string> = {
  cancelled: 'Sign-in was cancelled.',
  expired: 'That took too long — try again.',
  nocode: 'Google did not send anything back. Try again.',
  google: 'Google would not complete the sign-in. Try again in a moment.',
  full: 'This server is full, so no new accounts can be made just now.',
}

const NAMES: Record<string, string> = {
  fr: 'French',
  ru: 'Russian',
  it: 'Italian',
  ar: 'Arabic',
  nl: 'Dutch',
  de: 'German',
}

/** The door, and nothing else.
 *
 * This page used to argue: a worked sample, a key to the colours, three
 * sections on the lemmatiser and the licence. All of it was true and none of it
 * belonged here — the people who reach this screen have been handed the link by
 * someone, so they have already decided. Explaining the product to a person who
 * came to sign in is a toll, not a service.
 *
 * So: mark, name, button, small print. The argument lives in the README and in
 * the reader itself, where it can be seen rather than claimed. */
export default function SignIn({ me, error }: { me: Me; error?: string }) {
  // Only asked once, and only used when the account is created — it decides
  // which starter lessons you are given. The picker is hidden entirely when
  // there is nothing to choose, which today there is not.
  const [lang, setLang] = useState(me.languages[0] ?? 'fr')
  const full = !me.signup

  return (
    <main className="signin">
      {/* The same file the browser tab and the consent screen use, so the mark
          cannot drift between them. */}
      <img className="signin-mark" src="/favicon.svg" alt="" width="72" height="72" />
      <h1>LL_textreader</h1>

      {error && <p className="warn">{REASONS[error] ?? 'Something went wrong signing in.'}</p>}

      {!me.google ? (
        <p className="warn">
          Google sign-in is not configured on this server, so there is no way in yet.
        </p>
      ) : full ? (
        <p className="warn">
          This server has as many accounts as it is willing to hold. If you already have one,
          you can still <a href="/api/auth/google/start">sign in</a>.
        </p>
      ) : (
        <>
          {me.languages.length > 1 && (
            <p className="signin-lang">
              <label htmlFor="lang">I am learning</label>{' '}
              <select id="lang" value={lang} onChange={(e) => setLang(e.target.value)}>
                {me.languages.map((l) => (
                  <option key={l} value={l}>
                    {NAMES[l] ?? l}
                  </option>
                ))}
              </select>
            </p>
          )}
          {/* A link, not a fetch: signing in is a full-page journey to Google
              and back, and an XHR cannot make that trip. */}
          <a className="button primary" href={`/api/auth/google/start?lang=${lang}`}>
            Sign in with Google
          </a>
        </>
      )}

      <p className="meta signin-foot">
        <a href="/privacy">What is stored</a> · <a href="/terms">Terms</a>
      </p>
    </main>
  )
}
