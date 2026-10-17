#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply the test-build changes (bug fixes + top-10 rules) to a COPY of apertium-uzb.

    scripts/testbuild/build.sh        (copies <path-to-apertium-uzb> to <path-to-apertium-uzb-test>,
                                       runs this script, compiles, regenerates the modes)
    python scripts/testbuild/apply_changes.py <path-to-apertium-uzb-test> results/testbuild

Refuses to run on a directory named apertium-uzb (the original). Every edit is an exact-match
replacement that must succeed exactly once, so the script fails loudly instead of half-applying.
Each change carries a "test build" comment with its rule id from results/triage/RULES.md.

Version 2 (after the adversarial review in results/testbuild/diff_review.json): R4 (-ki), R8 (-roq)
and R29 (archaic forms) are restricted to corpus-attested words (scripts/testbuild/make_lists.py)
instead of whole classes; R7 uses the refined stem list; -(a)r future negative is -mas, its person
endings take no attached +da; de- gets the {й} glide (deyuvchi, deyiladi); pronouns get -gacha.
"""
import os
import re
import sys

OK = "ʻ"


def edit(text, old, new, label, count=1):
    n = text.count(old)
    if n != count:
        raise SystemExit(f"[{label}] expected {count} occurrence(s), found {n}: {old[:80]!r}")
    return text.replace(old, new)


def esc(analysis):
    """lexc upper side for an analysis: kerak<adj>+ki<cnjadv> -> kerak%<adj%>%+ki%<cnjadv%>"""
    return re.sub(r"<([^>]+)>", r"%<\1%>", analysis).replace("+", "%+")


def read_tsv(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    return [l.split("\t") for l in lines[1:] if l.strip()]


def lexc_changes(s, lists):
    # ---- tags and archiphonemes ------------------------------------------------------------
    s = edit(s, "%<vaux%>\n",
             "%<vaux%>\n"
             "%<fut2%>      ! -{a}r future (kelarman); was used but undeclared (test build)\n"
             "%<gna_when%>  ! -{G}ach converb; was used but undeclared (test build)\n"
             "%<gna_neg%>   ! -masdan converb; was used but undeclared (test build)\n"
             "%<sp%>        ! 3rd person of the volitional (V-PERS-VOL); was used but undeclared (test build)\n"
             "%<term%>      ! Terminative case -{G}acha (test build, R9)\n"
             "%<gpr_pot%>   ! -(u)vchi agentive participle, as in apertium-kaz/tat/kir (test build, R10)\n"
             "%<arch%>      ! Archaic/literary form, analysis only (test build, R29)\n",
             "tags")
    s = edit(s, "%{u%}              ! Harmonising \"deletion/insertion vowel\"\n",
             "%{u%}              ! Harmonising \"deletion/insertion vowel\"\n"
             "%{U%}              ! Vowel of -(u)v and -(u)vchi: u; o after a deleted stem-final a (test build, R11)\n",
             "archiphoneme {U}")

    # ---- R32: passive of vowel-final transitive verbs -------------------------------------
    s = edit(s, "%<v%>%<tv%>%<pass%>:%>i%{L%} VERB-TV-FULL ;",
             "%<v%>%<tv%>%<pass%>:%>%{i%}%{L%} VERB-TV-FULL ; ! test build R32: was a literal i", "R32")

    # ---- R17: -gach assimilates after k/q -------------------------------------------------
    s = edit(s, "%<gna_when%>:%>gach # ;     ! FIXME: rename",
             "%<gna_when%>:%>%{G%}ach # ;     ! FIXME: rename ! test build R17: was a literal g", "R17")

    # ---- R39: -(a)r future: {a}r (no y after vowels), own person endings, negative -mas ----
    s = edit(s, "%<fut2%>:%>%{E%}r PERS3 ; ! Dir/LR ! FIXME: need a different tag for this?",
             "%<fut2%>:%>%{a%}r PERS-FUT2 ; ! FIXME: need a different tag for this? ! test build R39: "
             "{a}r (der, not *deyr), own person endings, generable\n"
             "%<neg%>%<fut2%>:%>mas PERS-FUT2 ; ! test build R39: kelmas, kelmasman, kelmaslar", "R39")
    # the negative path must not reach the -(a)r future (it gave *kelmar)
    s = edit(s, "AORIST ;\n%<neg%>:%>ma AORIST ;",
             "AORIST ;\n%<neg%>:%>ma AORIST-NEG ; ! test build R39: was AORIST, which now holds the -(a)r future", "R39 neg")

    # ---- R12: Cyrillic р in ATTR-SUBST ----------------------------------------------------
    s = edit(s, "%<subst%>: POSSESSIVES ;\n%<subst%>%<pl%>:%>%{L%}%{A%}р CASES ;\n"
                "%<subst%>%<pl%>:%>%{L%}%{A%}р POSSESSIVES ;",
             "%<subst%>: POSSESSIVES ;\n%<subst%>%<pl%>:%>%{L%}%{A%}r CASES ; ! test build R12: was Cyrillic р\n"
             "%<subst%>%<pl%>:%>%{L%}%{A%}r POSSESSIVES ; ! test build R12: was Cyrillic р", "R12")

    # ---- R11: -(u)v verbal noun with its own vowel {U}; drop the non-Uzbek negative -mauv ----
    s = edit(s, "%<ger%>:%>%{u%}v GER-INFL ; ", "%<ger%>:%>%{U%}v GER-INFL ; ! test build R11: {U}, not {u}", "R11")
    s = edit(s, "%<neg%>%<ger%>:%>ma%>%{u%}v GER-INFL ; ",
             "!%<neg%>%<ger%>:%>ma%>%{u%}v GER-INFL ; ! test build: off; gave *kelmaiv/*kelmov, Uzbek uses -maslik (R3)",
             "R11 neg")

    # ---- R10 and R3 -------------------------------------------------------------------------
    s = edit(s, "%<gpr_rsub%>:%>%{G%}an # ;",
             "%<gpr_rsub%>:%>%{G%}an # ;\n"
             "%<gpr_pot%>:%>%{U%}vchi GPR-POT ; ! test build R10: keluvchi, belgilovchi, oʻquvchi", "R10")
    s = edit(s, "%<neg%>%<ger_past%>:%>ma%>%{G%}an GER-INFL ;",
             "%<neg%>%<ger_past%>:%>ma%>%{G%}an GER-INFL ;\n"
             "%<ger_perf%>:%>%{G%}anlik FULL-NOMINAL-INFLECTION ; ! test build R3: boʻlganlik, boʻlganligi\n"
             "%<neg%>%<ger_perf%>:%>ma%>%{G%}anlik FULL-NOMINAL-INFLECTION ; ! test build R3: boʻlmaganligi\n"
             "%<neg%>%<ger_ppot%>:%>maslik FULL-NOMINAL-INFLECTION ; ! test build R3: boʻlmaslik, boʻlmasligi", "R3")
    s = edit(s, "e%<cop%>%<ger_perf%>:ekan%>%{L%}%{I%}k GER-POSSESSIVES ;",
             "e%<cop%>%<ger_perf%>:ekanlik FULL-NOMINAL-INFLECTION ; ! test build R3: was GER-POSSESSIVES, gave *ekanliki\n"
             "e%<cop%>%<neg%>%<ger_ppot%>:emaslik FULL-NOMINAL-INFLECTION ; ! test build R3: emasligi", "R3 copula")

    # ---- R15 contracted copula --------------------------------------------------------------
    s = edit(s, "FUT ;\n\nV-INFL-ABIL ;", "FUT ;\n\nV-INFL-ABIL ;\n\nCONTR-COP ; ! test build R15", "verb hub")

    # ---- R5 attached -gina on adverbs, postpositions, converbs, -ta numerals ---------------
    for old_, lbl in (("LEXICON ADV1\n%<adv%>: # ; ! this is for when the adverb is used as an adverb", "ADV1"),
                      ("LEXICON ADV2\n\n%<adv%>: # ;", "ADV2"), ("LEXICON ADV3\n\n%<adv%>: # ;", "ADV3"),
                      ("LEXICON POST\n%<post%>: # ;", "POST"), ("LEXICON POSTADV\n%<postadv%>: # ;", "POSTADV")):
        s = edit(s, old_, old_.replace(": # ;", ": CLIT-GINA-OPT ;", 1) + " ! test build R5: was #", lbl)
    s = edit(s, "%<gna_perf%>:%>%{i%}b # ;", "%<gna_perf%>:%>%{i%}b CLIT-GINA-OPT ; ! test build R5: was #", "gna_perf")
    s = edit(s, "%<num%>%<cl%>:%>ta # ;", "%<num%>%<cl%>:%>ta CLIT-GINA-OPT ; ! test build R5 (bittagina): was #", "num cl")
    s = edit(s, "%+gana%<postadv%>:% %{G%}ana # ; ! \"\"",
             "%+gana%<postadv%>:% %{G%}ana # ; ! \"\" ! Dir/LR ! test build R5: separate gana kept for analysis only\n"
             "CLIT-GINA ; ! test build R5: attached -gina/-kina/-qina", "R5 gana")

    # ---- R4 -ki: interrogative adverbs, -ng/-ngiz imperatives, and attested predicatives -----
    s = edit(s, "%<adv%>%<itg%>: # ; !  CASES ;", "%<adv%>%<itg%>: CLIT-KI-OPT ; !  CASES ; ! test build R4 (negaki): was #",
             "ADV-ITG")
    s = edit(s, "%<imp%>%<p2%>%<pl%>:%>%{i%}ng # ; !Dir/LR",
             "%<imp%>%<p2%>%<pl%>:%>%{i%}ng CLIT-KI-OPT ; !Dir/LR ! test build R4 (qarangki): was #", "imp pl ng")
    s = edit(s, "%<imp%>%<p2%>%<pl%>:%>%{i%}ngiz # ; ",
             "%<imp%>%<p2%>%<pl%>:%>%{i%}ngiz CLIT-KI-OPT ; ! test build R4: was #", "imp pl ngiz")

    # ---- R9 terminative -gacha (nouns, demonstratives, personal pronouns) -------------------
    s = edit(s, "LEXICON CASES-COMMON\n\n%<gen%>:%>ning CLITICS-NO-COP ;",
             "LEXICON CASES-COMMON\n\n%<gen%>:%>ning CLITICS-NO-COP ;\n"
             "%<term%>:%>%{G%}acha CLITICS-NO-COP ; ! test build R9", "R9 CASES-COMMON")
    s = edit(s, "LEXICON CASE-COMMON\n\n%<gen%>:%>ning CLITICS-NO-COP ;",
             "LEXICON CASE-COMMON\n\n%<gen%>:%>ning CLITICS-NO-COP ;\n"
             "%<term%>:%>%{G%}acha CLITICS-NO-COP ; ! test build R9", "R9 CASE-COMMON")
    s = edit(s, "%<prn%>%<dem%>%<dat%>:nga # ;",
             "%<prn%>%<dem%>%<dat%>:nga # ;\n%<prn%>%<dem%>%<term%>:ngacha # ; ! test build R9: bungacha, shungacha",
             "R9 PRON-DEM-BU")

    # ---- de- gets the {й} glide like ye- (deyuvchi, deyiladi, deyish) --------------------------
    for cls in ("VERB-TV ; ! \"to say\"", "V-IV ; ! ", "V-TV ; ! "):
        s = edit(s, f"de:de {cls}", f"de:de%{{й%}} {cls} ! test build: {{й}} glide (deyuvchi, deyiladi)", f"de {cls}")

    # ---- Hardcoded additions: R9 personal pronouns, R4 predicatives, R29 archaic forms ------
    prn = [("men", "p1><sg"), ("sen", "p2><sg"), ("u", "p3><sg"), ("biz", "p1><pl"), ("siz", "p2><pl"), ("ular", "p3><pl")]
    surf = {"men": "mengacha", "sen": "sengacha", "u": "ungacha", "biz": "bizgacha", "siz": "sizgacha", "ular": "ulargacha"}
    block = "".join(f"{esc(f'{p}<prn><pers><{pn}><term>')}:{surf[p]} # ; ! test build R9\n" for p, pn in prn)
    for w, a, _ in lists["r4"]:
        if "<imp>" in a or "<adv><itg>" in a:
            continue  # reached through the imperative and ADV-ITG paths above
        block += f"{esc(a)}:{w} # ; ! test build R4 (attested -ki)\n"
    arch_prn = [("u<prn><pers><p3><sg><gen><arch>", "aning"), ("u<prn><pers><p3><sg><dat><arch>", "anga"),
                ("u<prn><pers><p3><sg><acc><arch>", "ani"), ("u<prn><pers><p3><sg><abl><arch>", "andin"),
                ("u<prn><pers><p3><sg><loc><arch>", "anda"), ("ular<prn><pers><p3><pl><nom><arch>", "alar"),
                ("bu<prn><dem><nom><arch>", "bul"), ("kabi<post><arch>", "kibi")]
    for a, w in arch_prn:
        block += f"{esc(a)}:{w} # ; ! Dir/LR ! test build R29\n"
    for w, a, _ in lists["r29"]:
        block += f"{esc(a)}:{w} # ; ! Dir/LR ! test build R29 (attested archaic form)\n"
    s = edit(s, "LEXICON Hardcoded\n\n", "LEXICON Hardcoded\n\n" + block + "\n", "Hardcoded additions")

    # ---- R8 comparative -roq for attested gradable lemmas (Root -> Comparatives) -------------
    s = edit(s, "LEXICON Root\n\nDigits ;", "LEXICON Root\n\nComparatives ; ! test build R8\nDigits ;", "Root")
    comp = "\nLEXICON Comparatives   ! R8: lemmas whose -roq form is attested (make_lists.py)\n"
    for lemma, classes, _ in lists["r8"]:
        for c in classes.split(","):
            comp += f"{lemma}:{lemma} {'COMP-ADJ' if c == 'adj' else 'COMP-ADV'} ;\n"

    # ---- new continuation lexicons (placed before the stems) ------------------------------------
    new = """
