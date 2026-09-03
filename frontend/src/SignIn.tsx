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

/** The product, in one sentence, using the reader's own classes.
 *
 * Shown rather than described, for the same reason the legend is: these are the
 * real `.tok` spans, so this cannot drift from what the reader actually does.
 * A paragraph claiming "words are coloured by whether you know them" asks to be
 * believed; this is just true on the page in front of you. */
function Sample() {
  return (
    <p className="signin-demo">
      <span className="tok tok--known">Le </span>
      <span className="tok tok--learning">brouillard</span>
      <span className="tok tok--known"> se levait sur le </span>
      <span className="tok tok--new">quai</span>
      <span className="tok tok--known">, et nous </span>
      <span className="tok tok--novel-form">marcherons</span>
      <span className="tok tok--known"> vers la lanterne.</span>
    </p>
  )
}

export default function SignIn({ me, error }: { me: Me; error?: string }) {
  // Only asked once, and only used when the account is created — it decides
  // which starter lessons you are given. Changing what you read later is the
  // library's job, not this screen's.
  const [lang, setLang] = useState(me.languages[0] ?? 'fr')
  const full = !me.signup

  return (
    <main className="signin">
      <h1>LL_textreader</h1>
      <p className="lede">
        Read whatever you actually want to read, in a language you are learning. Every word
        is coloured by whether <em>you</em> know it.
      </p>

      <Sample />

      <ul className="signin-key">
        <li>
          <span className="tok tok--new">quai</span> you have never judged this word
        </li>
        <li>
          <span className="tok tok--novel-form">marcherons</span> you know the word — not
          this shape of it
        </li>
        <li>
          <span className="tok tok--learning">brouillard</span> you are learning it
        </li>
      </ul>

      <p className="lede">
        Click a word, read the definition, and it changes colour. There is no deck to
        grind: you meet the word again in the next thing you read. As you read more, the
        page decolourises.
      </p>

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
        <div className="signin-go">
          {me.languages.length > 1 && (
            <p className="bar">
              <label htmlFor="lang">I am learning</label>
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
          <p className="meta">
            You start with a couple of short texts to read. Everything you import after that
            is private to your account — it is never shared with other readers, and you can
            take all of it with you or delete it at any time.
          </p>
        </div>
      )}

      <p className="meta signin-foot">
        <a href="/privacy">What is stored</a> · <a href="/terms">Terms</a>
      </p>
    </main>
  )
}
