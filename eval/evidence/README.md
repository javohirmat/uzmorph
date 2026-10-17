# Evidence files behind the README numbers

All files contain words, tags and counts only (no sentences).

| file | made by | README number |
|---|---|---|
| `dictionary_coverage.json` | `tools/coverage/dictionary_coverage.py OUT orig tb v4fix … v91` | raw token coverage of every build (upstream `orig` 86.151, this release `v91` 89.328); the CHANGES.md coverage column is these plus the anchor offset |
| `guesser_coverage_v91.json` | `tools/coverage/guesser_coverage.py v91 uzmorph/data/uzb_guesser.automorf.bin OUT` | dictionary + confident guesser (raw 93.44, anchored 94.80) and + unfiltered guesser |
| `guesser_coverage_v8d.json` | same tool, previous analyzer (v8d) | 94.77 anchored (see note below) |
| `guesser_precision_sample100.json` | individual judgements of 100 confident guesses (word types drawn token-weighted from the corpus; not native-speaker judgements) | 57 strict / 63 lenient |
| `regress_v8d.json`, `regress_v9.json`, `regress_v91.json` | `tools/regression/regress.py` | per-build regression: coverage figures, types/tokens lost and gained vs the previous build and vs upstream, top lost/gained types, 50 sampled gains, the generation checks |
| `gencheck.json` | `tools/gencheck/gencheck.py` | spurious -ish- generation: v8d 275 / 462, v9 0, v9.1 0 |
| `lexc_additions.json` | `tools/regression/lexc_additions.py UPSTREAM_LEXC apertium-uzb/apertium-uzb.uzb.lexc OUT` | "about 4,430 added lines": 4,434 non-comment lines added, 3,048 comment lines added, 3,093 upstream lines removed or edited |

**Anchoring.** The first survey of upstream measured 87.51% with an earlier version of the measurement. The regression tool gives 86.151% for the same build. "Anchored" figures add 87.51 − 86.151 = 1.359 points (the `all` figure; the other three variants have their own offsets, listed in `guesser_coverage.py`).

**Guesser coverage note.** The pre-release report gave 94.74 (dictionary + confident guesser) and 95.69 (+ all guesses). That run could not be reproduced from the shipped code. The committed tool gives 94.77 / 95.87 on the same analyzer (v8d, with the shipped guesser binary) and 94.80 / 95.88 on this release, so the README uses the reproducible figures.

**Line count note.** An earlier draft said "about 7,500 added lines". That was the raw number of added lines including comments (7,556); the real additions are the 4,434 non-comment lines.
