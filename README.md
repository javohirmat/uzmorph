# uzmorph: Uzbek morphological analyzer and generator

`uzmorph` is an improved version of the [Apertium](https://www.apertium.org/) Uzbek transducer (`apertium-uzb`), packaged with a Python layer:

- **Analyzer and generator.** The finite-state transducer (`apertium-uzb/`, built with lttoolbox/HFST) adds about 4,430 lexicon and rule lines (fixes, rules and new lemmas; not counting comments) to upstream `00522e3`, and comments out about 3,000 duplicate or junk lines. See [CHANGES.md](CHANGES.md); the count is in `eval/evidence/lexc_additions.json`.
- **Guesser.** A separate stem-slot transducer, plus a corpus-trained ranker that returns only confident guesses for words the dictionary does not know.
- **Proper-noun layer.** Splits capitalised unknown words into stem + suffixes using corpus capitalisation statistics, plus a small Wikidata-verified name list.
- **Reading ranker.** Trained without supervision on the uz-books-v2 corpus. It replaces Constraint Grammar `-1` for choosing the best reading: a prior plus a class-bigram context plus four rules.
- **Input in three scripts.** Official Latin, Cyrillic, and the 2026 Latin alphabet, converted by a rule-based transliterator.
- **UD-style output.** Each reading comes with lemma, UPOS and features.

Status: **0.9.0, research release.** Please read [Limitations](#limitations-and-caveats) before relying on the numbers.

## Install

The package calls `lt-proc` from lttoolbox. It does not need Apertium, HFST or CG3 at run time.

```bash
sudo apt install lttoolbox          # Debian/Ubuntu (macOS: see the Apertium installation wiki page)
pip install .                       # from a clone of this repository; no Python dependencies
python -m unittest discover tests   # ~3 s
```

Python ≥ 3.8. The prebuilt transducers and model files (12 MB) ship in `uzmorph/data/`.

## Quickstart

```python
import uzmorph

for t in uzmorph.analyze("Kecha doʻstlarim bilan Samarqandga bordik."):
    if t.is_word:
        b = t.best
        print(f"{t.text:12} {b.lemma:10} {b.upos:6} {b.feats}")
```
```
Kecha        kecha      NOUN   Case=Nom|Number=Sing
doʻstlarim   doʻst      NOUN   Case=Nom|Number=Plur|Poss=1Sg
bilan        bilan      CCONJ  _
Samarqandga  Samarqand  PROPN  Case=Dat|Number=Sing
bordik       bor        VERB   Number=Plur|Person=1|VerbForm=Fin|Mood=Ind|TAM=Past
```

More:

```python
import uzmorph

# ranked readings with scores
t = uzmorph.analyze("U kitob oʻqiyapti.")[2]
for r in t.readings:
    print(r.analysis, round(r.score, 2), r.source)

# Cyrillic input (script="auto" detects Cyrillic; tokens come back in Latin)
for t in uzmorph.analyze("Китобларимизни ўқидингизми?", script="cyr"):
    if t.is_word:
        print(t.text, t.best.analysis)

# unknown words: confident guesser, then the proper-noun layer
for t in uzmorph.analyze("Kecha Zarafshonbekni koʻrdim."):
    if t.is_word:
        print(t.text, t.known, t.best.analysis, t.best.source)

# generation
print(uzmorph.generate("kitob", "<n><pl><px1pl><abl>"))
print(uzmorph.generate("oʻqi", ["v", "tv", "prog", "p1", "sg"]))
```
```
oʻqi<v><tv><prog><p3><sg> -20.07 lexicon
oʻqi<v><tv><prog><p3><pl> -38.84 lexicon
Kitoblarimizni kitob<n><pl><px1pl><acc>
oʻqidingizmi oʻqi<v><tv><ifi><p2><pl>+mi<qst>
Kecha True kecha<n><nom> lexicon
Zarafshonbekni False Zarafshonbek<np><guess><acc> names-guess
koʻrdim True koʻr<v><tv><ifi><p1><sg> lexicon
['kitoblarimizdan']
['oʻqiyapman']
```

Command line (TSV: token, lemma, UPOS, feats, Apertium reading, source; a blank line between sentences; `--json` for JSON lines; `-n 0` for all readings; `--no-guess` for dictionary only). The whole input is analysed in one batch:

```
$ uzmorph analyze "Bolalar maktabga ketishdi."
Bolalar	bola	NOUN	Case=Nom|Number=Plur	bola<n><pl><nom>	lexicon
maktabga	maktab	NOUN	Case=Dat|Number=Sing	maktab<n><dat>	lexicon
ketishdi	ket	VERB	Number=Plur|Person=3|VerbForm=Fin|Mood=Ind|TAM=Past	ket<v><iv><ifi><p3><pl>	lexicon
.
$ echo "У кеча келди." | uzmorph analyze -n 2
U	u	DET	_	u<det><dem>	lexicon
U	u	PRON	Case=Nom|Number=Sing	u<prn><pers><p3><sg><nom>	lexicon
kecha	kecha	NOUN	Case=Nom|Number=Sing	kecha<n><nom>	lexicon
kecha	kecha	NOUN	Case=Nom|Number=Sing	kecha<n><attr>	lexicon
keldi	kel	VERB	Number=Sing|Person=3|VerbForm=Fin|Mood=Ind|TAM=Past	kel<v><iv><ifi><p3><sg>	lexicon
keldi	kel	VERB	Number=Plur|Person=3|VerbForm=Fin|Mood=Ind|TAM=Past	kel<v><iv><ifi><p3><pl>	lexicon
.
$ uzmorph generate oʻqi v.tv.prog.p1.sg
oʻqiyapman
```

The last example shows a known weakness: the top reading of *u* here is the determiner, not the pronoun. See below.

`Token` fields:
- `text`: the surface form as analysed (official Latin);
- `sent`: the sentence index;
- `is_word`;
- `known`: whether the main dictionary recognised the word (every part of a hyphenated word; always `False` for punctuation and numbers);
- `readings`: best first;
- `prefix`: the earlier parts of a hyphenated token, with their case kept (they are prepended to the lemma).

`Reading` fields:
- `analysis`: the Apertium reading of the head unit only (for a hyphenated token, its last part; an enclitic after a hyphen such as *-a*, *-yu* is not included), without the surface form;
- `lemma`, `upos`, `feats`;
- `score`: log scale, `None` for name readings;
- `source`: `lexicon`, `guesser`, `names-list` or `names-guess`.

`Analyzer(guess=True, names_level=1, ctx_weight=1.0)` exposes the options. `Analyzer.analyze_tokens(list_of_token_lists)` takes pre-tokenised input, and `Analyzer.lookup(words)` returns raw lt-proc output. Control characters are removed from the input; a token or word containing whitespace raises `ValueError`, as do `generate()` tags that are not of the form `<a><b>…` (or a list of tag names). `generate()` never returns outputs containing `#`, `@`, `*` or whitespace. If lt-proc is missing, fails or takes longer than 120 s, you get a `RuntimeError` saying so.

## Results

Every number in this section comes from a file in this repository: `eval/results/`, `eval/nonsense/` and `eval/evidence/`. The source file is named next to each table.

**Coverage.** Token coverage of the uz-books-v2 word-frequency list (types with ≥3 uses, every casing weighted by its corpus share):

| system | coverage (raw) | coverage (anchored) |
|---|---|---|
| upstream apertium-uzb 00522e3 | 86.15 | 87.51 |
| this analyzer (dictionary) | 89.33 | **90.69** |
| this analyzer + confident guesser | 93.44 | **94.80** |
| this analyzer + unfiltered guesser (not the package default) | 94.52 | 95.88 |

- **Sources:** `eval/evidence/dictionary_coverage.json` (every build, from `tools/coverage/dictionary_coverage.py`) and `eval/evidence/guesser_coverage_v91.json` (`tools/coverage/guesser_coverage.py`). The per-build regression reports (types and tokens gained and lost, generation checks) are `eval/evidence/regress_*.json`.
- **Anchoring.** The first survey of upstream measured 87.51%, with an earlier version of the same measurement. The regression tool used for every later build gives 86.15% for the same upstream build. So "anchored" means each raw figure plus a constant 1.36 points (87.51 − 86.15), which keeps all figures on the scale of the first survey. Gains are identical on both scales.
- **The guesser's coverage is acceptance, not correctness.** On a sample of 100 confident guesses (word types drawn in proportion to corpus frequency, each judged individually; not by a native speaker), 57 were fully right (63 if adjective/participle-vs-noun confusions are accepted): `eval/evidence/guesser_precision_sample100.json` (words and judgements only).

**Top-1 accuracy.** Measured on the held-out test split: 156 sentences, 1,731 scored tokens, four genres. Every token counts, so an unanalysed token is wrong. Source: `eval/results/split_scores.md`, section "lat / test / all", "best" column.

| system | lemma+feats | lemma | UPOS* |
|---|---|---|---|
| upstream apertium-uzb 00522e3 + CG `-1` (no guesser) | 79.7 | 86.5 | 75.4 |
| our previous build (v8d analyzer + CG `-1` + guesser) | 83.9 | 90.4 | 77.1 |
| **uzmorph 0.9** (v9.1 analyzer + ranker + guesser + proper-noun layer) | **93.5** | **96.1** | 79.1 |
| uzmorph 0.9, dictionary words only (no guesser, no names) | 88.0 | 90.5 | 74.1 |
| [ZirhUzMorph](https://github.com/XojiakbarJamoldinov/ZirhUzMorph) 0.1.1, all analyses incl. unknown-stem guesses | 87.8 | 92.2 | 57.3 |
| ZirhUzMorph 0.1.1, known stems only | 83.5 | 87.9 | 56.9 |

\*UPOS is not comparable across tools: ZirhUzMorph only distinguishes N and V.

- **By genre (test, lemma+feats).** The four genres add up to the 1,731 tokens. The names row is a subset across genres (gold PROPN tokens), not a fifth genre.

  | genre | tokens | upstream + CG | uzmorph | Zirh |
  |---|---|---|---|---|
  | books | 540 | 80.6 | 91.9 | 90.4 |
  | wiki | 437 | 80.3 | 95.7 | 86.3 |
  | news | 340 | 78.5 | 93.8 | 86.2 |
  | telegram | 414 | 78.7 | 93.0 | 87.2 |
  | *subset: proper names* | *179* | *54.2* | *96.1* | *86.6* |

- **Dev split** (104 sentences, 1,062 tokens): uzmorph 94.1, Zirh 87.5, upstream + CG 78.1.
- **Scripts:** the Cyrillic and 2026-Latin copies of the evaluation set were transliterated from the Latin gold by our own transliterator, so the identical scores (`split_scores.md`, sections "cyr" and "new") only show that the round trip back to Latin is lossless on these sentences. They are not an independent test on natively written Cyrillic text.
- **Ranker components** are measured on dev (`eval/results/ablation_dev.md`).
- **The released package** reproduces the "uzmorph 0.9" rows exactly: `eval/results/score_uzmorph.md`, written by `eval/scripts/score_uzmorph.py`.
- The analyzer fix for hyphenated compounds (v9.1, see CHANGES.md) changed no scored token's result. Test and dev are the same as with v9.

**Rejecting non-words.** 299 generated non-words with zero corpus hits. Lower is better. Source: `eval/nonsense/results_v91.md`.

| input | system | accepted |
|---|---|---|
| lower-case | uzmorph, dictionary only | **1%** |
| lower-case | uzmorph + confident guesser (package default) | 17% |
| lower-case | uzmorph + unfiltered guesser (research setting) | 90% |
| lower-case | ZirhUzMorph, known stems | 15% |
| lower-case | ZirhUzMorph, any segmentation (incl. unknown-stem guesses) | 85% |
| Capitalised, mid-sentence | uzmorph, dictionary + confident guesser | 13% |
| Capitalised, mid-sentence | uzmorph default (+ proper-noun layer) | 100% |

- **How Zirh is counted.** For every string, ZirhUzMorph returns either a segmentation or the bare word marked `[?]`. A bare `word[?]` (46 of the 299) is counted as a rejection, and any segmentation as acceptance. Counting the bare `word[?]` as output too would give 100%.
- **Neither our unfiltered guesser nor Zirh's unknown-stem guesses is a rejection test:** both analyse almost any string by design.
- **The proper-noun layer accepts every capitalised unknown word in mid-sentence** as a `<guess>` name (source `names-guess`), so capitalised non-words are always accepted. Use `names_level=0` to switch it off.

**Generation.** ZirhUzMorph has no generator. Ours regenerates the standard forms: 0 of 462 checked verb forms give a spurious cooperative -ish- variant (v8d: 275; upstream has the same bug, BUGS_UPSTREAM.md #1). Source: `eval/evidence/gencheck.json`, from `tools/gencheck/gencheck.py`.

## Limitations and caveats

- **The gold is mostly model-built and only partly human-checked.** Of the 2,894 word tokens:
  - 1,525 labels were auto-accepted where the two analysers agreed unambiguously (or the word was closed-class). A 150-token spot-check of these found 6 errors (4.0%), which were fixed.
  - About 1,120 labels were adjudicated in context by an AI assistant and were never reviewed by a person.
  - 250 rows (the hardest disagreement and low-confidence tokens) were checked by a native speaker.
  
  This can favour the conventions of the tools the gold was built from. Details are in `eval/README.md`.
- **In-domain advantage on books.** Our lexicon additions and ranker statistics come from the same book corpus as the "books" genre. Only the class-bigram context model and the capitalisation statistics were trained with the evaluation documents excluded. The corpus reading prior, the paradigm sizes (duplicate-lemma rule), the other model files and the lemma mining used the whole corpus, including those documents. Books is also where our margin is smallest (91.9 vs 90.4).
- **Singular-default convention.** Finite 3rd-person verbs are labelled Number=Sing unless the plural is overt (-dilar, -ishdi, …). Our ranker has a rule for exactly this convention. Without it, dev lemma+feats drops from 94.1 to 87.5, which is exactly Zirh's 87.5 (`ablation_dev.md`, row "FINAL − singular default"). Zirh needs no such rule: our mapping of its tags (`eval/scripts/scheme.py`) already gives an unmarked 3rd-person form Number=Sing. Another convention (e.g. "ambiguous") would change the comparison.
- **UPOS is weak (79%).** Pronoun vs determiner vs noun is often wrong: *u* is ranked DET, *men*, *ular* and *oʻz* NOUN. Adjective vs noun is also unreliable (*yangi* → NOUN). The lemma+feats metric does not see most of these errors (Number is not scored on pronouns). The corpus EM prior collapses some of these homographs. This is the first thing to fix.
- **Guesser readings are often wrong** (57–63% fully right), e.g. *oʻqiganmisiz* → `oʻqiganmi<n>…<guess>`. Use `--no-guess` / `Analyzer(guess=False, names_level=0)` when precision matters.
- **The proper-noun layer is a fallback**, not a recogniser (see above).
- **Small test set.** 1,731 tokens give roughly ±1.2 points (95% CI, token-level; wider if sentence clustering is taken into account) on the headline number.
- **Apostrophes.** Input is normalised to oʻ/gʻ (U+02BB) and tutuq ʼ (U+02BC). The transducer itself still only accepts U+02BC for the tutuq (BUGS_UPSTREAM.md #21), so normalise first if you call the `.bin` directly.
- **Hyphenation.** `analyze()` rejoins words split by a hyphen at a line end (*kito-⏎blarim* → *kitoblarim*; before a capital the hyphen is kept: *ilmiy-⏎Amaliy* → *ilmiy-Amaliy*). A real hyphenated compound that happens to be broken at its hyphen before a lower-case letter is joined without the hyphen.
- **Tokens starting with a digit** (*2025-yilda*, *15*) are tokenised but not analysed (`is_word=False`), as in the evaluation.
- The research scripts in `tools/` and `eval/scripts/` need the original working data and are provided for transparency. They are not a one-command reproduction.

## Building the transducers

```bash
sudo apt install lttoolbox lttoolbox-dev hfst cg3 cg3-dev apertium apertium-dev autoconf automake pkg-config make gawk
cd apertium-uzb
./autogen.sh && make -j4
cp uzb.automorf.bin uzb.autogen.bin uzb_guesser.automorf.bin ../uzmorph/data/
```

A clean build from this tree reproduces the shipped `.bin` files byte for byte (tested on Ubuntu with apertium 3.9, lttoolbox 3.7, hfst 3.16). The full analysis pipeline also builds `uzb.rlx.bin` and the Apertium modes (`modes/uzb-morph.mode` etc.).

To regenerate the ranker, name and guesser models from the corpus, run the scripts in `tools/models/` (see `tools/README.md`). Then run `python tools/models/export_models.py PHASE3_DIR GUESSER_DIR uzmorph/data`, which writes the shipped `*.json.gz`, `name_sufprior.json` and `names_list.tsv`. Keys are sorted alphabetically, so no file keeps corpus order.

## Source code of the bundled transducers (GPL-3.0)

The wheel ships three compiled transducers in `uzmorph/data/` (`uzb.automorf.bin`, `uzb.autogen.bin`, `uzb_guesser.automorf.bin`). They are object code built from the modified apertium-uzb source, GPL-3.0-only.
- **Corresponding Source:** the `apertium-uzb/` directory of this repository (tag `v0.9.0`: https://github.com/javohirmat/uzmorph/tree/v0.9.0/apertium-uzb) and of the sdist `uzmorph-0.9.0.tar.gz`, which is published alongside every wheel. Upstream base: https://github.com/apertium/apertium-uzb commit `00522e3`. All changes are listed in [CHANGES.md](CHANGES.md).
- **Rebuilding:** see [Building the transducers](#building-the-transducers). A clean build reproduces the shipped files byte for byte.
- **Written offer:** [uzmorph/data/SOURCE.md](uzmorph/data/SOURCE.md) (installed with the package) contains the three-year written offer for the Corresponding Source, plus these pointers.

## Repository layout

| path | contents |
|---|---|
| `apertium-uzb/` | analyzer source (modified apertium-uzb; upstream AUTHORS, COPYING, README kept) |
| `uzmorph/` | Python package; `uzmorph/data/` = transducers and models |
| `tests/` | fast unit tests |
| `eval/` | scoring scripts, protocol, results tables, non-word list, `evidence/` files behind the README numbers (the gold sentences are private) |
| `tools/` | research scripts: model building, lemma mining, regression, triage |
| `CHANGES.md` | everything changed relative to upstream |
| `BUGS_UPSTREAM.md` | draft bug report for apertium-uzb (not filed) |
| `REVIEW.md` | pre-release review checklist |

## Data and licences

| component | source | licence |
|---|---|---|
| `apertium-uzb/`, transducers | Apertium apertium-uzb (F. M. Tyers et al.) + our changes | GPL-3.0-only |
| Python package, tools, eval scripts | this project | GPL-3.0-only |
| ranker, guesser and capitalisation models (`*.json.gz`) and the proper-noun suffix prior (`name_sufprior.json`) | counts derived from [tahrirchi/uz-books-v2](https://huggingface.co/datasets/tahrirchi/uz-books-v2) (dataset card: MIT) | GPL-3.0-only, like the package. They are counts only: word types, Apertium tags and suffix strings with frequencies or probabilities. They contain no sentences or running text. |
| `names_list.tsv` | stems mined from the corpus, verified against Wikidata (ids included) | GPL-3.0-only, like the package (the Wikidata ids it cites are CC0) |
| `eval/nonsense/nonwords.tsv` | generated strings | GPL-3.0-only |

Run-time dependency: lttoolbox (GPL-2.0-or-later), called as a separate program. The evaluation compared against ZirhUzMorph (MIT), which is not bundled.

## Citation

> There is no paper yet. Please cite this repository (see `CITATION.cff`) and Apertium:
> ```
> @misc{uzmorph2026, title={uzmorph: an improved Apertium-based morphological analyzer for Uzbek}, author={Matniyazov, Javohir}, year={2026}, note={version 0.9.0}, url={https://github.com/javohirmat/uzmorph}}
> ```

Contact (including requests for the private evaluation set): Javohir Matniyazov, javohirmatniyazovv@gmail.com.

## Licence

GPL-3.0-only (see `LICENSE`), matching upstream apertium-uzb. This applies to the whole repository: analyzer, transducers, Python package, tools and evaluation scripts.
