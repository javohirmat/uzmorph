# Changes to apertium-uzb

## 0.9.0 (2026-10-17)

Base: [apertium/apertium-uzb](https://github.com/apertium/apertium-uzb) commit `00522e3` (2025-05-16), GPL-3.0-only.
Changed source files: `apertium-uzb.uzb.lexc`, `apertium-uzb.uzb.twol`, `apertium-uzb.uzb.guesser`, `Makefile.am`, plus the new file `coopfilter.regexp` (each carries a MODIFIED VERSION notice). Other differences from the upstream tree: `README.md`, a symlink to `README` upstream, is a regular file with the same content here; the dangling symlink `eval/evaluate-morph.py` (it points into a sibling `apertium-tyv` checkout) was removed. All other files are unchanged upstream files.
Edits in the lexc and twol files are marked with comments (`R*` test build, `F*` v4/v5 fixes, `G*`/`H*`/`P*` rules, `v5 G1` -ish- fix). Run `git diff --no-index` against an upstream checkout for the exact diff.

Coverage below is token coverage over the uz-books-v2 word-frequency list (types with ≥3 uses), using `lt-proc -w`. Figures are anchored to the first survey's 87.51% for upstream (anchored = raw + 1.359; see `eval/evidence/README.md`). Raw values for every build are in `eval/evidence/dictionary_coverage.json` (upstream 86.151 → v8d 89.291 → v9.1 89.328).

| build | what | coverage |
|---|---|---|
| upstream 00522e3 | | 87.51 |
| test build | bug fixes R11, R12, R13, R17, R20, R32, R34, R39; undeclared tags (`fut2`, `gna_when`, `gna_neg`, `sp`) declared; top-10 triage rules R3, R4, R5, R7, R8, R9, R10, R15, R29 (-ganlik/-maslik, +ki, +gina, non-voicing stems, attested -roq, -gacha, -(u)vchi participle, contracted copula, archaic forms) | 88.59 |
| v4 | F1 hyphen + `-da` regression of the test build fixed (POSTADV-END); F2 `uq` without -uv/-uvchi; F3 junk verbs `tupla`, `tugdir` removed; F4 ye+{E} → yeya; 400 corpus-ranked lemmas | 89.88 |
| v5 | 571 lemmas (spot-checked batch + Wikipedia/Wikidata-verified); F5 3,022 exact duplicate lexc entries commented out; F6 junk verbs `bula`, `ut` removed (frequent forms kept as `<mistake>`); F7 `haqidagi` = haqida<post><attr>; F8 `deya` generated; F9 `topta`; F10 elidable stem vowel {ı} (bagʻri, ogʻzi); F11 junk noun `itarmoq` removed | 90.29 |
| v6, v6b | OTM abbreviation; analysis-only spelling variants (ustivor, talofat, …); `nari` -roq; -ayotganlik; -(a)qol; 428 Wikipedia-verified lemmas | 90.41 |
| v7 | H1 -(a)ver; H2 -mayotgan; H3 case on -roq adverbs; H4 -(a)yap after consonants; H5 -(a)yotib; H6 colloquial -(u)vdi; H7 archaic -dur; H8 durang; batches 3–6 (1,226 lemmas) | 90.60 |
| v8 … v8d | P1 present continuous generates -yap (ketyapti), {a}yab analysis-only; P2 -moq + possessive q→gʻ (bilmogʻi); P3 -armish; P4 archaic -mak; P5 optative fix (qaraylik; no *qarayylik*); P6 -guncha; batch-2 lemmas and variants; `alayno A1→A1` paradigm typo | 90.65 |
| v9 | `v5 G1`: the cooperative -ish- filter (`coopfilter.regexp`) is now composed **before** twol, so it applies; one lexc line restores `<vaux><coop>` -ish- forms. Coverage vs v8d: 0 types lost, 0 gained. Generator: 0 of 462 checked verb forms produce a spurious -ish- variant (v8d: 275). | 90.65 |
| **v9.1** (this release) | The hyphen-initial clitic entries `%-a:%-a QST` and `%-ya:%-ya QST` are commented out (BUGS_UPSTREAM.md #23). lt-proc's longest match took *-a* from the start of the second part of hyphenated compounds (*ilmiy-amaliy* → ilmiy + -a + \*maliy). The clitic is now read as `-` + `a`/`ya`, and the Python layer attaches it to its host. vs v9: 14,474 types / 581,148 tokens gained (*mart-aprel*, *30-yanvar*), 1,071 types / 13,557 tokens lost (mostly junk splits like *st-yasi*); all 52 generation checks pass; 0/462 spurious -ish- forms; no scored evaluation token changes. | 90.69 |

Every step was regression-checked (`tools/regression/regress.py`; the v8d, v9 and v9.1 reports are in `eval/evidence/`): types and tokens lost or gained against the previous build, random 50-type samples of the gains, and generation checks (52 positive and must-not-generate checks at v8d; all pass at v9 and v9.1).
- **Intended losses vs upstream** (at v9): 751 types / 29,004 tokens. These are typo-verb analyses (tupla-, ut-, tugdir-, bula-, uquvchi…), junk strings (univ, yea, rail) and 6 *-yy* strings that only the old optative bug accepted. At v9.1 the loss vs upstream is 1,796 types / 42,436 tokens; the extra 1,071 / 13,557 are the hyphenated strings that were only analysed through the `-a`/`-ya` entries (e.g. *st-yasi*, *f-yat*).
- **Analysis-only additions** (`Dir/LR`, never generated): colloquial, archaic and variant spellings.

Separate guesser transducer (`uzb_guesser.automorf.bin`): the upstream {🂡} stem-slot guesser with a rewritten stem pattern (≥3 letters, contains a vowel, ʻ/ʼ only where valid). The main transducer is unaffected.

Python layer (not part of apertium-uzb): apostrophe normalisation, a ranked guesser, a proper-noun layer and a corpus-trained ranker that replaces CG `-1` for choosing the best reading. See `README.md`.

Size of the change: 4,434 non-comment lines added to `apertium-uzb.uzb.lexc` and 3,093 upstream lines removed or edited (most commented out as duplicates or junk), from `tools/regression/lexc_additions.py` (`eval/evidence/lexc_additions.json`).