!!!!!!! TEST BUILD (results/triage/RULES.md): new continuation lexicons !!!!!!!

LEXICON GPR-POT   ! R10: -(u)vchi participle; bare = attributive, <subst> = used as a noun
# ;
%<subst%>: FULL-NOMINAL-INFLECTION ;

LEXICON AORIST-NEG   ! R39: negative aorist only (kelmaydi); the -(a)r future has its own -mas line
%<aor%>:%>%{E%} PERS3 ;

LEXICON PERS-FUT2   ! R39: person endings of the -(a)r future (kelar, kelarman, kelarlar)
%<p1%>%<sg%>:%>man CLITICS ;
%<p2%>%<sg%>:%>san CLITICS ;
%<p2%>%<frm%>%<sg%>:%>siz CLITICS ;
%<p3%>%<sg%>: FUT2-P3-CLIT ;
%<p1%>%<pl%>:%>miz CLITICS ;
%<p2%>%<pl%>:%>silar CLITICS ;
%<p2%>%<frm%>%<pl%>:%>sizlar CLITICS ;
%<p3%>%<pl%>:%>lar CLITICS ;

LEXICON FUT2-P3-CLIT   ! R39: bare kelar takes -mi, -ki, -dek but not attached +da/+day/+cha (yerda, ularda are nouns)
%+mi%<qst%>:mi # ;
%+ki%<cnjadv%>:ki # ;
%+dek%<post%>:dek # ;
# ;

