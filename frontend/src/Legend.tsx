/** What the colours mean and which key does what.
 *
 * Shown, not described: every sample below carries the same CSS class the reader
 * uses, so the legend cannot drift from the thing it explains.
 */

const COLOURS: Array<[string, string, string]> = [
  ['new', 'quai', "New. You have never said anything about this word."],
  ['novel-form', 'marcherons', 'You know this word. This shape of it is new to you.'],
  ['learning', 'brouillard', 'You are learning it.'],
  ['review', 'lanterne', 'You have met this a lot now. Do you know it yet?'],
  ['known', 'maison', 'Known. Nothing to do.'],
]

const KEYS: Array<[string, string]> = [
  ['Tab', 'jump to the next word that wants an answer'],
  ['⇧ Tab', 'jump back'],
  ['1', "I'm learning this"],
  ['k', 'I know this'],
  ['i', 'ignore it — names, numbers'],
  ['⇧ K', 'everything unresolved on this page → known, and stay here'],
  ['j  ↓  ↑', 'move one sentence'],
  ['Enter', 'write your own note'],
  ['Esc', 'back to the text'],
  ['o', 'the word underneath is wrong'],
  ['Space', 'hear the sentence'],
  ['/', 'go somewhere else'],
]

const BUTTONS: Array<[string, string]> = [
  ['English', 'put a translation under each sentence'],
  ['click = learning', 'while on, clicking a blue word marks it — good for a fast pass'],
  ['Mark page known', 'clears the blue and answers the underlined; you stay on the page'],
  ['Next page', 'turn the page and record what you met'],
  ['undo', 'appears after a bulk change; takes it back'],
  ["something's wrong", 'tell me about it — bottom right, on every page'],
]

export default function Legend({ onBack }: { onBack: () => void }) {
  return (
    <main>
      <p className="bar">
        <button onClick={onBack}>← library</button>
      </p>

      <h1>What the colours mean</h1>

      {/* The assembled picture first, the parts list after. */}
      <p className="legend-demo">
        <span className="tok tok--known">Le </span>
        <span className="tok tok--learning">brouillard</span>
        <span className="tok tok--known"> se levait sur le </span>
        <span className="tok tok--new">quai</span>
        <span className="tok tok--known">, et nous </span>
        <span className="tok tok--novel-form">marcherons</span>
        <span className="tok tok--known"> vers la </span>
        <span className="tok tok--review">lanterne</span>
        <span className="tok tok--known">.</span>
      </p>

      <ul className="legend">
        {COLOURS.map(([state, word, meaning]) => (
          <li key={state}>
            <span className={`tok tok--${state}`}>{word}</span>
            <span>{meaning}</span>
          </li>
        ))}
      </ul>

      <p className="muted">
        Blue always means the word wants something from you. Filled in, you have never
        judged it. Dashed, you know the word but not this shape of it. Underlined, you
        have met it often enough that it is time you decided.
      </p>

      <h1>The loop</h1>
      <p className="legend-loop">
        <kbd>Tab</kbd> → read the sentence → <kbd>k</kbd> or <kbd>1</kbd> → <kbd>Tab</kbd>
      </p>
      <p className="muted">
        That is the whole thing. You never hunt for blue words; Tab finds the next
        one, including the ones underlined because it is time you decided.
        Do not be shy with <kbd>⇧ K</kbd> — clearing a page you can mostly read is the
        point, not cheating.
      </p>

      <h1>Keys</h1>
      <ul className="legend keys-list">
        {KEYS.map(([key, what]) => (
          <li key={key}>
            <kbd>{key}</kbd>
            <span>{what}</span>
          </li>
        ))}
      </ul>

      <h1>Buttons</h1>
      <ul className="legend keys-list">
        {BUTTONS.map(([label, what]) => (
          <li key={label}>
            <span className="legend-btn">{label}</span>
            <span>{what}</span>
          </li>
        ))}
      </ul>

      <h1>Two things that surprise people</h1>
      <ul className="legend-notes">
        <li>
          Marking a word marks <em>the word</em>, not the spelling. Say you know{' '}
          <span className="tok tok--known">marcher</span> and every form of it changes —
          except ones you have not actually met, which get the underline.
        </li>
        <li>
          A page counts once. Reading it again does not move anything on, because what
          makes meeting a word again useful is the gap in between.
        </li>
      </ul>
    </main>
  )
}
