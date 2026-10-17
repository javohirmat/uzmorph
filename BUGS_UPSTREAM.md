# Draft: bug report for apertium-uzb (not yet filed)

> DRAFT for review. Nothing has been reported upstream. Target: https://github.com/apertium/apertium-uzb/issues (one issue per item, or a single tracking issue).
> Line numbers refer to commit `00522e3`. Every example below was re-run on binaries built from a clean `00522e3` checkout (`lt-proc -w uzb.automorf.bin` for analysis, `lt-proc -g uzb.autogen.bin` for generation) and reproduces there. Each fix is in this repository's `apertium-uzb/` (see CHANGES.md), and we are happy to send PRs.

## Morphotactics and phonology

1. **Cooperative -ish- filter never applies (generation over-produces -ish- forms).** The `.twoc` that should allow `[-coop]` only together with a bare `[+p3pl]` is composed *after* twol, and twol has already deleted both flags. As a result `oʻqi<v><tv><prog><p1><sg>` generates *oʻqiyabman/oʻqishayabman* (see also #2), and `qil<v><tv><neg><ifi><p3><sg>` gives *qilmadi/qilishmadi*. In our check, 275 of 462 verb forms had a spurious -ish- variant.
   *Fix:* compose the flag filter (`~[ $[-coop] & ~$[+p3pl] ]`) onto the lexc output before twol (`coopfilter.regexp` and two Makefile rules), and add `%<vaux%>%<coop%>:%>%{i%}sh` so -ish- forms of auxiliaries stay analysable. Result: 0/462 spurious forms, no coverage change.
2. **Present continuous generates -yab.** The generable PRES-CONT line is `{a}yab`, so `ket<prog><p3><sg>` → *ketayabdi* and `oʻqi<prog><p1><sg>` → *oʻqiyabman*. The standard -yap is analysis-only (lexc ~765–768), and *kelayapti*-type forms after consonants are not accepted at all. *Fix:* make `yap` generable and `{a}yab` analysis-only; add -(a)yap after consonant stems as analysis-only.
3. **Optative after vowel stems doubles the y:** `de<opt><p1><pl>` → *deyylik*, `qara…` → *qarayylik*, and *qaraylik* is not analysed. *Fix:* `{a}y/{a}yin/{a}ylik` without epenthetic y after a vowel.
4. **{D}:t after p applies everywhere** (twol): *gaptagi* is accepted while *gapdagi*, *tipdagi* are rejected. *Fix:* only before i (causative -tir-, -yapti).
5. **ʻ is in the twol Cons set,** so `obroʻ<n><px3sp><nom>` generates *obroʻi*, and *obroʻsi* is rejected. *Fix:* remove ʻ (gʻ-final stems unaffected).
6. **-(u)v verbal noun:** `{u}` only maps to i, so `kel<v><iv><ger>` → *keliv* and *yondashuv* is not analysed. (*yondashuv* is rejected.) *Fix:* separate archiphoneme {U} (u; o after a deleted stem-final a: tanlov), stem-final a/i deleted before it.
7. **ye-/de- glide:** `ye<v><tv><aor><p3><sg>` → *yeadi*, and *yeydi* is rejected. The -(y)a converb is wrong after these stems: `ye<v><tv><prc_impf>` → *yea* and `de<v><tv><prc_impf>` → *dey* (expected *yeya*, *deya*; *yeya* is rejected, and *deya* is analysed only as the lexical adverb/conjunction). *Fix:* {E}:y across a deleted {й}; {й}:y before -ish, the passive and {U}; `ye/de + {E}` = yeya/deya.
8. **VERB-TV passive has a literal i** (`%>i%{L%}`, line 603): *koʻzlailgan* instead of *koʻzlangan*. *Fix:* `%>%{i%}%{L%}`.
9. **ATTR-SUBST plural uses Cyrillic р (U+0440)** (lines 993–994, copied from apertium-kaz): Cyrillic-r *uydagilaр* is analysed, while *uydagilar* is not.
10. **-gach has a literal g:** *chiqgach* accepted, *chiqqach* rejected. *Fix:* `%{G%}ach`.
11. **-moq + possessive does not voice q:** `boʻl<v><iv><ger_inf><px3sp><nom>` → *boʻlmoqi* (also analysed), *boʻlmogʻi* rejected.
12. **-(a)r future (`<fut2>`, lexc line 776):** the only line is in LEXICON AORIST, analysis-only (`Dir/LR`), and the tag is not declared (see #16). So the forms that are accepted come out with an escaped tag (*kelarman* → `kel<v><iv>\<fut2\><p1><sg>`), nothing can be generated, the 3rd person *kelar* gets only the participle reading, and common forms are rejected: *derman* (vowel stem), *kelmasman* (negative -mas).
13. **No elidable stem vowel:** `ogʻiz<n><px3sp><nom>` → *ogʻizi* (*ogʻzi* rejected), `burun…` → *buruni*, `oʻgʻil…` → *oʻgʻili*; *oʻgʻli* is analysed only through a spurious stem `oʻgʻl`. (*bagʻir* is not in the upstream lexicon at all: *bagʻri* is rejected.) *Fix:* elidable {ı} (bagʻri, ogʻzi, ogʻizda), plus the missing stems.
14. **k/q voicing is obligatory for every vowel + k/q stem:** *huqugʻi*. Monosyllables and many loans do not voice. *Fix:* mark non-voicing stems with {K}/{Q}.
15. **{s} deleted after y:** *asosiyi*, *vodiyi* accepted; *asosiysi*, *vodiysi* rejected (open in this release).

## Lexicon

16. **Undeclared multichar tags** (`fut2`, `gna_when`, `gna_neg`, `sp`). Declaring `gna_when` also makes -gach generable.
17. **Paradigm typo `alayno A1→A1`** (hfst-lexc "sublexicon not defined" warning).
18. **About 3,000 duplicate lexc entries:** 3,017 lines repeat an entry already present in the same LEXICON (ignoring whitespace and comments). (Our v5 commented out 3,022 lines; it was counted on our test build, where a few lines had become identical after other edits.)
19. **Junk entries that accept common typos as words:** verbs `tupla` (*tupladi*, typo of *toʻpladi*), `tugdir` (*tugdirdi*, of *tugʻdirdi*), `bula` (*buladi*, of *boʻladi*), `ut` (*utgan*, *utib*, of *oʻtgan*, *oʻtib*); noun `itarmoq` (the infinitive of *itar-*).
20. **haqidagi is not analysed** (`*haqidagi`), although *haqida* is a postposition; expected `haqida<post><attr>`.

## Spelling / input

21. **Tutuq only as U+02BC.** `spellrelax` targets ’ (U+2019), but the lexicon uses ʼ (U+02BC), so *ta’lim*, *ta'lim* and *ta‘lim* are split into *ta* + *lim* and counted as analysed. Corpora (e.g. uz-books-v2) write ’. (Not fixed in the transducer here; our Python layer normalises apostrophes before lookup.)

## Guesser

22. **Stem pattern never matches oʻ/gʻ:** `apertium-uzb.uzb.guesser` defines vowels/consonants with ASCII `'`, while the lexicon uses ʻ (U+02BB). *Fix:* a letter class with ʻ/ʼ, ≥3 letters and at least one vowel.
## Hyphenated words

23. **Hyphen-initial clitic entries break hyphenated compounds.** The lexc words `%-a:%-a QST` and `%-ya:%-ya QST` (lines 1395–1396) make lt-proc's longest match take *-a* / *-ya* from the start of the second part: *ilmiy-amaliy* → `ilmiy` + `-a<qst>` + `*maliy`; also *Oʻzbekiston-Amerika* (`-A<qst>` + `*merika`) and *Abu-Ali* (`-A` + `li<mistake>`). *Fix:* remove the two entries; the clitic in *Keldingiz-a* is still read as `-` + `a`. In this release the Python layer attaches it to its host.