LEXICON CONTR-COP   ! R15: -(a)r / -mas + contracted edi / ekan (like -gandi in INDEF-PAST)
%<fut2%>+e%<cop%>%<ifi%>:%>%{a%}r%>di PERS2 ;
%<neg%>%<fut2%>+e%<cop%>%<ifi%>:%>mas%>di PERS2 ;
%<fut2%>+e%<cop%>%<aor%>%<evid%>:%>%{a%}r%>kan V-PERS-S1 ;
%<neg%>%<fut2%>+e%<cop%>%<aor%>%<evid%>:%>mas%>kan V-PERS-S1 ;

LEXICON COMP-ADJ   ! R8
%<adj%>%<comp%>:%>roq CLITICS-INCL-COP ;
%<adj%>%<comp%>%<subst%>:%>roq SUBST ;
%<adj%>%<comp%>%<advl%>:%>roq CLITICS-INCL-COP ;

LEXICON COMP-ADV   ! R8
%<adv%>%<comp%>:%>roq CLIT-GINA-OPT ;

LEXICON CLIT-KI   ! R4
%+ki%<cnjadv%>:ki # ;

LEXICON CLIT-KI-OPT   ! R4: interrogative adverbs, -ng/-ngiz imperatives
CLIT-KI ;
# ;

