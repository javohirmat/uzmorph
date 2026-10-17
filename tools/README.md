# Research tools

These are the scripts that produced this release. They are included for transparency and reproducibility. They are **not** needed to use the package, and they contain no corpus text.

Some tools use the Python packages `wordfreq` (data CC BY-SA 4.0) and `pymorphy3` only as filters during lemma mining (to drop English and Russian words from candidate lists). Nothing derived from them is shipped, and the package does not depend on them. Tool outputs are git-ignored.

They were written against a private working directory. Paths in them were rewritten to a neutral `work/` prefix:

| path in scripts | contents |
|---|---|
| `work/data/lat-*.parquet` | tahrirchi/uz-books-v2, Latin split (MIT, Hugging Face) |
| `work/cache/wordfreq_lat_full.sqlite` | whole-corpus word frequency table (built by the triage tools) |
| `work/verify/` | coverage tables and per-build lt-proc outputs (`regression/covlib.py`) |
| `work/morph/apertium-uzb-v4`, `-v5`, `-v6` | build trees of v8d, v9 and v9.1 (v9.1 = `../apertium-uzb`) |
| `work/morph/phase2/`, `phase3/` | mining outputs, guesser and ranker models |
| `work/morph/eval_gold/` | `../eval` plus the private set |

Run them from a directory where `work/` holds that layout. To regenerate only the shipped models you need just the corpus shards and an analyzer build (see below).

## models/: the corpus-trained models in `uzmorph/data/`

| step | script | output |
|---|---|---|
| reading priors θ, φ (EM over the top 400k corpus types) | `em_priors.py` | `priors.pkl` |
| class-bigram context model (running text; evaluation docs excluded) | `build_context.py` | `context.pkl` |
| paradigm support per lemma (duplicate-lemma rule) | `paradigm.py` | `paradigm.pkl` |
| capitalisation statistics (evaluation docs excluded) | `capstats.py` | `capstats.pkl` |
| proper-noun suffix prior | `name_sufprior.py` | `name_sufprior.pkl` |
| proper-noun list: mine candidates, verify against Wikidata | `names_mine.py`, `names_verify.py` | `names_list.tsv` |
| guesser ranking model | `build_guess_table.py` | `guess_model.pkl` |
| convert to the shipped pickle-free files (keys sorted, lossless pruning) | `export_models.py PHASE3_DIR GUESSER_DIR uzmorph/data` | `uzmorph/data/*.json.gz`, `name_sufprior.json`, `names_list.tsv` |

`rank_lib.py`, `names.py` and `uzb_guess.py` are the research versions of `uzmorph/ranker.py`, `names.py` and `guesser.py`. On all 2,970 word tokens of the 264 sampled evaluation sentences the package gives exactly the same top reading as the research pipeline. `export_models.py` drops only fields that the run-time code never reads (see the comments in it).

## mining/: lemma mining (new dictionary entries)
`mine_step1-3.py` (analogy suffix stripping, then filters for typos, fragments, foreign words and forms of known words), `select_lemmas.py`, `wiki_verify.py` / `wiki_select.py` (uz.wikipedia + Wikidata evidence bar), `build_lemmas_v5.py`, `mk_batch_lemmas.py`. The candidate batches and spot-check sheets are not included: they contain corpus example sentences.

## regression/: build chain and regression checks
`apply_v4.py` … `apply_v8.py`, `apply_batch.py`, `build_v4/5/6.sh` (lexicon and rule edits on top of the test build); `regress.py` (coverage gained/lost by type and token vs a previous build, plus the generation checks); `attribute.py` (gains per rule); `covlib.py`, `cov.py`, `parse.py`, `clean.py`, `rules1.py`; `lexc_additions.py` (lines added/removed vs upstream). v9.1 is one hand edit on top of v9 (two lexc entries commented out; see CHANGES.md), so it has no apply script.

## gencheck/
`gencheck.py`: generates 462 verb forms and counts spurious cooperative -ish- outputs (v8d 275, v9 0, v9.1 0); output in `../eval/evidence/gencheck.json`.

## coverage/
`dictionary_coverage.py` (raw coverage of any build) and `guesser_coverage.py` (dictionary + confident / unfiltered guesser, raw and anchored). Outputs are in `../eval/evidence/`; the anchoring is explained in `../eval/evidence/README.md`.

## triage/: phase-1 triage library and test build
`uzmorph_tb/` (lt-proc wrapper, casing, corpus readers, unknown-word type guesser, the R1–R39 rule catalogue) and `testbuild/` (apply the first bug fixes and the top-10 rules to a scratch copy of apertium-uzb, then compare builds). The numbered step scripts `00`–`05c` that produced the triage tables are not in this release.
