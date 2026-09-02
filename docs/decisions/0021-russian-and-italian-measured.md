# 0021 — Russian and Italian, measured

**Status: built.** 0012 planned this; this is what happened when it was done, and
the four things that were not what 0012 expected.

Measured September 2026 against `ru_core_news_md` 3.8.0 and `it_core_news_md`
3.8.0. The tables are `backend/tests/test_russian.py` and `test_italian.py`, kept
as floors so a model upgrade that quietly gets worse fails a test.

## The prediction was wrong, usefully

0012 said: "Expect case to be reasonable and aspect to be the risk."

| | Russian | |
|---|---|---|
| aspect | 11/11 | the predicted risk; it does not exist |
| case | 12/12 | perfect, including the prepositional |
| tense | 8/8 | |
| lemma | 20/22 | `другом` read as a pronoun, `большую` given the comparative |
| POS | 21/22 | the same `другом` |

Aspect is the one thing a Russian model has no excuse to get wrong — it is
marked in the stem, not inferred — and it is fine. Case, the thing that was
expected to need watching, is the strongest feature in the model.

What was actually broken was **person**, **the oblique pronouns**, and **ё**.

## The three rules Russian needed

### Person, which failed silently

`ru_core_news_md` writes `Person=First|Second|Third`. Every other model in the
project writes `1|2|3`, and `morph.ts` has one table for all languages, so a
Russian verb would have shown **no person at all** — not a wrong answer, an
absent one, which is the kind of failure nobody reports because nothing looks
broken. Normalised in the adapter, so one UD convention reaches the front end.

### The oblique pronouns, which split the commonest words in the language

`меня`, `мне`, `мной` all come back as their own lemmas. So `я` becomes four
vocabulary entries, and the words a beginner meets most are the ones the lexicon
counts worst. (The model *does* lemmatise them onto `он` when it reads them as
possessive determiners, so this is a gap rather than a considered disagreement.)

Mapped onto the nominative, from a flat table of closed-class forms. This is not
a guess about a model's confidence, so rule 7 does not apply — these are facts of
Russian. `им` and `ним` are ambiguous between `он` and `они`, and the tagger's
Number decides; with no Number, nothing is claimed.

The payoff is the point of the whole design: mark `я` known and `меня` renders as
a **novel form** — you know the word, you have not met this shape — rather than
as a second word you have never seen.

### ё, which the table did not catch

The one found by reading rather than by testing, which is the ratio `status.md`
keeps noting. Russian is normally written with ё spelled е and the model was
trained that way, so a word that carries its ё can fall out of vocabulary:

| written with ё | | written with е | |
|---|---|---|---|
| `живёт` | `живёт`, VERB, Tense=**Past** | `живет` | `жить`, VERB, Tense=Pres |
| `пьёт` | `пьёт`, **NOUN** | `пьет` | `пить`, VERB, Tense=Pres |
| `поёт` | `поёт`, — | `поет` | `петь`, VERB, Tense=Pres |
| `берёт` | `берёт`, — | `берет` | `брать`, VERB, Tense=Pres |

Five of eight common verbs, and the failure takes the **part of speech** with it,
which matters more than the tense because POS is part of the key (rule 3). The
sixteen-sentence table missed it because it happened to use е-spelled words; one
page of a starter text found it in about a minute.

**0012 ruled that ё must not be folded into е**, because that would merge `всё`
with `все`, and that ruling stands untouched: `norm` still keeps every ё, and the
two remain separate entries. What the adapter does instead is read the de-ёed
word a second time and take that reading **only if it comes back a verb** — the
same shape, and the same safety argument, as the French rule for a capitalised
word opening a sentence. `всё`, `ещё` and `её` are not verbs in any reading, so
they are never touched.

## Italian gets no rules, deliberately

| | Italian | |
|---|---|---|
| lemma | 14/17 | `chiamo`, `andremo` → `andre`, `verrei` → `velere` |
| POS | 17/17 | |
| person | 6/9 | |

