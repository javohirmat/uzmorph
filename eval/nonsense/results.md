# Nonsense acceptance (lower is better). 299 non-words (300 generated, 1 real form removed), 0 hits in a 10.5M-type corpus frequency list.

| type | n | ours | ours_guess | ours_guess_all | zirh_any_known | zirh_top_known |
|---|---|---|---|---|---|---|
| ALL | 299 | 1% | 17% | 90% | 15% | 15% |
| case_before_pl | 30 | 0% | 0% | 100% | 100% | 100% |
| case_before_poss | 30 | 0% | 0% | 100% | 0% | 0% |
| double_case | 30 | 0% | 3% | 100% | 3% | 3% |
| noun+verb_tense | 29 | 0% | 24% | 100% | 10% | 10% |
| tense_before_neg | 30 | 0% | 30% | 100% | 0% | 0% |
| typo_drop | 30 | 3% | 13% | 70% | 17% | 17% |
| typo_subst | 30 | 0% | 7% | 70% | 0% | 0% |
| typo_swap | 30 | 0% | 3% | 73% | 3% | 3% |
| verb_stem+case | 30 | 3% | 87% | 100% | 13% | 13% |
| wrong_px3_allomorph | 30 | 0% | 0% | 83% | 0% | 0% |

Notes: boshqarmamoqda removed (real form). In case_before_pl, -dan+lar (3 words) and arguably -ning+lar (8) can be predicative plurals ("ular Toshkentdanlar"); -ni+lar and -ga+lar (19) cannot - Zirh accepts all 19 as PRED.PL. ours_guess_all guesses for any unknown string by design, so it is not a rejection test.