LEXICON CLIT-GINA   ! R5: restrictive, attached (gina / kina after k / qina after q)
%+gina%<postadv%>:%>%{G%}ina # ;

LEXICON CLIT-GINA-OPT   ! R5: adverbs, postpositions, converbs, -ta numerals
CLIT-GINA ;
# ;
""" + comp + "\n"
    s = edit(s, "LEXICON Digits ! Use/Cic", new + "LEXICON Digits ! Use/Cic", "new lexicons")

    # ---- R7: non-voicing k/q stems (noun/adjective entries only) --------------------------------
    stems = {r[0] for r in lists["r7"]}
    out, marked = [], set()
    in_common = False
    for line in s.split("\n"):
        if line.startswith("LEXICON "):
            in_common = line.split()[1] == "Common"
        m = re.match(r"^([^!\s:%][^:]*?):(\S+)(\s+)(\S+)(\s*;.*)$", line) if in_common else None
        if m and m.group(2) in stems and re.match(r"^(N1|N-|A1|A2|A5)", m.group(4)):
            surf_ = m.group(2)
            arch = "%{K%}" if surf_.endswith("k") else "%{Q%}"
            # the voiced original stays, analysis only, so nothing that was recognised is lost;
            # the generator gets only the non-voicing stem (huquqi)
            out.append(f"{line} ! Dir/LR ! test build R7: voiced form kept for analysis only")
            line = f"{m.group(1)}:{surf_[:-1]}{arch}{m.group(3)}{m.group(4)}{m.group(5)} ! test build R7: no voicing"
            marked.add(surf_)
        out.append(line)
    missing = stems - marked
    if missing:
        raise SystemExit(f"[R7] stems not found in nominal entries: {sorted(missing)}")
    return "\n".join(out), len(marked)


def twol_changes(t):
    t = edit(t, " %{I%}:i %{u%}:i ! Vow\n",
             " %{I%}:i %{u%}:i ! Vow\n %{U%}:u %{U%}:o a:0 i:0 ! test build R11\n", "R11 alphabet")
    t = edit(t, "          %{A%} %{I%} %{E%} %{u%} ;", "          %{A%} %{I%} %{E%} %{u%} %{U%} ;", "Vow set")
    t = edit(t, "Cons = b c d f g h j k l m n p q r s t v z x y ʻ\n",
             "Cons = b c d f g h j k l m n p q r s t v z x y\n", "R20 Cons")
    t = edit(t, '"{D} as t after (some?) voiceless cons"\n%{D%}:t <=> [ :p ]/[ :0 | %>: ]* _ ;',
             '"{D} as t after p only before i: causative -tir-, progressive -yapti (test build R13: '
             'was every {D}, which gave *gaptagi*; nominal -da/-dagi/-dan never assimilate)"\n'
             '%{D%}:t <=> [ :p ]/[ :0 | %>: ]* _ i: ;', "R13")
    t = edit(t, '"{E} becomes y when following a vowel"\n%{E%}:y <=> :Vow %>: _ ;',
             '"{E} becomes y when following a vowel (test build R34: also across a deleted {й}, yeydi)"\n'
             '%{E%}:y <=> :Vow (%{й%}:0) %>: _ ;', "R34")
    t = edit(t, '"{й}:y only before -ish"\n%{й%}:y <=> _ %>: %{i%}: :s :h ;',
             '"{й}:y before -ish, the passive -{i}{L} and the -(u)v vowel {U} (test build: yeyish, deyiladi, deyuvchi)"\n'
             '%{й%}:y <=> _ (%[%-coop%]:0) %>: [ %{i%}: [ :s :h | %{L%}: ] | %{U%}: ] ;', "glide")
    t = t.rstrip("\n") + """

