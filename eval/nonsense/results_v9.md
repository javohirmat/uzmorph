# Nonsense acceptance after phase 3 (lower is better). Same 299 non-words as results.md (Zirh: 15% any-known, unchanged).

| type | n | v8d | v8d+guess | v9 | v9+guess | v9 Capitalised: analyzer + verified name list | v9 Capitalised mid-sentence: + name guesser |
|---|---|---|---|---|---|---|---|
| ALL | 299 | 1% | 17% | 1% | 17% | 1% | 100% |
| case_before_pl | 30 | 0% | 0% | 0% | 0% | 0% | 100% |
| case_before_poss | 30 | 0% | 0% | 0% | 0% | 0% | 100% |
| double_case | 30 | 0% | 3% | 0% | 3% | 0% | 100% |
| noun+verb_tense | 29 | 0% | 24% | 0% | 24% | 0% | 100% |
| tense_before_neg | 30 | 0% | 30% | 0% | 30% | 0% | 100% |
| typo_drop | 30 | 3% | 13% | 3% | 13% | 3% | 100% |
| typo_subst | 30 | 0% | 7% | 0% | 7% | 0% | 100% |
| typo_swap | 30 | 0% | 3% | 0% | 3% | 3% | 100% |
| verb_stem+case | 30 | 3% | 87% | 3% | 87% | 7% | 100% |
| wrong_px3_allomorph | 30 | 0% | 0% | 0% | 0% | 0% | 100% |

The proper-noun guesser accepts any capitalised unknown word in mid-sentence position by design (a fallback whose readings are marked <guess>), so its column is not a rejection test. Lower-case non-words never reach it. The verified name list accepted none of the non-words; the few Capitalised hits come from existing analyzer entries.
