#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Compare two apertium-uzb builds over every corpus type: coverage, losses, gains per rule.

    python scripts/testbuild/compare_builds.py --old <path-to-apertium-uzb> --new <path-to-apertium-uzb-test> \\
        --step3 results/step3 --r7 results/testbuild/r7_stems.tsv --out results/testbuild --workers 6

No recount: every type of results/step3/work/all_types.tsv.gz is looked up in every casing it occurs
in (uzmorph/casing.py), with BOTH builds, and nothing is skipped (types unknown to the old build may be
known to the new one). Coverage uses the case-class method (definition C): ALL-CAPS uses need KEY,
mid-sentence lowercase uses need key, the rest need Key or a mixed-case spelling; each with and
without readings that are only <mistake>.

Outputs (under --out):
  coverage.json / coverage.md   all and clean coverage, with and without <mistake>, both builds
  losses.tsv                     types whose unknown occurrences rise (recognised before, not now)
  gains.tsv.gz                   every type whose unknown occurrences fall, with the rules credited
  per_rule.json                  tokens and types recovered per rule (exclusive / shared)
  samples.md                     50 random newly recognised types per rule (seed 2026)
Attribution reads the new analyses of the forms that became known (tags such as <gpr_pot>, <comp>,
<term>, <arch>; lemma-based for R7, R13, R20, R34). A type matched by several rules is "shared".
"""
import argparse
import collections
import gzip
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from uzmorph_tb import casing as cs  # noqa: E402
from uzmorph_tb import textnorm as tn  # noqa: E402
from uzmorph_tb.apertium import Apertium  # noqa: E402

OK = "ʻ"
RULE_NAMES = {
    "R3": "-ganlik/-maslik verbal nouns", "R4": "clitic -ki", "R5": "attached -gina", "R7": "non-voicing k/q stems",
    "R8": "comparative -roq", "R9": "terminative -gacha", "R10": "-(u)vchi participle", "R11": "-(u)v verbal noun",
    "R12": "-dagilar (Cyrillic р)", "R13": "{D} after p", "R15": "contracted -ardi/-masdi/-arkan",
    "R17": "-gach after k/q", "R20": "-si after oʻ", "R29": "archaic forms", "R32": "passive of vowel-final TV",
    "R34": "ye-/de- glide", "R39": "-(a)r future", "other": "not matched by any rule pattern",
}


def rules_of(analyses, r7):
    found = set()
    for a in analyses:
        lemma = re.match(r"[^<]*", a).group(0)
        if "<gpr_pot>" in a:
            found.add("R10")
        if "<ger_perf>" in a or "<ger_ppot>" in a:
            found.add("R3")
        if "<comp>" in a:
            found.add("R8")
        if "+gina<postadv>" in a:
            found.add("R5")
        if "+ki<cnjadv>" in a:
            found.add("R4")
        if re.search(r"<ger>(<|\+|$)", a):
            found.add("R11")
        if "<term>" in a:
            found.add("R9")
        if "<arch>" in a:
            found.add("R29")
        if "<fut2>+e<cop>" in a:
            found.add("R15")
        elif "<fut2>" in a:
            found.add("R39")
        if "<loc><subst><pl>" in a:
            found.add("R12")
        if "<v><tv><pass>" in a and lemma[-1:] in "aeiou":
            found.add("R32")
        if "<gna_when>" in a:
            found.add("R17")
        if lemma in r7 and "<px" in a:
            found.add("R7")
        if lemma.endswith("p") and ("<loc>" in a or "<abl>" in a or "<sim>" in a):
            found.add("R13")
        if lemma.endswith("o" + OK) and "<px3sp>" in a:
            found.add("R20")
        if lemma in ("ye", "de") and "<v>" in a:
            found.add("R34")  # ye- glide; de- got the same {й} glide after review (deyish, deyuvchi)
    return found


def read_types(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            k, *v = line.rstrip("\n").split("\t")
            yield k, [int(x) for x in v]


def main():
    ap_ = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap_.add_argument("--old", required=True)
    ap_.add_argument("--new", required=True)
    ap_.add_argument("--step3", required=True)
    ap_.add_argument("--r7", required=True)
    ap_.add_argument("--out", required=True)
    ap_.add_argument("--workers", type=int, default=6)
    ap_.add_argument("--batch", type=int, default=300_000)
    ap_.add_argument("--samples", type=int, default=50)
    args = ap_.parse_args()
    t0 = time.time()
    os.makedirs(args.out, exist_ok=True)
    r7 = {l.split("\t")[0] for l in open(args.r7, encoding="utf-8").read().splitlines()[1:] if l.strip()}
    old = Apertium(args.old, workers=args.workers, batch_size=50_000)
    new = Apertium(args.new, workers=args.workers, batch_size=50_000)
    tot = {b: {m: [0, 0, 0, 0] for m in ("C", "C-nomist")} for b in ("old", "new")}
    losses, gains = [], []
    per_rule = collections.defaultdict(lambda: {"types": 0, "tokens": 0, "types_excl": 0, "tokens_excl": 0,
                                                "types_nomist": 0, "tokens_nomist": 0})
    batch, n = [], 0

    def process(batch):
        need = set()
        for k, v in batch:
            need.update(cs.forms_needed(old, k, v))
            for p in ([p for p in tn.parts_of(k) if tn.is_word(p)] if tn.HYPHENS.search(k) else []):
                need.update(cs.forms_needed(old, p, v))
        need = sorted(need)
        an_o = dict(zip(need, old.analyses(need)))
        an_n = dict(zip(need, new.analyses(need)))
        for k, v in batch:
            parts = [p for p in tn.parts_of(k) if tn.is_word(p)] if tn.HYPHENS.search(k) else []
            res = {}
            for b, an in (("old", an_o), ("new", an_n)):
                for mist, tag in ((True, "C"), (False, "C-nomist")):
                    whole = cs.flags_of(old, k, v, an, mist)
                    pf = {p: cs.flags_of(old, p, v, an, mist) for p in parts}
                    t = cs.account(k, v, whole, pf)["C"]
                    for i in range(4):
                        tot[b][tag][i] += t[i]
                    res[(b, tag)] = t
            # change in UNKNOWN occurrences (tokens - known): a hyphenated word that becomes known as a
            # whole counts once instead of once per part, so known tokens can fall while nothing is lost
            unk = lambda b, tag: res[(b, tag)][0] - res[(b, tag)][1]  # noqa: E731
            d = unk("old", "C") - unk("new", "C")            # > 0: occurrences recovered
            dn = unk("old", "C-nomist") - unk("new", "C-nomist")
            if d < 0 or dn < 0:
                lost_forms = [f for f in cs.forms_needed(old, k, v) + parts if an_o.get(f) and not an_n.get(f)]
                losses.append((k, v[cs.C], d, dn, ",".join(lost_forms), (an_o.get(lost_forms[0]) or [""])[0] if lost_forms else ""))
            if d > 0 or dn > 0:
                forms = [f for f in cs.forms_needed(old, k, v) + parts
                         if an_n.get(f) and (not an_o.get(f) or cs.only_mistake(an_o.get(f)))]
                anas = [a for f in forms for a in an_n[f]]
                rs = rules_of(anas, r7) or {"other"}
                gains.append((k, v[cs.C], d, dn, ",".join(sorted(rs)), (anas or [""])[0]))
                for r in rs:
                    pr = per_rule[r]
                    pr["types"] += d > 0
                    pr["tokens"] += max(d, 0)
                    pr["types_nomist"] += dn > 0
                    pr["tokens_nomist"] += max(dn, 0)
                    if len(rs) == 1:
                        pr["types_excl"] += d > 0
                        pr["tokens_excl"] += max(d, 0)

    for k, v in read_types(os.path.join(args.step3, "work", "all_types.tsv.gz")):
        batch.append((k, v))
        if len(batch) >= args.batch:
            process(batch)
            n += len(batch)
            batch = []
            print(f"[{time.time() - t0:.0f}s] {n:,} types", file=sys.stderr, flush=True)
    if batch:
        process(batch)
        n += len(batch)

    pct = lambda a, b: round(100 * a / b, 3) if b else None  # noqa: E731
    cov = {b: {tag: {"tokens": t[0], "known": t[1], "clean": t[2], "known_clean": t[3],
                     "all_pct": pct(t[1], t[0]), "clean_pct": pct(t[3], t[2])} for tag, t in d.items()}
           for b, d in tot.items()}
    json.dump({"types": n, "coverage": cov, "seconds": round(time.time() - t0)},
              open(os.path.join(args.out, "coverage.json"), "w",encoding='utf-8'), indent=1)
    json.dump({r: dict(v, name=RULE_NAMES.get(r, r)) for r, v in sorted(per_rule.items(), key=lambda x: -x[1]["tokens"])},
              open(os.path.join(args.out, "per_rule.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(args.out, "losses.tsv"), "w", encoding="utf-8") as f:
        f.write("key\tcount\tunknown_increase\tunknown_increase_nomist\tlost_forms\told_analysis\n")
        for row in sorted(losses, key=lambda r: (min(r[2], r[3]), r[0])):
            f.write("\t".join(map(str, (row[0], row[1], -row[2], -row[3]) + tuple(row[4:]))) + "\n")
    with gzip.open(os.path.join(args.out, "gains.tsv.gz"), "wt", encoding="utf-8") as f:
        f.write("key\tcount\trecovered\trecovered_nomist\trules\tnew_analysis\n")
        for row in sorted(gains, key=lambda r: (-r[2], r[0])):
            f.write("\t".join(map(str, row)) + "\n")
    rnd = random.Random(2026)
    md = ["# Newly recognised word types: random samples per rule", "",
          f"{args.samples} types drawn uniformly at random (seed 2026) from all types whose recognised occurrences "
          "rose and whose new analyses use the rule. Columns: type, corpus count, recognised occurrences gained, "
          "first new analysis. Look here for false acceptances.", ""]
    by_rule = collections.defaultdict(list)
    for g in gains:
        for r in g[4].split(","):
            by_rule[r].append(g)
    for r in sorted(by_rule, key=lambda r: -per_rule[r]["tokens"]):
        xs = by_rule[r]
        pick = rnd.sample(xs, min(args.samples, len(xs)))
        md += [f"## {r} — {RULE_NAMES.get(r, r)} ({len(xs):,} types, {per_rule[r]['tokens']:,} tokens)", "",
               "| type | count | gained | new analysis |", "|---|---|---|---|"]
        md += [f"| {k} | {c:,} | {d:,} | `{a}` |" for k, c, d, dn, rs, a in sorted(pick, key=lambda x: -x[1])]
        md.append("")
    open(os.path.join(args.out, "samples.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(json.dumps(cov, indent=1))
    print(f"losses: {len(losses)} types; gains: {len(gains)} types; {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
