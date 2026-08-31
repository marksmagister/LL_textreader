# 0002 — Arabic needs two stages before lemmatisation

**Decided:** 2026-09-01 · **Status:** accepted in principle, **deferred past the pilot**

The pilot ships French (and maybe Russian). This stays written down so the schema and the
import pipeline keep room for it — the point is that adding Arabic later must not force a
rewrite, not that it works now.

## Context
Arabic breaks the assumptions the Dutch/French/Russian path can get away with.

## Decision
Two extra stages, neither optional:

1. **Clitic segmentation.** `وسيكتبونها` → و + س + يكتبون + ها: conjunction, future particle,
   verb, object pronoun. Each is a separate learnable unit. CAMeL Tools or MADAMIRA;
   Farasa is lighter and decent. This is one-to-many, which is why tokens carry char
   offsets rather than being reconstructible.
2. **Diacritic-blind matching.** Text is normally undiacritized, so `علم` is several words.
   The analyser returns ranked candidates; pick by context and store `confidence`. Below
   threshold, fall back to surface-form behaviour rather than guess.

**The root is not the key.** ك-ت-ب covers kataba, kitāb, maktab, kātib, maktaba — write,
book, office, writer, library. Separate vocabulary items. Root goes in `root_index`, used
only for a "related words" panel.

## Open
Levantine. MSA-trained tools mis-analyse بدي، عم بكتب، مش. Either a dialect-ID step routing
to a dialect analyser, or accept lower accuracy and lean on `lemma_override`. Undecided.
