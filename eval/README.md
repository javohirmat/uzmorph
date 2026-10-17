# Evaluation

Everything needed to *re-score* the analyzer is here except the evaluation sentences and their gold labels.

## The evaluation set is private

The gold set has 260 sentences (2,894 word tokens; 2,793 scored: test 1,731 + dev 1,062) sampled from four genres. (2,797 were scored before the native check, which flagged 4 more tokens as excluded. 264 sentences were sampled and 4 were later excluded; the 264 had 2,970 word tokens, which is the set used for the package-vs-research parity check in `tools/README.md`.)

| genre | sentences | source |
|---|---|---|
| books | 71 | tahrirchi/uz-books-v2 (Latin split), one sentence per book |
| wiki | 70 | uz.wikipedia, one sentence per article |
| news | 40 | three Uzbek news sites (RSS, Oct 2026), one sentence per article |
| telegram | 79 | 8 public channels; links, handles, hashtags, phone numbers and emoji stripped |

**The sentences and gold labels are not distributed, for copyright reasons.** The book sentences come from copyrighted books, the news sites do not allow republication, and the Telegram text is third-party content. Researchers can request the evaluation set for research use from the maintainer; see the contact line in the top-level README.

The scripts expect the private files in `eval/private/` (git-ignored): `sentences.jsonl`, `gold.json`, and the analyser output caches `ours*.json`, `cands*.json`, `zirh.json`.

## Protocol (frozen before any tuning)

- `split.json`: dev/test split by sentence, stratified by genre. Within each genre the sentence ids were shuffled with seed 20261017, and the first 40% went to dev (dev 104 sentences / 1,062 scored tokens; test 156 / 1,731).
- All tuning (ranker rules, context weight, proper-noun design) used dev only. Test was scored once, after the configuration was frozen.
- The ranker models are trained on corpus text only, never on the gold. The documents the evaluation sentences come from were excluded from the context and capitalisation statistics.
- Accuracy is over **all** scored tokens: an unanalysed token counts as wrong. "best" = top-ranked reading; "oracle" = gold reading anywhere in the candidate list.
- lemma+feats is the headline metric. UPOS is not comparable across tools, because ZirhUzMorph only outputs N/V.
- Not scored: tokens flagged foreign / typo / affix fragment / abbreviation.
- Scheme and both tag mappings: `ANNOTATION.md`.

## How the gold was made (read this before citing the numbers)

1. Both analysers (ours and ZirhUzMorph 0.1.1) were run on every token, and their outputs were mapped into one scheme.
2. **1,525 labels were auto-accepted** where the tools agreed unambiguously, or the word was closed-class. A **spot-check of 150** of these auto-accepted tokens found 6 errors (4.0%), which were fixed. The other auto-accepted labels were not looked at individually.
3. The remaining ~1,370 tokens were adjudicated in context by an AI assistant. **About 1,120 of these AI-adjudicated labels were never reviewed by a person.**
4. **250 rows were checked by a native speaker:** the 250 hardest of the 550 disagreement or low-confidence tokens. 24 were marked wrong; 8 labels were changed, and 17 rows were kept on documented convention questions (copula lemma *e*, *deb/degan* → *de-*, postpositional nouns).

So the gold is **mostly model-built, with a partial native check** (250 of 2,894 tokens checked by a person, plus the 150-token spot-check). It may be biased toward the conventions of the tools it was built from.

## Files

| path | what |
|---|---|
| `results/split_scores.md/.json` | headline tables: dev/test × script × genre (after the native check), including the upstream 00522e3 + CG row |
| `results/score_uzmorph.md` | output of `scripts/score_uzmorph.py`: the released package on the private set |
| `results/split_scores_pre_review.md` | the same before the native check (v9 analyzer; test 93.4 vs 87.7) |
| `results/ablation_dev.md/.json` | ranker components on dev |
| `results/checked_subset.md` | only the natively checked tokens (a hard, non-representative subset) |
| `results/scores.md/.json` | the earlier single-pass table (v8d, before the dev/test split) |
| `results/loss_analysis.md` | where v8d lost to Zirh (error-category counts only) |
| `nonsense/nonwords.tsv` | 300 generated non-words (0 corpus hits). `boshqarmamoqda` turned out to be real and is excluded, so 299 are scored. |
| `nonsense/results_v91.md` | non-word acceptance for this release (lower-case and capitalised); `results.md`, `results_v9.md` are the earlier runs |
| `scripts/score_uzmorph.py` | scores **the released package** on the private set (reproduces the "after" row exactly: test lat 93.5) |
| `scripts/score.py`, `score_split.py`, `rank_eval.py`, `ablation.py`, `checked_subset.py` | research scoring scripts |
| `scripts/run_ours.py`, `run_zirh.py`, `candidates.py`, `build_gold.py` | gold-building pipeline |
| `scripts/make_nonsense.py`, `run_nonsense.py`, `run_nonsense_v9.py`, `run_nonsense_v91.py` | non-word test |
| `evidence/` | the files behind the README's coverage, guesser-precision, line-count and generation numbers (see `evidence/README.md`) |

The research scripts refer to the original working layout through `work/...` paths (see `../tools/README.md`).
