# SPDX-License-Identifier: GPL-3.0-only
"""Catalogue of morphology gaps in apertium-uzb 00522e3, with pattern detectors.

Each rule names one fix in the lexc/twol that would recover a family of words. A detector
proposes (rule, base, ...) decompositions of an unknown lower-cased word; the decomposition
fires when Apertium analyses the base with the required part of speech. Detectors are cheap
enough to run over every unknown type in work/all_types.tsv.gz.

Detector hits are candidates, not decisions: a hit says "this word looks like base + the
missing morpheme and the base is known". Precision per rule is measured on the reviewed
top-2000 list (05_triage_finalize.py) and used to discount the full-corpus impact.

All proposed tags are AI proposals for a native speaker and the maintainers to review.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .textnorm import OKINA, TUTUQ

O_ = "o" + OKINA
G_ = "g" + OKINA
VOWELS = "aeiou"


_VERB_REST = r"^(gan|adi|ady|ib|ish|ma|may|sa|di|ar|uvchi|ayotgan|adigan|moq|gach|guncha|ishi|ishga|ishda|ishni|ishdan)"


def ends_in_vowel(s: str) -> bool:
    return bool(s) and (s[-1] in VOWELS or s.endswith(O_))


# ----------------------------------------------------------------------------- catalogue
@dataclass
class Rule:
    id: str
    name: str
    where: str          # lexc/twol location at 00522e3
    diagnosis: str      # why it fails now (checked with lt-proc)
    fix: str            # proposed change (not applied)
    tags: str           # proposed analysis pattern
    examples: str
    kind: str = "morphotactics"   # morphotactics | twol | lexicon-marking | tokenizer | casing | spelling
    ask: str = ""       # native-speaker question, if any
    decision: str = ""  # the project owner's answer, if given


RULES: dict[str, Rule] = {r.id: r for r in [
    Rule("R1", "attributive -(da)gi after postpositions",
         "LEXICON POST (line 490); haqida, boʻyicha are POST-NOM (lines 32215, 4421)",
         "POST ends in `%<post%>: #`, so nothing can follow a postposition; nouns reach -dagi through GENERAL-POSSESSIVE-ETC.",
         "Add `%<post%>%<attr%>:%>gi #` for postpositions ending in -da (haqida, ishtirokida-type are nouns) and "
         "`%<post%>%<attr%>:%>dagi #` for the others (boʻyicha), plus `%<post%>%<attr%>%<subst%>` into SUBST for haqidagilar.",
         "haqida<post><attr>", "haqidagi, boʻyichadagi, toʻgʻrisidagi"),
    Rule("R2", "copula 3pl -lar",
         "LEXICON Copula (line 1131) → V-PERS-S2 (line 811) / V-PERS-S1 (line 800)",
         "V-PERS-S2 and V-PERS-S1 give 3pl only as an empty string or `%[%+p3pl%]`; in .twoc that symbol only licenses "
         "the cooperative -ish- plural (kelishdi) and has no surface form, so edi/ekan/emas never take -lar.",
         "Give the copula its own person lexicon with `%<p3%>%<pl%>:%>lar`, used by `e<cop><ifi>`, `e<cop><aor><evid>`, "
         "`e<cop><neg><aor>` and -dir (`%<p3%>%<frm%>%<pl%>:dirlar`). Do not add -lar to CLIT-COP after nouns (kitoblar would get a spurious copula reading).",
         "e<cop><ifi><p3><pl>", "edilar, ekanlar, emaslar, egadirlar, kelgandilar"),
    Rule("R3", "-lik after -gan / -mas / -ish (verbal nouns)",
         "NON-FINITE (line 671), GERUND (line 708); <ger_perf> (line 226) is used only by the copula (ekanlik, LEXICON "
         "Copula line 1134), <ger_ppot> (line 227) is unused",
         "No continuation lexicon produces -ganlik or -maslik (about 25 such words exist as whole N1 entries, e.g. "
         "oʻqiganlik, ishonmaslik); apertium-kaz has `%<ger_perf%>:%>%{G%}%{A%}н%>%{L%}%{I%}%{K%} GER-INFL` "
         "and `%<neg%>%<gpr_ppot%>:...ст%{I%}%{K%}`.",
         "In GERUND: `%<ger_perf%>:%>%{G%}anlik FULL-NOMINAL-INFLECTION ;`, `%<neg%>%<ger_perf%>:%>ma%>%{G%}anlik …`, "
         "`%<neg%>%<ger_ppot%>:%>maslik …`, and for the copula `e%<cop%>%<neg%>%<ger_ppot%>:emaslik …`. Use the noun "
         "inflection, whose possessives carry the %{ʻ%} that makes k→g before a vowel (boʻlganligi); GER-INFL's "
         "possessives lack it (see R33) and %{K%} only maps to k. The existing copula path shows the problem: "
         "e<cop><ger_perf><px3sp><nom> generates *ekanliki* (9 uses in the corpus), while ekanligi (182,921 uses) is "
         "recognised only through a separate ekanlik N1 entry.",
         "boʻl<v><iv><ger_perf><px3sp><nom>; boʻl<v><iv><neg><ger_ppot><px3sp><nom>",
         "boʻlganligi, boʻlmasligi, qilmaslik, emasligi, boʻlmaganligi"),
    Rule("R4", "clitic -ki after predicatives, adverbs and conjunctions",
         "LEXICON CLITICS (line 917) holds `+ki<cnjadv>`; only finite verb person lexicons (PERS, PERS2, PERS3) reach it",
         "A1/N1/ADV/CA/POST paths end in CLITICS-INCL-COP or `#`, which do not contain -ki; every entry in "
         "LEXICON IMPERATIVE except the archaic -gay line (741, which goes to PERS) also ends in `#`, so qarangki, bilingki fail too.",
         "Add `%+ki%<cnjadv%>:ki #` to CLITICS-NO-COP (reached by nominals and predicatives) and to ADV/CA/POSTADV/MOD "
         "continuations; keep it out of attributive -gi/-ki on time nouns (R26).",
         "kerak<adj>+ki<cnjadv>", "kerakki, shundaki, mumkinki, lozimki, afsuski, borki, negaki"),
    Rule("R5", "restrictive -gina / -kina / -qina attached",
         "LEXICON CLIT-GHANA-ETC (line 945)",
         "The particle is encoded as a separate word `% %{G%}ana` (a space, then gana), which reads like the Kazakh "
         "ғана; the attached Uzbek spelling faqatgina, shugina is not produced. birgina, ozgina exist only as whole words.",
         "Replace or complement with `%+gina%<postadv%>:%>%{G%}ina #` (gina after vowels and voiced consonants, kina after k, "
         "qina after q), reachable after adverbs, pronouns, numerals, postpositions, case forms and converbs.",
         "faqat<postadv>+gina<postadv>", "faqatgina, anchagina, bilangina, hozirgina, boʻlgandagina",
         ask="Is restrictive -gina always written attached (faqatgina), and is the separate 'gana' ever correct in Uzbek?"),
    Rule("R6", "suffixes after numbers written in digits",
         "LEXICON NUM-DIGIT (line 1281); ordinal lines commented out (1287-1289)",
         "NUM-DIGIT allows only bare digits; 100dan, 5ta, 3-sinf need case, -ta, -inchi after the digits.",
         "NUM-DIGIT → optional `%-` then the NUM continuation (case, -ta, -(i)nchi, -gacha, px). Pair it with the tokenizer change T1.",
         "100<num><abl>; 5<num><cl>", "100dan, 100-dan, 5ta, 2024-yilgacha"),
    Rule("R7", "k/q stems that do not voice before vowels",
         "twol rule 'intervocalic stem-final k & q voice' (apertium-uzb.uzb.twol, <=> rule)",
         "The rule is obligatory for every vowel+k/q stem, so huquq+i must surface as huqugʻi; huquqi is rejected. "
         "Arabic and Russian loans (huquq, haq, ittifoq, ishtirok, axloq, blok) do not voice.",
         "Mark non-voicing stems in the lexicon with the already declared archiphonemes `%{Q%}`/`%{K%}` (twol: `%{Q%}:q`, "
         "`%{K%}:k`, outside the voicing rule), e.g. `huquq:huqu%{Q%} N1`.",
         "huquq<n><px3sp><nom>", "huquqi, haqi, ittifoqi, ishtirokida, axloqi", kind="lexicon-marking"),
    Rule("R8", "comparative -roq",
         "A1/A2 (lines 446-470: 'FIXME: add comparative'); tag <comp> declared (line 50)",
         "No adjective or adverb lexicon produces -roq; only a few whole words exist (koʻproq, ichkariroq, ishonchliroq).",
         "A1/A2/ADV: `%<adj%>%<comp%>:%>roq CLITICS-INCL-COP ;` `%<adj%>%<comp%>%<subst%>:%>roq SUBST ;` "
         "(q→gʻ before vowels: aniqrogʻi), as apertium-kaz does with -{I}р{A}{K}.",
         "tez<adj><comp>", "tezroq, kamroq, yaxshiroq, kattaroq, aniqrogʻi"),
    Rule("R9", "terminative -gacha / -kacha / -qacha",
         "CASES / CASE-COMMON (lines 975-1238)",
         "No case lexicon has -gacha; only a few whole words (yilgacha, yoshgacha) and ertaga+cha exist.",
         "New case tag `<term>`: `%<term%>:%>%{G%}acha CLITICS-NO-COP` in CASES, CASE-COMMON, GER-CASE-NO_COPULA and "
         "pronoun lexicons. (Alternative without a new tag: `<dat>+cha<post>`. Today ertagacha gets `ertaga<n><nom>+cha<post>` "
         "because ertaga is a noun entry; a few -gacha words are whole entries: yilgacha, yoshgacha, hozirgacha.)",
         "maktab<n><term>", "maktabgacha, oxirigacha, kungacha, bizgacha, kechgacha"),
    Rule("R10", "agentive participle -(u)vchi",
         "NON-FINITE (line 671); no tag yet",
         "No continuation lexicon produces -(u)vchi; it exists only in about 200 lexicalised whole-word entries, mostly "
         "nouns (oʻqituvchi, oʻquvchi) and a few adjectives (biluvchi, yemiruvchi).",
         "Add `%<gpr_pot%>:%>%{u%}vchi SUBST-like continuation` (tag as apertium-kaz/tat/kir -ушы/-учы), with allomorphs "
         "-uvchi after consonants, -ovchi after -a stems (belgila→belgilovchi), -uvchi replacing -i (oʻqi→oʻquvchi); needs the R11 twol fix.",
         "kel<v><iv><gpr_pot>", "keluvchi, turuvchi, foydalanuvchi, taʼminlovchi, foydalanuvchilar"),
    Rule("R11", "-(u)v verbal noun surfaces as -iv",
         "twol alphabet `%{u%}:i` (apertium-uzb.uzb.twol, line ~12); GERUND `%<ger%>:%>%{u%}v` (line 710)",
         "{u} can only surface as i, so kel<v><iv><ger><nom> generates *keliv* and the analyser accepts *yondashiv* but rejects yondashuv.",
         "Twol: `%{u%}:u`, with -a+uv → -ov (tanla→tanlov) and -i+uv → -uv (oʻqi→oʻquv).",
         "yondash<v><iv><ger><nom>", "yondashuv, tekshiruv, kuzatuv, tanlov, qidiruv", kind="twol"),
    Rule("R12", "-dagilar: Cyrillic р in ATTR-SUBST",
         "LEXICON ATTR-SUBST (lexc lines 993-994)",
         "`%<subst%>%<pl%>:%>%{L%}%{A%}р` ends in Cyrillic р (U+0440), the same two lines as in the Cyrillic apertium-kaz "
         "lexc (lines 618-619, where р is correct); the analyser accepts "
         "*uydagilaр* (Cyrillic) and rejects uydagilar, atrofdagilar, uyimizdagilar.",
         "Replace р with Latin r in both lines.", "uy<n><loc><subst><pl><nom>", "atrofdagilar, uydagilar, uyimizdagilar",
         kind="lexicon-bug"),
    Rule("R13", "-dagi after p-final stems",
         "twol rule '{D} as t after (some?) voiceless cons'",
         "{D} is obligatorily t after p, so gap+{D}agi must surface as *gaptagi*; gapdagi, tipdagi are rejected "
         "(Uzbek spelling keeps -da-).",
         "Restrict the {D}:t rule to the causative -{D}ir- (yop-tir-, lexc lines 585, 608), the one place where Uzbek "
         "spelling assimilates; -da and -dagi never assimilate.",
         "gap<n><loc><attr>", "tipdagi, gapdagi", kind="twol"),
    Rule("R14", "copula -dir and question -mi after adverbs, postpositions, conjunctions and gerunds",
         "ADV (line 480) → ADV3 (line 876), POST (490), CA (532), GER-CASE-NO_COPULA (1072)",
         "These lexicons end in `#` or a no-copula clitic class, so demakdir, uchundir, qilishdir, shundaymi, uchunmi fail.",
         "Route them through a predicative clitic class: `+e<cop><aor><p3><frm><sg>:dir`, `+mi<qst>`, -ku, -chi.",
         "demak<cnjadv>+e<cop><aor><p3><frm><sg>", "demakdir, uchundir, qilishdir, bilandir, shundaymi, uchunmi"),
    Rule("R15", "contracted copula after -(a)r / -mas: -ardi, -masdi, -arkan",
         "AORIST (line 773); INDEF-PAST has the analogous -gandi (line 743)",
         "Only -gandi (past + edi) is contracted; -ar+edi and -mas+edi (past habitual), -ar ekan are missing "
         "(kelardi gets an accidental <fut2><p3> reading, boʻlardim fails).",
         "Like INDEF-PAST: `%<fut2%>+e%<cop%>%<ifi%>:%>%{E%}r%>di PERS2 ;` `%<neg%>%<fut2%>+e%<cop%>%<ifi%>:%>mas%>di PERS2 ;` "
         "and `...+e<cop><aor><evid>:...arkan / -maskan`.",
         "boʻl<v><iv><fut2>+e<cop><ifi><p1><sg>", "boʻlardim, olmasdi, bilmasdi, boʻlarkan, oʻylardi"),
    Rule("R16", "auxiliary -(a)ver- (continuative)",
         "V-INFL-ABIL (line 783)",
         "V-INFL-ABIL has only the ability auxiliary ol, attached as bare -ol (keloladi, analysed with a doubled "
         "<vaux><vaux>, see L4); ver (continue, keep on) is missing.",
         "`%<prc_impf%>+ver%<vaux%>:%>%{E%}ver V-AUX ;` next to the ol line.",
         "qol<v><iv><prc_impf>+ver<vaux><aor><p3><sg>", "boʻlaveradi, qolaveradi, boraveradi, qolaversa"),
    Rule("R17", "converbs -guncha and -gach after k/q",
         "NON-FINITE (line 671): `%<gna_when%>:%>gach` with a literal g; <gna_until> declared (line 214), unused",
         "-guncha is not produced; -gach never assimilates (chiqqach rejected, *chiqgach* accepted).",
         "`%<gna_until%>:%>%{G%}uncha CLITICS-NO-COP ;` and `%<gna_when%>:%>%{G%}ach #`.",
         "boʻl<v><iv><gna_until>", "boʻlguncha, kelguncha, yetguncha, chiqqach"),
    Rule("R18", "-ta (count) followed by possessive or case",
         "LEXICON NUM (line 1145): `%<num%>%<cl%>:%>ta #`",
         "-ta ends the word, so ikkitasi, ikkitadan, uchtasi fail. bironta, birontasi and birortasi fail for another reason: "
         "biron is not a numeral entry and birorta is a tagless whole-word entry (line 4284), so they need their own fix.",
         "`%<num%>%<cl%>:%>ta SUBST ;` (or FULL-NOMINAL-INFLECTION).", "ikki<num><cl><subst><px3sp><nom>",
         "ikkitasi, ikkitadan, birortasi, birontasi"),
    Rule("R19", "possessive -si after -iy stems",
         "twol {s} deletion after consonants; y counts as a consonant",
         "asosiy+{s}i must surface as *asosiyi*; the standard asosiysi, vodiysi, doimiysi are rejected.",
         "Treat stem-final y after i as a vowel for {s}:s (new set or a lexicon archiphoneme), keeping kuyi-type stems apart.",
         "vodiy<n><px3sp><nom>", "asosiysi, vodiysi, doimiysi, vodiysida", kind="twol",
         ask="After -iy stems, is px3 always -si (asosiysi, vodiysi), or is -yi (vodiyi) also acceptable?"),
    Rule("R20", "possessive -si after stems in oʻ",
         "twol Cons set includes ʻ",
         "ʻ counts as a consonant, so obroʻ+{s}i surfaces as *obroʻi*; obroʻsi is rejected.",
         "Remove ʻ from Cons (it is part of the vowel oʻ and of the consonant gʻ: check gʻ-final stems separately).",
         "obroʻ<n><px3sp><nom>", "obroʻsi, obroʻsini (the variant obroʻyi is handled with R21)", kind="twol"),
    Rule("R21", "possessive -(y)i after Arabic stems ending in a vowel (ʻayn/hamza)",
         "lexicon marking",
         "mavqe, manba, aʼzo take -si in the lexicon; the corpus also writes mavqei, manbayi, aʼzoyi.",
         "Mark these stems (mavqe, manba, aʼzo, mavzu?) with a px3 allomorph -i/-yi as a variant (Dir/LR).",
         "mavqe<n><px3sp><nom>", "mavqei, mavqeini, manbayi, aʼzoyi", kind="lexicon-marking",
         ask="Are mavqei, manbayi, aʼzoyi standard alongside mavqesi, manbasi, aʼzosi?"),
    Rule("R22", "vowel elision before vowel-initial suffixes",
         "lexicon: elided stems are listed by hand (oʻgʻl, singli); ogʻiz has none",
         "ogʻiz+i must surface as *ogʻizi*; ogʻzi, ogʻziga are rejected.",
         "Mark elidable stems (ogʻ{i}z, bagʻ{i}r, koʻng{i}l, ...) with an archiphoneme deleted before vowel-initial suffixes.",
         "ogʻiz<n><px3sp><nom>", "ogʻzi, ogʻziga, ogʻzidan", kind="lexicon-marking"),
    Rule("R23", "similative -dek after nouns, pronouns and attributives",
         "CLITICS (line 917) has +dek only after finite verbs; nouns get -day (<sim>)",
         "mendek, muzdek, odatdagidek fail. -day works after plain nouns (kitobday, muzday) but not after -dagi "
         "(odatdagiday is rejected too), and the pronoun men has no <sim> at all (menday gets only the noun men).",
         "Add `%<sim%>:%>dek` (Dir/LR variant of -day) to GENERAL-POSSESSIVE-ETC and pronoun lexicons, or `+dek<post>` to CLITICS-NO-COP.",
         "men<prn><pers><p1><sg><sim>", "mendek, muzdek, odatdagidek"),
    Rule("R24", "-cha after gerund + possessive and genitive pronouns",
         "GER-POSSESSIVES (line 1108) → GER-CASE-ETC; pronoun lexicons",
         "koʻrsatishicha, taʼkidlashicha ('according to what X said') and bizningcha fail; aytishicha exists as a whole word.",
         "`+cha<post>` after ger_abst+px3 and after genitive personal pronouns.",
         "koʻrsat<v><tv><ger_abst><px3sp><nom>+cha<post>", "koʻrsatishicha, taʼkidlashicha, berishicha, bizningcha"),
    Rule("R25", "indefinite -dir after case forms of interrogatives",
         "PRON-ITG-INFL (line 1323; kim, nima) and ADV-ITG (line 880; qachon, which takes no inflection)",
         "nimadir is accepted only as nima + copula -dir ('it is what'), with no indefinite reading (kimdir and qachondir "
         "are N1 entries); case forms with -dir (nimanidir, kimgadir, kimningdir, qachonlardir) are rejected.",
         "Pronoun paradigm: kim/nima/qachon/qayer + case + dir → <prn><ind> + case.",
         "kim<prn><ind><dat>", "nimanidir, kimgadir, kimningdir, kimnidir, qachonlardir"),
    Rule("R26", "attributive -gi/-ki/-qi after time and place nouns",
         "ADV-ATTR (line 483) only",
         "qishki and bahorgi fail; kechki, kechagi, yozgi, kuzgi, hozirgi exist only as whole-word entries; only ADV-ATTR "
         "adverbs get <attr>:{G}i.",
         "Add `%<n%>%<attr%>:%>%{G%}i` to a small set of time nouns (N1-TIME), not to every noun.",
         "qish<n><attr>", "qishki, bahorgi"),
    Rule("R27", "emphatic and additive clitics -(y)oq, -(y)am",
         "CLIT-MODASS (line 940)",
         "hoziroq, oʻzidayoq (emphatic -oq) and spoken -(y)am 'also' (oʻziyam, boʻlsayam) are missing.",
         "`%+oq%<emph%>:%>%{y%}oq` after nominals/adverbs/converbs; -(y)am as a Dir/LR spoken variant of ham.",
         "hozir<adv>+oq<emph>", "hoziroq, oʻzidayoq, oʻziyam, boʻlsayam"),
    Rule("R28", "optative and -yish after vowel-final verbs",
         "IMPERATIVE (line 722); twol {E}:y",
         "de+{E}ylik surfaces as *deyylik*; deylik, oʻqiylik are rejected; deyishga fails.",
         "After a vowel, {E}ylik → ylik (no extra y).",
         "de<v><tv><opt><p1><pl>", "deylik, oʻqiylik", kind="twol"),
    Rule("R29", "archaic and literary verb and pronoun forms",
         "not covered (classical texts: Navoiy, Bobur, Qodiriy)",
         "-ur/-r aorist (boʻlur, kelur), -ub converb (boʻlub), -gʻay (boʻlgʻay), -sun (boʻlsun), -gʻil (qilgʻil), -dur "
         "(bordur), and archaic pronoun forms (anga, aning, andin, ani, alar, bul). Only an analysis-only -gay exists "
         "(IMPERATIVE line 741, tagged <imp>), with a literal g, so boʻlgʻay and qilgʻay are rejected.",
         "A separate archaic sub-lexicon marked `Use/Arch` (analysis only, not generated), or a 'desc' analyser.",
         "boʻl<v><iv><aor><p3><sg> (arch)", "boʻlur, qilur, kelur, boʻlub, boʻlgʻay, anga, aning",
         kind="register", ask="Should classical/archaic forms be analysed by the main analyser or only by a separate 'desc' analyser?"),
    Rule("R30", "possessive and case after Titlecase abbreviations",
         "casing: abbreviations are stored in capitals (BMT, AQSH, SSSR)",
         "Bmtning, Aqshda, Sssrning are written in Titlecase with a suffix. lt-proc can match an upper-case input letter "
         "to a lower-case lexicon letter but not the reverse, so the lower-case 'mt' of Bmt cannot match BMT. Some listed "
         "words (Fkning, Jkning, Jpkning) also need new entries: FK, JK, JPK are not in the lexicon.",
         "Add Titlecase variants of frequent abbreviations as Dir/LR entries, or normalise abbreviation casing before lookup.",
         "BMT<abbr><gen>", "Bmtning, Aqshda, Aqshning, Sssrda, Fkning", kind="casing"),
    Rule("R31", "pronoun and determiner paradigm gaps",
         "Hardcoded pronoun entries; PRON-DEM-BU (line 563)",
         "Possessive pronouns with -niki (meniki, bizniki), demonstrative + px3 (bunisi, shunisi) and shuncha+lar are missing.",
         "Add the forms to the pronoun paradigms: men<prn><pers><p1><sg><gen><subst><nom> for meniki; bu<prn><dem><px3sp> for bunisi.",
         "men<prn><pers><p1><sg><gen><subst><nom>", "meniki, bizniki, bunisi, shunisi, shunchalar"),
    Rule("R32", "passive of vowel-final transitive verbs",
         "LEXICON VERB-TV (line 601): `%<v%>%<tv%>%<pass%>:%>i%{L%}` (VERB-IV has `%>%{i%}%{L%}`)",
         "The passive vowel is a literal i, so koʻzla<v><tv><pass><gpr_rsub> generates *koʻzlailgan*; koʻzlangan, "
         "tasniflanadi fail unless a separate -lan stem is listed (tayyorlan) or the verb also has a V-IV entry (ishla); "
         "ayblanuvchi, yetaklanuvchi also need R10. "
         "Found by the triage agents.",
         "`%<v%>%<tv%>%<pass%>:%>%{i%}%{L%} VERB-TV-FULL ;` (line 603; the pass+coop line 607 is already correct).",
         "koʻzla<v><tv><pass><gpr_rsub>", "koʻzlangan, tasniflanadi, distillangan", kind="lexicon-bug"),
    Rule("R33", "-moq infinitive + possessive: q→gʻ",
         "NON-FINITE (line 671): `%<ger_inf%>:%>moq GER-INFL`",
         "The q of -moq does not voice before a vowel: boʻl<v><iv><ger_inf><px3sp> generates *boʻlmoqi*; boʻlmogʻi is "
         "rejected. The twol voicing rule (line 79) needs a %{ʻ%} after the boundary, which noun POSSESSIVES carry "
         "(`%>%{ʻ%}%{s%}i`) but GER-POSSESSIVES (lines 1108-1118) do not. Found by the triage agents.",
         "Give the possessives after -moq the %{ʻ%} the voicing rule needs (a GER-INF possessive lexicon); {Q} cannot be used, it only maps to q.",
         "boʻl<v><iv><ger_inf><px3sp><nom>", "boʻlmogʻi, qilmogʻi, etmogʻi", kind="twol"),
    Rule("R34", "glide y after the verb ye- 'eat'",
         "lexc entry `ye:ye%{й%} V-TV`; twol '{й}:y only before -ish'",
         "{й} surfaces only before -ish, so ye<v><tv><aor><p3><sg> generates *yeadi*; yeydi, yeyman fail. Found by the triage agents.",
         "Let {й}:y surface before every vowel-initial suffix.", "ye<v><tv><aor><p3><sg>", "yeydi, yeyman, yeyishadi", kind="twol"),
    Rule("R35", "colloquial converb -p (boʻlib → boʻp)",
         "not covered (spoken register)",
         "Spoken contraction of -(i)b with loss of the stem-final l: boʻp, qip, kep, op, boʻpti, qipti. Found by the triage agents.",
         "Dir/LR variants in a spoken-register sub-lexicon (analysis only), not in the normative generator.",
         "boʻl<v><iv><gna_perf> (coll)", "boʻp, boʻpti, qipti, kepti", kind="register"),
    Rule("R36", "Arabic geminate stems: final consonant doubles before vowels",
         "lexicon marking (N1 has no doubling archiphoneme)",
         "haq (ḥaqq), had (ḥadd), sir (sirr) double their last consonant before vowel-initial suffixes: haqqi, haddi, sirri "
         "fail (hissi works only through a separate stem hiss). Found by the triage agents.",
         "Mark these stems with a doubling archiphoneme (haq%{q%}), or list the doubled stem for vowel-initial suffixes.",
         "haq<n><px3sp><nom>", "haqqi, haddi, sirri", kind="lexicon-marking"),
    Rule("R37", "question -mi followed by contracted edi/ekan",
         "CLIT-QST (line 935): `+mi<qst>` ends the word",
         "bormidi (5,120 uses), yoʻqmidi, boʻlganmidi, kelarmidi, boʻlarmikan fail, while bormi, boʻlganmi and edimi work. "
         "Found by the triage reviewers.",
         "After `+mi<qst>`, allow the contracted copula `+e<cop><ifi>` (-di + person) and `+e<cop><aor><evid>` (-kan).",
         "bor<adj>+mi<qst>+e<cop><ifi><p3><sg>", "bormidi, yoʻqmidi, boʻlganmidi, boʻlarmidi, boʻlarmikan"),
    Rule("R38", "privative -siz after a possessive",
         "ABESSIVE-POSTPOSITION (line 1040) is reached only from the bare stem and the plural",
         "-siz attaches only to the bare stem (uy+siz). ruxsatisiz, yordamisiz ('without his/its permission') get only a "
         "spurious copula reading (ruxsat<n><px3sp><nom>+e<cop><aor><p2><frm><sg>); ishtirokisiz is rejected, mainly "
         "because of R7. Found by the triage reviewers.",
         "Let POSSESSIVES continue to ABESSIVE-POSTPOSITION (px + `+siz<post>`).",
         "ruxsat<n><px3sp>+siz<post>", "ruxsatisiz, yordamisiz, ishtirokisiz"),
    Rule("R39", "3pl -lar after the -(a)r future",
         "AORIST (line 773): `%<fut2%>:%>%{E%}r PERS3`; PERS3 gives 3pl only as -{D}ilar",
         "kelarlar, qilarlar, bilarlar ('they will/would …') fail while kelarman, kelarmiz work. For vowel-final stems "
         "the -(a)r form itself is wrong: de- surfaces as deyr- (deyrman, deyrdi accepted; derman, derdi, derlar rejected) "
         "because {E} becomes y after a vowel, the same twol problem as R28. Found by the triage reviewers.",
         "Add `%<p3%>%<pl%>:%>lar` to the person endings used after <fut2>.",
         "de<v><tv><fut2><p3><pl>", "derlar, kelarlar, qilarlar"),
]}

# Decisions by the project owner (the native reviewer), 2026-10-16, on the native-speaker questions
DECISIONS = {
    "R5": "Attached -gina/-kina/-qina is the standard spelling (faqatgina, shundoqqina); keep the separate 'gana' "
          "only as an analysis-only (Dir/LR) variant.",
    "R19": "Only -si is standard after -iy stems (asosiysi, vodiysi, doimiysi). The -yi forms the analyser accepts "
           "today (asosiyi, vodiyi) are wrong: stop accepting and generating them.",
    "R21": "Accept -i, -yi and -si for analysis, since all three are common in real text; generate the corpus's most "
           "frequent form per word: mavqei (23,271 uses; mavqeyi 2,685; mavqesi 166, which is what Apertium generates "
           "today), manbai (103,085; manbasi 14,525; manbayi 13,515; manbai is now a separate N1 entry with the wrong "
           "lemma, lines 16864-16865), aʼzosi (76,364; aʼzoyi 8,351; aʼzoi 156), obroʻsi (10,407; obroʻyi 3,235, obroʻyini 1,958; obroʻi 44; "
           "the -si form itself needs the R20 fix). This needs per-word marking in the lexicon, not a general rule "
           "(the detector's tail precision is only 0.12 because of the Persian izafet).",
    "R6": "Accept all three spellings of a number + suffix: hyphen (5-ta, 100-dan), solid (5ta, 100dan) and spaced "
          "(5 ta, 100 dan; re-attached by the tokenizer, T1).",
}

# Open spelling questions that are not tied to one catalogue rule
QUESTIONS = [
    "**T4** (older spellings): should the main analyser accept frequent older or variant spellings (etarli for "
    "yetarli, budjet for byudjet, koeffitsient for koeffitsiyent, marganes for marganets), or only a separate "
    "variant ('desc') analyser?",
    "**R3**: is -ishlik (boʻlishligi) standard, or a variant of -ish (boʻlishi)?",
    "**R9**: tag for -gacha: a new case `<term>`, or the current convention `<dat>+cha<post>` (ertaga+cha)?",
]

# Tokenizer / normalisation proposals (not lexc rules) -------------------------------------
TOKENIZER = {
    "T1": "Attach a suffix chain that follows a closing quote or a number (with space, hyphen or nothing between) to "
          "that word: «Kitob»ning → Kitobning, 100 dan / 100-dan → 100dan (then R6).",
    "T2": "Re-join words broken by a line-break hyphen when the continuation is a known suffix chain "
          "(…lash, …langan, …ladi fragments).",
    "T3": "Map Cyrillic look-alikes in Roman numerals (І Ѵ Х) to Latin before lookup.",
    "T5": "uzmorph normaliser bug, fixed on 2026-10-16: in word-final oʻgʻ (yo‘g‘, cho‘g‘) the second apostrophe was "
          "left as a quote mark, so step 3 counted yoʻg, choʻg. Step 3's counts for these few types are slightly off.",
    "T6": "Keep multiword lexicon entries (baxsh et, sollallohu alayhi vasallam) and URLs (lex.uz) together "
          "in the tokenizer instead of counting their parts.",
    "T7": "Spaced or syllabified text (song lyrics 'bax - ti - miz', letter-spaced headings): re-join before "
          "lookup, or exclude it from coverage.",
    "T4": "Spelling-variant layer (separate 'desc' analyser, not the normative one): lost diacritics (u→oʻ, k→q, g→gʻ, "
          "h↔x) and initial e→ye in older texts.",
}


# ----------------------------------------------------------------------------- tails
PX = [("imiz", "<px1pl>"), ("ingiz", "<px2pl>"), ("lari", "<px3pl>"), ("im", "<px1sg>"),
      ("ing", "<px2sg>"), ("i", "<px3sp>")]
PX_V = [("miz", "<px1pl>"), ("ngiz", "<px2pl>"), ("lari", "<px3pl>"), ("m", "<px1sg>"),
        ("ng", "<px2sg>"), ("si", "<px3sp>")]
CASE = [("ning", "<gen>"), ("ni", "<acc>"), ("ga", "<dat>"), ("ka", "<dat>"), ("qa", "<dat>"),
        ("dagi", "<loc><attr>"), ("dan", "<abl>"), ("da", "<loc>"), ("gacha", "<term>"), ("day", "<sim>")]
CLIT = [("mi", "+mi<qst>"), ("dir", "+e<cop><aor><p3><frm><sg>"), ("gina", "+gina<postadv>"),
        ("ku", "+ku<emph>"), ("ki", "+ki<cnjadv>")]


def parse_tail(tail: str, after_vowel: bool, allow_pl=True, allow_px=True):
    """Nominal inflection tail -> tag string (without the stem), or None.
    (lar) (px) (case) (clitic); empty tail = <nom>."""
    best = None
    for pl in ([("lar", "<pl>"), ("", "")] if allow_pl else [("", "")]):
        if not tail.startswith(pl[0]):
            continue
        r1 = tail[len(pl[0]):]
        vowel1 = after_vowel if not pl[0] else False
        pxs = (PX_V if vowel1 else PX) if allow_px else []
        for px in pxs + [("", "")]:
            if not r1.startswith(px[0]):
                continue
            r2 = r1[len(px[0]):]
            for cs in CASE + [("", "<nom>")]:
                if not r2.startswith(cs[0]):
                    continue
                r3 = r2[len(cs[0]):]
                for cl in CLIT + [("", "")]:
                    if r3 == cl[0]:
                        tags = pl[1] + px[1] + cs[1] + cl[1]
                        cand = (len(pl[0]) + len(px[0]) + len(cs[0]), tags)
                        if best is None or cand[0] > best[0]:
                            best = cand
    return None if best is None else best[1]


# ----------------------------------------------------------------------------- detectors
@dataclass
class Cand:
    rule: str
    base: str            # string to analyse
    need: str            # regex the base analysis must match
    build: object        # f(base_analysis) -> proposed analysis
    note: str = ""
    lemma: str = ""       # expected lemma of the base analysis (preferred when several match)


@dataclass
class Hit:
    rule: str
    base: str
    base_analysis: str
    proposed: str
    note: str = ""


_NOMINAL = r"<(n|adj|np|prn|num|abbr)>"
_PRED = r"<(adj|adv|n|post|postadv|cnjadv|cnjsub|cnjcoo|prn|ij|mod|det|num)>|<cop>|<imp>"


def _lemma_tags(a: str) -> tuple[str, str]:
    m = re.match(r"([^<]*)(.*)", a)
    return m.group(1), m.group(2)


def _strip_case(a: str) -> str:
    return re.sub(r"(<nom>|<gen>|<acc>|<dat>|<loc>|<abl>)(\+.*)?$", "", a)


def _verb_stem_bases(stem_surface: str):
    """Verb stems a participle/verbal-noun surface prefix could come from."""
    yield stem_surface, ""
    yield stem_surface + "a", "a"      # belgil-ovchi <- belgila
    yield stem_surface + "i", "i"      # oʻq-uvchi <- oʻqi


def candidates(w: str) -> list[Cand]:
    out: list[Cand] = []
    add = out.append

    # R1 postposition + (da)gi
    for suf, cut in (("gi", 0), ("dagi", 0)):
        i = w.rfind(suf)
        while i > 1:
            base, tail = w[:i], w[i + len(suf):]
            t = parse_tail(tail, True, allow_px=False) if tail else ""
            if t is not None and (suf == "dagi" or base.endswith("da")):
                tt = t.replace("<nom>", "")
                add(Cand("R1", base, r"<post>", lambda a, tt=tt: _lemma_tags(a)[0] + "<post><attr>" + (("<subst>" + tt) if tt else "")))
            i = w.rfind(suf, 0, i)
    # R2 copula 3pl
    if w in ("edilar", "ekanlar", "emaslar", "emasdilar", "edilarmi", "ekanlarmi"):
        tags = {"edilar": "e<cop><ifi><p3><pl>", "ekanlar": "e<cop><aor><evid><p3><pl>",
                "emaslar": "e<cop><neg><aor><p3><pl>", "emasdilar": "e<cop><neg><aor>+e<cop><ifi><p3><pl>",
                "edilarmi": "e<cop><ifi><p3><pl>+mi<qst>", "ekanlarmi": "e<cop><aor><evid><p3><pl>+mi<qst>"}[w]
        add(Cand("R2", "edi", r"<cop>", lambda a, t=tags: t))
    for suf, tag in (("dirlar", "+e<cop><aor><p3><frm><pl>"), ("dilar", "+e<cop><ifi><p3><pl>")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            base = w[:-len(suf)] + ("dir" if suf == "dirlar" else "di")
            add(Cand("R2", base, r"<cop>", lambda a, tag=tag: re.sub(r"\+e<cop>.*$", "", a) + tag))
    # R3 -lik after -gan/-mas/-ish/-ayotgan, emaslik
    m = re.match(r"^(.+?(?:gan|kan|qan|mas|ish|sh))(lik|lig)(.*)$", w)
    if m:
        pre, lik, tail = m.groups()
        t = parse_tail(tail, False) if lik == "lig" and tail.startswith("i") else (parse_tail(tail, False) if lik == "lik" else None)
        if lik == "lig" and not tail[:1] in ("i",):
            t = None
        if t is not None:
            if pre.endswith(("gan", "kan", "qan")):
                add(Cand("R3", pre, r"<v>.*(<ger_past>|<gpr_rsub>|<past>)",
                         lambda a, t=t: re.sub(r"<(ger_past|gpr_rsub|past)>.*$", "", a) + ("<ger_perf>" if "<neg>" not in a else "<ger_perf>") + t))
            elif pre.endswith("mas"):
                add(Cand("R3", pre, r"<neg><gpr_fut>|<cop><neg>",
                         lambda a, t=t: re.sub(r"<neg><gpr_fut>.*$|<neg><aor>.*$", "", a) + "<neg><ger_ppot>" + t))
            else:
                add(Cand("R3", pre, r"<ger_abst>",
                         lambda a, t=t: re.sub(r"<ger_abst>.*$", "", a) + "<ger_abst><abs>" + t))
    # R4 -ki
    if w.endswith("ki") and len(w) > 4:
        add(Cand("R4", w[:-2], _PRED, lambda a: a + "+ki<cnjadv>"))
    # R5 -gina/-kina/-qina (possibly + dir/mi)
    for suf in ("gina", "kina", "qina"):
        j = w.rfind(suf)
        if j > 1 and w[j + 4:] in ("", "dir", "mi"):
            ext = {"": "", "dir": "+e<cop><aor><p3><frm><sg>", "mi": "+mi<qst>"}[w[j + 4:]]
            add(Cand("R5", w[:j], r".", lambda a, ext=ext: a + "+gina<postadv>" + ext))
    # R6 digits + suffix
    m = re.match(r"^(\d+(?:[.,]\d+)?)-?([a-z" + OKINA + TUTUQ + r"]+)$", w)
    if m:
        num, tail = m.groups()
        special = {"ta": "<num><cl>", "inchi": "<num><ord>", "nchi": "<num><ord>", "chi": "<num><ord>",
                   "lik": "<num>+lik", "ga": "<num><subst><dat>", "da": "<num><subst><loc>", "dan": "<num><subst><abl>",
                   "ni": "<num><subst><acc>", "ning": "<num><subst><gen>", "gacha": "<num><subst><term>",
                   "lar": "<num><subst><pl><nom>", "dagi": "<num><subst><loc><attr>"}
        if tail in special:
            add(Cand("R6", num, r"<num>", lambda a, n=num, t=special[tail]: n + t))
        else:
            t = parse_tail(tail, False)
            if t is not None:
                add(Cand("R6", num, r"<num>", lambda a, n=num, t=t: n + "<num><subst>" + t))
    # R7 non-voicing k/q + vowel-initial tail
    for i in range(3, len(w)):
        if w[i - 1] in "kq" and w[i] == "i" and ends_in_vowel(w[:i - 1]):
            base, tail = w[:i], w[i:]
            t = parse_tail(tail, False)
            if t is not None and t not in ("<nom>",) and (t.startswith("<px") or t.startswith("<pl>") is False):
                add(Cand("R7", base, _NOMINAL, lambda a, t=t: _strip_case(a) + t))
    # R8 comparative
    m = re.match(r"^(.+?)(roq|rogʻ)(.*)$", w)
    if m and len(m.group(1)) >= 2:
        base, roq, tail = m.groups()
        if roq == "roq" and tail == "":
            add(Cand("R8", base, r"<adj>|<adv>", lambda a: _lemma_tags(a)[0] + "<adj><comp>"))
        elif roq == "rogʻ":
            t = parse_tail(tail, False)
            if t is not None:
                add(Cand("R8", base, r"<adj>|<adv>", lambda a, t=t: _lemma_tags(a)[0] + "<adj><comp><subst>" + t))
        elif roq == "roq":
            t = parse_tail(tail, False)
            if t is not None and tail[:1] not in "aeiou":
                add(Cand("R8", base, r"<adj>|<adv>", lambda a, t=t: _lemma_tags(a)[0] + "<adj><comp><subst>" + t))
    # R9 terminative
    for suf in ("gacha", "kacha", "qacha"):
        if w.endswith(suf) and len(w) > len(suf) + 1:
            base = w[:-len(suf)]
            ext = ""
            add(Cand("R9", base, r"<(n|prn|num|np|adv|adj)>|<ger",
                     lambda a: re.sub(r"<nom>(\+.*)?$", "", a) + ("<term>" if "<nom>" in a else "+gacha<term>")))
            if base.endswith(("ga", "ka", "qa")):
                add(Cand("R9", base, r"<dat>", lambda a: re.sub(r"<dat>(\+.*)?$", "<term>", a)))
    # R10 -(u)vchi / -ovchi ; R11 -(u)v / -ov
    for suf, rule, tag in (("uvchi", "R10", "<gpr_pot>"), ("ovchi", "R10", "<gpr_pot>"),
                           ("uv", "R11", "<ger>"), ("ov", "R11", "<ger>")):
        j = w.find(suf)
        while j > 1:
            pre, tail = w[:j], w[j + len(suf):]
            t = parse_tail(tail, False)
            if t is not None:
                bases = [(pre + "a", "a")] if suf.startswith("o") else [(pre, ""), (pre + "i", "i")]
                for vb, _ in bases:
                    if len(vb) >= 2:
                        tt = ("<subst>" + t) if (rule == "R10" and t != "<nom>") else ("" if rule == "R10" else t)
                        add(Cand(rule, vb + "di", r"<v>", lambda a, tag=tag, tt=tt: re.sub(r"<(ifi|past)>.*$", "", a) + tag + tt,
                                 note="verb tested as stem+di", lemma=vb))
            j = w.find(suf, j + 1)
    # R12 -dagilar (Cyrillic р)
    m = re.match(r"^(.+?(?:da|ta)gi)(lar)(.*)$", w)
    if m:
        base, _, tail = m.groups()
        t = parse_tail("lar" + tail, False, allow_px=True)
        if t is not None:
            add(Cand("R12", base, r"<loc><attr>", lambda a, t=t: a.replace("<loc><attr>", "<loc><subst>") + t))
    # R13 p + dagi
    m = re.match(r"^(.+p)dagi(.*)$", w)
    if m and parse_tail(m.group(2), False, allow_px=False) is not None:
        add(Cand("R13", m.group(1) + "da", r"<loc>", lambda a: re.sub(r"<loc>.*$", "<loc><attr>", a)))
    # R14 -dir / -mi / -ku after closed classes and gerunds
    for suf, tag in (("dir", "+e<cop><aor><p3><frm><sg>"), ("mi", "+mi<qst>"), ("ku", "+ku<emph>"), ("chi", "+chi<qst>")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            add(Cand("R14", w[:-len(suf)], r"<(adv|post|cnjadv|cnjsub|postadv|det|ij)>|<ger_abst>|<ger>|<gpr_|<adj>",
                     lambda a, tag=tag: re.sub(r"\+e<cop>.*$", "", a) + tag))
    # R15 contracted copula after -(a)r / -mas
    m = re.match(r"^(.+?(?:ar|ir|ur|r|mas))(di|dim|ding|dik|dingiz|dilar|kan|kanmiz|midi|mikan)$", w)
    if m:
        pre, cop = m.groups()
        pers = {"di": "<ifi><p3><sg>", "dim": "<ifi><p1><sg>", "ding": "<ifi><p2><sg>", "dik": "<ifi><p1><pl>",
                "dingiz": "<ifi><p2><frm><sg>", "dilar": "<ifi><p3><pl>", "kan": "<aor><evid><p3><sg>",
                "kanmiz": "<aor><evid><p1><pl>", "midi": "<ifi><p3><sg>", "mikan": "<aor><evid><p3><sg>"}[cop]
        add(Cand("R15", pre, r"<v>.*(<gpr_fut>|<fut2>)",
                 lambda a, pers=pers: re.sub(r"<(gpr_fut|fut2)>.*$", "", a) + "<fut2>+e<cop>" + pers))
    # R16 -(a)ver- auxiliary
    m = re.match(r"^(.+?)(a|y)ver(.*)$", w)
    if m and len(m.group(1)) >= 2:
        stem, link, rest = m.groups()
        add(Cand("R16", stem + "di", r"<v>",
                 lambda a, rest=rest: re.sub(r"<(aor|ifi|past)>.*$", "", a) + "<prc_impf>+ver<vaux>(" + rest + ")",
                 lemma=stem))
    # R17 -guncha / -gach after k/q
    m = re.match(r"^(.+?)(g|k|q)uncha$", w)
    if m:
        add(Cand("R17", m.group(1) + "di", r"<v>", lambda a: re.sub(r"<(ifi|past)>.*$", "", a) + "<gna_until>", lemma=m.group(1)))
    m = re.match(r"^(.+?[kq])(kach|qach)$", w)
    if m:
        add(Cand("R17", m.group(1) + "di", r"<v>", lambda a: re.sub(r"<(ifi|past)>.*$", "", a) + "<gna_when>", lemma=m.group(1)))
    # R18 -ta + px/case
    m = re.match(r"^(.+?)ta(si|lari|dan|ga|ni|ning|da|miz|ngiz)(.*)$", w)
    if m:
        t = parse_tail(m.group(2) + m.group(3), True)
        if t is not None:
            add(Cand("R18", m.group(1), r"<num>|<det>|<prn>", lambda a, t=t: _lemma_tags(a)[0] + "<num><cl><subst>" + t))
    # R19 -iy + si ; R20 -oʻ + si ; R21 vowel + (y)i
    for rule, pat in (("R19", r"^(.+iy)(si|sini|siga|sida|sidan|sining|simiz|sidagi)$"),
                      ("R20", r"^(.+" + O_ + r")(si|sini|siga|sida|sidan|sining|sidagi)$")):
        m = re.match(pat, w)
        if m:
            t = parse_tail(m.group(2), True)
            if t is not None:
                add(Cand(rule, m.group(1), _NOMINAL, lambda a, t=t: _strip_case(a) + (("<subst>" + t) if "<adj>" in a and "<subst>" not in a else t)))
    m = re.match(r"^(.+[aeo])(y?i)(ni|ga|da|dan|ning|dagi)?$", w)
    if m:
        t = parse_tail("i" + (m.group(3) or ""), False)
        if t is not None:
            add(Cand("R21", m.group(1), _NOMINAL, lambda a, t=t: _strip_case(a) + t))
    # R22 vowel elision: C1 C2 + vowel tail <- C1 i/u C2
    for i in range(2, len(w) - 1):
        if w[i] in "iu" or not w[i - 1].isalpha() or w[i - 1] in VOWELS:
            continue
        for v in "iu":
            for k in range(i, min(i + 1, len(w))):
                base = w[:k] + v + w[k:k + 1]
                tail = w[k + 1:]
                if tail[:1] in ("i", "a") and len(base) >= 3:
                    t = parse_tail(tail, False)
                    if t is not None and t != "<nom>":
                        add(Cand("R22", base, r"<n>", lambda a, t=t: _strip_case(a) + t))
    # R23 -dek
    if w.endswith("dek") and len(w) > 5:
        add(Cand("R23", w[:-3], r"<(n|prn|adj|np)>|<attr>", lambda a: re.sub(r"<nom>(\+.*)?$", "", a) + "<sim>"))
    # R24 -cha after ger+px3 / gen pronoun
    if w.endswith("cha") and len(w) > 6:
        add(Cand("R24", w[:-3], r"<ger_abst><px|<prn><pers>.*<gen>", lambda a: a + "+cha<post>"))
    # R25 indefinite -dir after interrogative case forms
    m = re.match(r"^(kim|nima|qachon|qayer|qaysi|nechta)(.*)dir$", w)
    if m and m.group(2):
        add(Cand("R25", m.group(1) + m.group(2), r"<prn>|<adv>", lambda a: a.replace("<itg>", "<ind>")))
    # R26 attributive -gi/-ki/-qi on time nouns
    if re.match(r"^(qish|yoz|kuz|bahor|kech|tong|kun|tun|oqshom|kecha|bugun|ertaga|yil|oy|hafta|asr)(gi|ki|qi)$", w):
        add(Cand("R26", w[:-2], r"<n>|<adv>", lambda a: _lemma_tags(a)[0] + "<n><attr>"))
    # R27 -(y)oq / -(y)am
    for suf, tag in (("yoq", "+oq<emph>"), ("oq", "+oq<emph>"), ("yam", "+am<postadv>"), ("am", "+am<postadv>")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            base = w[:-len(suf)]
            if (suf.startswith("y") and ends_in_vowel(base)) or (not suf.startswith("y") and not ends_in_vowel(base)):
                add(Cand("R27", base, r".", lambda a, tag=tag: a + tag))
    # R28 optative after vowel stems
    m = re.match(r"^(.+[aeiou])ylik$", w)
    if m:
        add(Cand("R28", m.group(1) + "di", r"<v>", lambda a: re.sub(r"<(ifi|past)>.*$", "", a) + "<opt><p1><pl>", lemma=m.group(1)))
    # R29 archaic verb forms
    for pat, tag in ((r"^(.+?)(ur|ar)$", "<aor><p3><sg>"), (r"^(.+?)(ub)$", "<gna_perf>"),
                     (r"^(.+?)(gʻay|qay|kay)$", "<imp><p3><sg>"), (r"^(.+?)(sun)$", "<opt><p3><sg>"),
                     (r"^(.+?)(gʻil|qil|gil|kil)$", "<imp><p2><sg>"), (r"^(.+?)(gʻon|qon)$", "<gpr_rsub>"),
                     (r"^(.+?)(urlar|arlar)$", "<aor><p3><pl>")):
        m = re.match(pat, w)
        if m and len(m.group(1)) >= 2:
            add(Cand("R29", m.group(1) + "di", r"<v>", lambda a, tag=tag: re.sub(r"<(ifi|past)>.*$", "", a) + tag + " (arch)",
                     lemma=m.group(1)))
    if w in ("anga", "aning", "andin", "ani", "alar", "anda", "mundoq", "andoq", "bul", "kibi", "oʻzin", "boshin"):
        add(Cand("R29", "u" if w.startswith("an") else w, r".", lambda a, w=w: {"anga": "u<prn><pers><p3><sg><dat>", "aning": "u<prn><pers><p3><sg><gen>",
             "andin": "u<prn><pers><p3><sg><abl>", "ani": "u<prn><pers><p3><sg><acc>", "anda": "u<prn><pers><p3><sg><loc>"}.get(w, w + " (arch)")))
    # R32 passive of vowel-final transitive verbs: koʻzla+n+gan
    for i in range(3, len(w) - 2):
        if w[i] == "n" and w[i - 1] in "aiu" and re.match(_VERB_REST, w[i + 1:]):
            stem = w[:i]
            add(Cand("R32", stem + "di", r"<v><tv>", lambda a, rest=w[i + 1:]: re.sub(r"<(ifi|past)>.*$", "", a) + "<pass>…(" + rest + ")",
                     lemma=stem))
    # R33 -mogʻ/-magʻ + vowel-initial possessive
    m = re.match(r"^(.+?)(mogʻ|magʻ)(i.*)$", w)
    if m:
        t = parse_tail(m.group(3), False)
        if t is not None:
            add(Cand("R33", m.group(1) + "moq", r"<ger_inf>", lambda a, t=t: re.sub(r"<ger_inf>.*$", "<ger_inf>", a) + t))
    # R34 ye- 'eat' with glide y
    if re.match(r"^yey(di|man|san|miz|siz|dilar|apti|ishadi|ayotgan|in|ishi)?$", w) and w != "yey":
        add(Cand("R34", "yeyish", r"<v>", lambda a, w=w: "ye<v><tv>…(" + w[3:] + ")"))
    # R35 colloquial -p converb: boʻp(ti) <- boʻlib
    m = re.match(r"^(.+?)p(ti|man|san|miz|siz|tilar|qoldi|qolgan)?$", w)
    if m and len(m.group(1)) >= 2:
        add(Cand("R35", m.group(1) + "lib", r"<gna_perf>|<prc_perf>", lambda a: re.sub(r"<(gna_perf|prc_perf)>.*$", "", a) + "<gna_perf> (coll)",
                 lemma=m.group(1) + "l"))
    # R36 Arabic gemination: haqqi <- haq (lexical: only stems known to be Arabic geminates)
    for stem in ("haq", "had", "zid", "sir", "dur", "his", "rab", "sin", "tib", "xat", "xas"):
        if w.startswith(stem + stem[-1]) and w[len(stem) + 1:len(stem) + 2] == "i":
            t = parse_tail(w[len(stem) + 1:], False)
            if t is not None:
                add(Cand("R36", stem, r"<n>", lambda a, t=t: _strip_case(a) + t))
    # R37 -mi + contracted copula: bormidi
    m = re.match(r"^(.+?)mi(di|dim|ding|dik|dingiz|dilar|kan)$", w)
    if m and len(m.group(1)) >= 2:
        add(Cand("R37", m.group(1) + "mi", r"\+mi<qst>", lambda a, c=m.group(2): a + "+e<cop>" + ("<aor><evid>" if c == "kan" else "<ifi>")))
    # R38 px3 + -siz: ruxsatisiz
    m = re.match(r"^(.+?(?:i|si))siz$", w)
    if m and len(m.group(1)) >= 4:
        add(Cand("R38", m.group(1), r"<px3sp>", lambda a: _strip_case(a) + "+siz<post>"))
    # R39 -(a)r future + 3pl -lar: kelarlar
    m = re.match(r"^(.+?(?:ar|ir|ur|r))lar$", w)
    if m and len(m.group(1)) >= 3:
        add(Cand("R39", m.group(1), r"<v>.*(<gpr_fut>|<fut2>)", lambda a: re.sub(r"<(gpr_fut|fut2)>.*$", "", a) + "<fut2><p3><pl>"))
    # R30 Titlecase abbreviation + suffix (Bmtning -> BMT+ning)
    for i in range(2, min(len(w), 7)):
        tail = w[i:]
        t = parse_tail(tail, ends_in_vowel(w[:i])) if tail else None
        if t is not None and t != "<nom>" and tail[:1] not in ("i",):
            add(Cand("R30", w[:i].upper(), r"^(?:[^<]*[A-Z]){2}[^<]*<(abbr|np)>",
                     lambda a, t=t: re.sub(r"<nom>(\+.*)?$", "", a) + t.replace("<nom>", "")))
    # R31 pronoun and determiner paradigm gaps
    pr = {"meniki": "men", "seniki": "sen", "bizniki": "biz", "sizniki": "siz", "bunisi": "bu", "shunisi": "shu",
          "bunisini": "bu", "shunisini": "shu", "shunchalar": "shuncha", "bunchalar": "buncha", "munchalar": "muncha"}
    if w in pr:
        add(Cand("R31", pr[w], r"<prn>|<det>|<adv>", lambda a, w=w: _lemma_tags(a)[0] + "<prn>… (" + w + ")"))
    return out


def detect(words: list[str], analyses_of) -> dict[str, list[Hit]]:
    """analyses_of(list[str]) -> list[list[str]]. Returns word -> confirmed hits."""
    cands = {w: candidates(w) for w in words}
    bases = sorted({c.base for cs in cands.values() for c in cs})
    an = dict(zip(bases, analyses_of(bases)))
    out = {}
    for w, cs in cands.items():
        hits, seen = [], set()
        for c in cs:
            want = c.lemma or c.base
            for a in sorted(an.get(c.base, []), key=lambda a: _lemma_tags(a)[0].lower() != want.lower()):
                if re.search(c.need, a):
                    try:
                        prop = c.build(a)
                    except Exception:  # noqa: BLE001 - a bad builder must not stop a corpus run
                        prop = ""
                    key = (c.rule, c.base)
                    if key not in seen:
                        seen.add(key)
                        hits.append(Hit(c.rule, c.base, a, prop, c.note))
                    break
        if hits:
            out[w] = hits
    return out


for _rid, _d in DECISIONS.items():
    RULES[_rid].decision = _d

