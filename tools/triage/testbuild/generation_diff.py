#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate the main paradigm cells of every lexicon entry with two builds and diff the outputs.

    python scripts/testbuild/generation_diff.py <path-to-apertium-uzb> <path-to-apertium-uzb-test> \\
        results/testbuild/generation_diff.tsv

Every difference should be explained by an intended fix (R11 -uv, R32 passive, R13 -dagi after p,
R20 -si after oʻ, R7 marked stems, R34 ye-, R39 -(a)r, R17 -gach, R12 -dagilar). The summary groups
differences by paradigm cell so unexpected ones stand out.
"""
import collections
import os
import re
import subprocess
import sys

ENTRY = re.compile(r"^([^!\s:%][^:]*?):(\S+)\s+(\S+)\s*;")
CELLS = {
    "N": ["<n><nom>", "<n><px3sp><nom>", "<n><px1sg><nom>", "<n><pl><nom>", "<n><dat>", "<n><loc>", "<n><abl>",
          "<n><loc><attr>", "<n><loc><subst><pl><nom>", "<n><px3sp><acc>"],
    "A": ["<adj>", "<adj><subst><px3sp><nom>"],
    "V": ["<v><{t}><aor><p3><sg>", "<v><{t}><ifi><p3><sg>", "<v><{t}><past><p3><sg>", "<v><{t}><ger_abst><nom>",
          "<v><{t}><gna_perf>", "<v><{t}><gpr_rsub>", "<v><{t}><prog><p3><sg>", "<v><{t}><neg><aor><p3><sg>",
          "<v><{t}><pass><gpr_rsub>", "<v><{t}><ger><nom>", "<v><{t}><gna_when>", "<v><{t}><gpr_impf>",
          "<v><{t}><caus><coop><ifi><p3><sg>"],
}


def gen(langdir, items):
    out = subprocess.run(["lt-proc", "-g", os.path.join(langdir, "uzb.autogen.bin")],
                         input="\n".join("^" + x + "$" for x in items) + "\n", capture_output=True, text=True).stdout
    return out.split("\n")[:len(items)]


def main():
    old, new, out = (os.path.expanduser(a) for a in sys.argv[1:4])
    items = set()
    in_common = False
    for line in open(os.path.join(old, "apertium-uzb.uzb.lexc"), encoding="utf-8"):
        if line.startswith("LEXICON "):
            in_common = line.split()[1] == "Common"
            continue
        m = ENTRY.match(line) if in_common else None
        if not m or "%" in m.group(1):
            continue
        lemma, cls = m.group(1), m.group(3)
        if cls.startswith(("N1", "N-")):
            items.update(lemma + c for c in CELLS["N"])
        elif cls.startswith(("A1", "A2", "A5")):
            items.update(lemma + c for c in CELLS["A"])
        elif re.match(r"^(V-TV|VERB-TV|V-IV|VERB-IV|V ;|V$)", cls):
            t = "tv" if "TV" in cls or cls == "V" else "iv"
            items.update(lemma + c.format(t=t) for c in CELLS["V"])
    items = sorted(items)
    g_old, g_new = gen(old, items), gen(new, items)
    diffs = [(i, a, b) for i, a, b in zip(items, g_old, g_new) if a != b]
    by_cell = collections.Counter(re.sub(r"^[^<]*", "", i) for i, _, _ in diffs)
    with open(out, "w", encoding="utf-8") as f:
        f.write("analysis\told\tnew\n")
        for row in diffs:
            f.write("\t".join(row) + "\n")
    print(f"{len(items):,} analyses generated with both builds; {len(diffs):,} differ")
    for cell, n in by_cell.most_common():
        ex = next((d for d in diffs if d[0].endswith(cell)), None)
        print(f"{n:>7,}  {cell:40}  e.g. {ex[0]}: {ex[1]} -> {ex[2]}")


if __name__ == "__main__":
    main()
