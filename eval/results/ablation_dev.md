# Ranker components, DEV split only (104 sentences, 1,062 main tokens after the native reviewer sheet; 1,063 before — numbers moved by ≤0.1), analyzer v9.1, Latin

Top-1 accuracy over all main tokens (uncovered = wrong); lf = lemma+feats. All tuning decisions were made on this table; test was scored once afterwards.

| step | lemma | upos | coarse | feats | lf | full |
|---|---|---|---|---|---|---|
| CG -1 + guesser (baseline) | 91.4 | 79.3 | 90.7 | 84.5 | 83.4 | 82.3 |
| corpus EM prior only (replaces CG) | 94.0 | 78.8 | 91.3 | 83.2 | 82.8 | 80.4 |
| + singular default | 94.0 | 78.8 | 91.3 | 87.7 | 87.2 | 84.8 |
| + real lemma beats short lemma+px1/2sg | 94.0 | 78.8 | 91.3 | 87.7 | 87.2 | 84.8 |
| + demote medial imperatives | 94.0 | 78.9 | 91.4 | 87.8 | 87.3 | 84.9 |
| + duplicate-lemma rule (corpus paradigm size) | 94.2 | 80.6 | 93.6 | 89.9 | 89.3 | 87.8 |
| + class-bigram context (λ=1) | 94.3 | 80.8 | 93.4 | 92.5 | 91.7 | 89.9 |
| + proper-noun guesser & verified list = FINAL | 96.5 | 83.0 | 95.8 | 94.8 | 94.1 | 92.3 |
| FINAL − singular default | 96.5 | 83.0 | 95.8 | 88.2 | 87.5 | 85.7 |
| FINAL − real lemma | 96.0 | 83.0 | 95.6 | 94.4 | 93.6 | 92.1 |
| FINAL − medial imperative | 96.5 | 82.9 | 95.7 | 94.7 | 94.0 | 92.2 |
| FINAL − duplicate lemma | 96.2 | 81.2 | 93.8 | 92.5 | 91.9 | 89.5 |
| FINAL − context | 96.4 | 82.8 | 96.0 | 92.3 | 91.6 | 90.1 |
| FINAL − names | 94.3 | 80.8 | 93.4 | 92.5 | 91.7 | 89.9 |
| FINAL with λ=0.5 | 96.4 | 82.7 | 95.9 | 94.4 | 93.7 | 92.2 |
| FINAL with λ=1.5 | 96.5 | 82.5 | 95.3 | 94.5 | 93.7 | 91.9 |
| FINAL but HMM (Baum-Welch) context instead of bigram | 96.5 | 82.9 | 96.0 | 94.4 | 93.7 | 92.1 |
| FINAL + tried: closed-class reading beats noun | 96.4 | 83.1 | 96.0 | 94.7 | 94.0 | 92.5 |
| FINAL + tried: demote bare -gan verbal noun | 96.5 | 83.1 | 95.9 | 93.8 | 93.0 | 91.2 |
| FINAL + tried: passive split over lexical -n/-l verb | 96.5 | 83.0 | 95.8 | 94.8 | 94.1 | 92.3 |