"stem-final a and i are deleted before the -(u)v vowel {U} (test build R11: tanla+uv = tanlov, oʻqi+uvchi = oʻquvchi)"
Vx:0 <=> _ %>: %{U%}: ;
     where Vx in ( a i ) ;

"{U} is o after a deleted stem-final a (test build R11)"
%{U%}:o <=> a:0 %>: _ ;
"""
    return t


def main():
    d, lists_dir = os.path.abspath(os.path.expanduser(sys.argv[1])), sys.argv[2]
    if os.path.basename(d) == "apertium-uzb":
        raise SystemExit("refusing to modify the original apertium-uzb; run on a copy")
    lists = {"r7": read_tsv(os.path.join(lists_dir, "r7_stems.tsv")),
             "r4": read_tsv(os.path.join(lists_dir, "r4_ki_words.tsv")),
             "r8": read_tsv(os.path.join(lists_dir, "r8_gradable.tsv")),
             "r29": read_tsv(os.path.join(lists_dir, "r29_archaic.tsv"))}
    lp = os.path.join(d, "apertium-uzb.uzb.lexc")
    tp = os.path.join(d, "apertium-uzb.uzb.twol")
    s, n7 = lexc_changes(open(lp, encoding="utf-8").read(), lists)
    t = twol_changes(open(tp, encoding="utf-8").read())
    open(lp, "w", encoding="utf-8").write(s)
    open(tp, "w", encoding="utf-8").write(t)
    print(f"applied: R7 {n7} stems, R4 {len(lists['r4'])} words, R8 {len(lists['r8'])} lemmas, "
          f"R29 {len(lists['r29'])} archaic forms")


if __name__ == "__main__":
    main()
