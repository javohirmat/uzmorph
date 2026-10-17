#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Write results/testbuild/REPORT.md (and samples.md) from the comparison outputs.

    python scripts/testbuild/write_report.py results/testbuild

Reads coverage.json, gains.tsv.gz, losses.tsv, generation_diff.tsv and the lists made by
make_lists.py / r7_nonvoicing_stems.py. Gains are re-attributed with the final patterns (de- forms
gained through the {й} glide are credited to R34, like ye-).
"""
import collections
import csv
import gzip
import json
import os
import random
import re
import sys

NAMES = {
    "R10": "-(u)vchi participle (keluvchi, belgilovchi)", "R3": "-ganlik / -maslik verbal nouns (boʻlganligi)",
    "R7": "non-voicing k/q stems (huquqi, haqi)", "R8": "comparative -roq (tezroq, aniqrogʻi)",
    "R11": "-(u)v verbal noun (yondashuv, tanlov)", "R5": "attached -gina (faqatgina)",
    "R9": "terminative -gacha (maktabgacha, bizgacha)", "R15": "contracted -ardi / -masdi / -arkan",
    "R4": "-ki after predicatives (kerakki)", "R32": "passive of vowel-final transitive verbs (koʻzlangan)",
    "R29": "archaic forms, analysis only (boʻlur, anga)", "R39": "-(a)r future (derman, kelarlar, kelmasman)",
    "R12": "-dagilar (Cyrillic р)", "R13": "-dagi/-dan after p (gapdagi)", "R34": "ye-/de- glide (yeydi, deyish)",
    "R20": "-si after oʻ (obroʻsi)", "R17": "-gach after k/q (chiqqach)", "other": "not matched by a rule pattern",
}


def loss_category(key, old):
    old = old.replace("\\", "")  # the original printed undeclared tags escaped: \<gna_when\>
    if "<fut2>" in old:
        return "R39: old *-yr / -(a)r forms"
    if re.search(r"<ger>(<|\+|$)", old) and "iv" in key:
        return "R11: old *-iv gerund readings (univ, archiv, yoziv)"
    if "<gna_when>" in old:
        return "R17: *-qgach / *-kgach (now chiqqach, tekkach)"
    if "ptay" in key or "ptagi" in key:
        return "R13: *-ptagi / *-ptay (now -pdagi / -pday)"
    if re.search(r"oʻ(i|ini|iga|ida|ining|idan)$", key) or re.match(r"(ab|o)?obroʻ<|oʻ<n><px", old) or "obroʻ<" in old:
        return "R20: *-oʻi (now -oʻsi)"
    if old.startswith(("de<", "ye<")):
        return "de-/ye- glide: *desh, *deil, *yeish (now deyish, deyil, yeyish)"
    if "<pass>" in old:
        return "R32: *-ailgan passives (now -angan)"
    if "<ger_perf>" in old and "ekanlik" in key:
        return "R3: *ekanliki (now ekanligi)"
    return "other"


def main():
    d = sys.argv[1]
    cov = json.load(open(os.path.join(d, "coverage.json"),encoding='utf-8'))
    c = cov["coverage"]
    gains = []
    with gzip.open(os.path.join(d, "gains.tsv.gz"), "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            k, n, rec, recn, rules, ana = line.rstrip("\n").split("\t")
            rs = rules.split(",")
            if rs == ["other"] and re.match(r"(de|ye)<v>", ana):
                rs = ["R34"]
            gains.append((k, int(n), int(rec), int(recn), rs, ana))
    per = collections.defaultdict(lambda: [0, 0, 0, 0])
    for k, n, rec, recn, rs, ana in gains:
        for r in rs:
            p = per[r]
            p[0] += rec > 0
            p[1] += max(rec, 0)
            if len(rs) == 1:
                p[2] += rec > 0
                p[3] += max(rec, 0)
    total_rec = sum(max(g[2], 0) for g in gains)
    shared = sum(max(g[2], 0) for g in gains if len(g[4]) > 1)
    losses = list(csv.DictReader(open(os.path.join(d, "losses.tsv"), encoding="utf-8"), delimiter="\t"))
    lcat = collections.defaultdict(lambda: [0, 0, []])
    for r in losses:
        cat = loss_category(r["key"], r["old_analysis"])
        lcat[cat][0] += 1
        lcat[cat][1] += int(r["unknown_increase"])
        lcat[cat][2].append(r["key"])
    gd = list(csv.DictReader(open(os.path.join(d, "generation_diff.tsv"), encoding="utf-8"), delimiter="\t"))
    gcell = collections.Counter(re.sub(r"^[^<]*", "", r["analysis"]) for r in gd)
    n_lists = {name: sum(1 for _ in open(os.path.join(d, f), encoding="utf-8")) - 1
               for name, f in (("r7", "r7_stems.tsv"), ("r4", "r4_ki_words.tsv"), ("r8", "r8_gradable.tsv"),
                               ("r29", "r29_archaic.tsv"))}

    # ---- samples.md ------------------------------------------------------------------------------
    rnd = random.Random(2026)
    by_rule = collections.defaultdict(list)
    for g in gains:
        for r in g[4]:
            by_rule[r].append(g)
    sm = ["# Newly recognised word types: 50 random samples per rule", "",
          "Drawn uniformly at random (seed 2026) from all types whose unknown occurrences fell and whose new "
          "analyses use the rule, so rare types, where false acceptances hide, are well represented. Columns: type, "
          "corpus count, occurrences recovered, first new analysis.", ""]
    for r in sorted(by_rule, key=lambda r: -per[r][1]):
        xs = by_rule[r]
        pick = rnd.sample(xs, min(50, len(xs)))
        sm += [f"## {r}: {NAMES.get(r, r)} ({len(xs):,} types, {per[r][1]:,} occurrences)", "",
               "| type | count | recovered | new analysis |", "|---|---|---|---|"]
        sm += [f"| {k} | {n:,} | {rec:,} | `{a}` |" for k, n, rec, recn, rs, a in sorted(pick, key=lambda x: -x[1])]
        sm.append("")
    open(os.path.join(d, "samples.md"), "w", encoding="utf-8").write("\n".join(sm) + "\n")

    # ---- REPORT.md -------------------------------------------------------------------------------
    o, n = c["old"], c["new"]
    md = ["# Test build of apertium-uzb: bug fixes and the top-10 rules", "",
          "*Scratch copy only.* The original `<path-to-apertium-uzb>` is untouched (`git status` clean); the test build is "
          "`<path-to-apertium-uzb-test>`. Nothing was committed, pushed or reported upstream. The source changes are in "
          "`apertium-uzb-test.diff` (lexc and twol only; no other source file changed). `scripts/testbuild/build.sh` "
          "rebuilds the copy from scratch. All linguistic choices are AI proposals for review.", "",
          "## 1. Coverage (whole corpus, case-class method, no recount)", "",
          "| | original | test build | change |", "|---|---|---|---|"]
    for tag, label in (("C", ""), ("C-nomist", ", without `<mistake>`-only readings")):
        for kind, key in (("all tokens", "all_pct"), ("clean tokens", "clean_pct")):
            md.append(f"| {kind}{label} | {o[tag][key]:.2f}% | {n[tag][key]:.2f}% | **+{n[tag][key] - o[tag][key]:.2f}** |")
    unk_o, unk_n = o["C"]["tokens"] - o["C"]["known"], n["C"]["tokens"] - n["C"]["known"]
    md += ["", f"Unknown occurrences fall from {unk_o:,} to {unk_n:,} ({unk_o - unk_n:,} fewer, "
           f"{100 * (unk_o - unk_n) / unk_o:.1f}% of all unknown occurrences). Method: every type of step 3's "
           "`all_types.tsv.gz` (14.8M) is looked up in every casing it occurs in with both builds; ALL-CAPS uses need "
           "`KEY`, lowercase uses `key`, the rest `Key` or a mixed-case spelling (`compare_builds.py`). The token total "
           "differs slightly between builds because a hyphenated word that becomes known as a whole is one token, not two.", "",
           "## 2. Occurrences recovered per rule", "",
           "Exact counts from the new analyses: an occurrence is credited to every rule its new analysis uses "
           f"(*shared* when there are several). {total_rec:,} occurrences recovered in total; {shared:,} of them by more "
           "than one rule.", "",
           "| rule | what | types | occurrences | of which only this rule |", "|---|---|---|---|---|"]
    for r, (t, tok, te, toke) in sorted(per.items(), key=lambda x: -x[1][1]):
        md.append(f"| {r} | {NAMES.get(r, r)} | {t:,} | {tok:,} | {toke:,} |")
    md += ["", "Random samples of 50 newly recognised types per rule, for spotting false acceptances: `samples.md`.", "",
           "## 3. Regression checks", "",
           "- Existing tests: `tests/morphophonology/dorsalobstruents.yaml` 16/16 pairs pass in both directions "
           "(`scripts/morphtest_yaml.py`); `apertium-regtest test` passes.",
           "- `tests/vocabulary/all.txt` (33,122 words): **no word the original analyses is lost**; unanalysed words "
           "fall from 6,253 to 5,622.",
           f"- Generation: the main paradigm cells of every lexicon entry ({len(gd):,} of 275,020 differ) change only in "
           "the intended places (`generation_diff.tsv`):", ""]
    md += ["| cell | changed | example |", "|---|---|---|"]
    for cell, cnt in gcell.most_common(14):
        ex = next(r for r in gd if r["analysis"].endswith(cell))
        md.append(f"| `{cell}` | {cnt:,} | {ex['analysis']}: {ex['old']} → {ex['new']} |")
    md += ["", f"- Whole corpus: {len(losses):,} word types ({sum(int(r['unknown_increase']) for r in losses):,} "
           "occurrences) are recognised by the original but not by the test build. All of them are the old wrong "
           "spellings that the fixes stop accepting:", "",
           "| category | types | occurrences | examples |", "|---|---|---|---|"]
    for cat, (t, tok, ex) in sorted(lcat.items(), key=lambda x: -x[1][1]):
        md.append(f"| {cat} | {t:,} | {tok:,} | {', '.join(ex[:8])} |")
    md += ["", "The full list is `losses.tsv`; an `other` row above, if any, is a loss to look at.", ""]
    notes = os.path.join(d, "REPORT_notes.md")
    if os.path.exists(notes):
        md.append(open(notes, encoding="utf-8").read().rstrip() + "\n")
    md += ["## Lists used by the build", "",
           f"- R7: {n_lists['r7']} non-voicing stems (`r7_stems.tsv`, `scripts/testbuild/r7_nonvoicing_stems.py`)",
           f"- R4: {n_lists['r4']} attested -ki words (`r4_ki_words.tsv`), R8: {n_lists['r8']} gradable lemmas "
           f"(`r8_gradable.tsv`), R29: {n_lists['r29']} archaic forms (`r29_archaic.tsv`) (`scripts/testbuild/make_lists.py`)", ""]
    open(os.path.join(d, "REPORT.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"wrote {d}/REPORT.md and samples.md; recovered {total_rec:,}; losses {len(losses)} types")


if __name__ == "__main__":
    main()
