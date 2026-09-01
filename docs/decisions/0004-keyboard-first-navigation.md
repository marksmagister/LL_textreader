# 0004 — Keyboard-first navigation

The core loop must never require the mouse. You press Tab, read the sentence, press a
number or `k`, press Tab. That rhythm is the ergonomic argument for the whole reader:
you never hunt for blue words, and an hour of reading feels like flow rather than
clicking.

## The bindings

```
Tab / Shift-Tab   next / previous unknown word
1 2 3 4           set learning level
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