Two real weaknesses. **First-person singular `-o` forms** are often left
unlemmatised or read as the noun they are homographs of — `Abito a Roma` gives
the noun *abito*, a suit; `Lavoro in banca` gives *lavoro*, work. And **future
and conditional stems get invented**: `andremo` → `andre`, `verrei` → `velere`.

Neither can be fixed from the form with certainty. French tense rules work
because French endings are uniform and the future stem always ends in `-r`;
Italian `parlo → parlare` but `finisco → finire` and `vado → andare`, which is a
lexicon, not a rule. Where the lemmatiser gives up it already returns the surface
form, which is the honest answer (rule 7), and the rest is what `o` is for.

Worth saying because it was tempting: the starter texts were **not** written
around this. `Mi chiamo` is the first sentence anyone learns in Italian and it is
one of the failures, and it stays in. Writing the demo around the model's weak
spots would make the demo a lie.

## Italian is the control, and it did its job

0012 wanted Italian alongside Russian to find out whether the novel-form state
earns its keep. Measured by importing the starter texts through the real
pipeline and counting how much of the third text the first two teach:

| | lemmas already taught | of those, in a shape never met |
|---|---|---|
| Russian, text 3 | 41 | **19** |
| Italian, text 3 | 42 | **4** |

The same amount of vocabulary carried over; five times as many unmet shapes. That
is the first measured evidence for the two-table split, and it says what one
would hope: in Italian the state is a nicety, in Russian it is half of what you
see. Not proof — six short texts by one author — but it is a number where there
was an argument.

## What the front end needed

`morph.ts` gained **Case** above all (a Russian word with no case shown is a word
with nothing shown), plus **Aspect**, **Animacy**, **Voice** and the short form.
Two decisions inside that:

- **Case and number are said as one phrase**: "genitive plural", never "plural ·
  genitive", the same way person and number already were.
- **Only the marked half of a feature is named.** `Voice=Act` and `Animacy=Inan`
  sit on nearly every Russian word; printing them would be noise on every token.
  Mapping only `Pass` and `Anim` gets that for free, because an unmapped value is
  already dropped.

## Which language the grammar is named in

0012 expected a third setting here, next to interface language and translation
target. There is none, and there should not be: the rule leaves nothing for a
reader to decide.

**The language you are reading, when this reader has the words for it; otherwise
the language of the interface.** So French keeps *imparfait*, which is the
maintainer's stated reason for naming grammar at all — it is the word you meet
everywhere else in French. Russian has no table, so an A2 reader gets "genitive
plural" or "Genitiv Singular" rather than *родительный падеж*, which at A2 is a
wall. Every combination that rule produces is the one you would have picked, so
the settings screen explains it instead of asking.

## Three things deliberately not done

**No shared adapter base class.** There are now three adapters running the same
twenty-five-line spaCy walk, which is the point at which CLAUDE.md would allow an
abstraction. It is not taken, for one concrete reason: extracting it means
touching `fr.py`, and any change to its `pipeline_id` marks **every French lesson
on the live box stale** and forces a reprocess. That is a real cost paid for a
tidier file. The trigger to revisit is a fourth language, or the next time `fr.py`
has to change anyway.

**German is not yet a translation target.** `translate.py` is keyed on
`(source, target)` and `sentence_gloss` already stores `target_lang`, so it is one
`MODELS` entry per pair plus somewhere to choose. `ru→en` and `it→en` are added;
German pairs are not, because the network this was built on could not reach
Hugging Face to confirm the model names, and inventing them would turn a clean
"no model for this pair" into a confusing download error. The two that were added
follow the naming scheme 0012 already specified and are unverified in the same
way — if one is wrong, the fix is that one string.

**No dictionary for Russian or Italian yet.** `setup-dictionary.sh` takes them
both and the loader was already language-agnostic, but the extracts are ~940MB
and ~500MB and were not downloaded here. Until they are, clicking a Russian word
gives grammar and a note field but no gloss. That is a download, not a decision.
