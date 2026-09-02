# 0004 — Keyboard-first navigation

The core loop must never require the mouse. You press Tab, read the sentence, press a
number or `k`, press Tab. That rhythm is the ergonomic argument for the whole reader:
you never hunt for blue words, and an hour of reading feels like flow rather than
clicking.

## The bindings

```
Tab / Shift-Tab   next / previous word that wants an answer
1                 mark as learning
k                 mark known
i                 ignore (names, numbers)
Space             play/pause sentence audio
Shift-Space       replay current sentence
j / ↓ · ↑         next / previous sentence
Enter             open definition panel, focus search
Esc               close panel, return focus to text
Shift-K           page done → all remaining blue to known
Cmd-Enter         save note and advance to next unknown
/                 command palette (import, jump to lesson, switch lang)
o                 override this word's lemma
```

## What Tab stops on

A word you have never judged, and a word at level 4 — the one the app has met often
enough to be asking about (0008). Both want an answer, and the second was originally
unreachable: Tab walked past it, so the only way to reach the state 0008 exists to
produce was to spot a thin rule under a word and click it.

Not a novel form. That one is telling you something rather than asking, there is no
key to press, and stopping on every one of them would make Tab useless in Russian —
which is the language the novel-form state exists for.

## Superseded: the learning levels

`2`, `3` and `4` are gone. Levels are no longer set by hand — they are counted from
how many pages you have met the word on, so the only judgements the reader offers are
learning, known and ignore. See `0008-learning-levels.md`.

## One collision, resolved

The spec asked for both `k` = mark known and `j`/`k` = next/previous sentence. `k` goes
to **mark known**, because it is in the core loop and the vim pair is not. Previous
sentence is `↑` only; `j` and `↓` both go to the next sentence.

## Focus discipline

The definition panel must never take focus unless you asked for it, and `Esc` must
always return you to your exact position in the text. Getting this wrong is what makes
reader UIs feel sticky. Concretely: the reader owns a "cursor" token; panel opening
does not move it, and closing the panel restores focus to the cursor.

## Typography

The text is the interface. Fixed measure of ~65 characters, generous line height, and
a serif with real Cyrillic — Literata or Source Serif 4. System stacks fall back badly
on Russian and it makes reading quietly unpleasant.

## Audio (not built)

`Space` / `Shift-Space` are reserved. When audio lands, Whisper with
`word_timestamps=True` gives sentence timings; clicking a sentence seeks there and the
current sentence takes a subtle background. Reading and listening in one view, not two
modes.
