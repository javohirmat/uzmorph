#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Corpus-attested word lists for the test build (R4 -ki, R8 -roq, R29 archaic forms).

    python scripts/testbuild/make_lists.py <path-to-apertium-uzb> results/step3/word_freq.tsv.gz results/testbuild

After review of the first test build, these three rules are restricted to what the corpus attests,
because attaching them to whole classes gave wrong readings to frequent words (yoki = yo+ki,
koʻngil = koʻn+gil, taroq = ta+roq) and made the generator produce non-words (judaroq).

  r4_ki_words.tsv      R4: the reviewed triage rows labelled R4, plus tail hits that both tail judges
                       marked valid and that occur >= 500 times; analysis = base analysis + ki<cnjadv>
  r8_gradable.tsv      R8: adjective/adverb lemmas (3+ letters) whose -roq form occurs >= 20 times and
                       is unknown to the original analyser
  r29_archaic.tsv      R29: archaic forms of lexicon verbs (-ur, -urlar, -ub, -gʻil/-gil/-qil/-kil,
                       -gʻay/-qay/-kay, -sun) and of predicatives (-dur) that occur >= 100 times and are
                       unknown to the original analyser (so no modern word gets an archaic reading)
"""
import csv
import gzip
import json
import os
import re
import subprocess
import sys

OK = "ʻ"
ENTRY = re.compile(r"^([^!\s:%][^:]*?):(\S+)\s+(\S+)\s*;")


def analyse(langdir, words):
    out = subprocess.run(["lt-proc", "-w", os.path.join(langdir, "uzb.automorf.bin")],
                         input="\n".join(words) + "\n", capture_output=True, text=True).stdout.split("\n")
    res = {}
    for w, line in zip(words, out):
        parts = re.findall(r"\^((?:\\.|[^$\\])*)\$", line)
        an = parts[0].split("/")[1:] if len(parts) == 1 else []
        res[w] = [] if (not an or an[0].startswith("*")) else an
    return res


def esc(analysis):
    """lexc upper side for an analysis string: kerak<adj>+ki<cnjadv> -> kerak%<adj%>%+ki%<cnjadv%>"""
    return re.sub(r"<([^>]+)>", r"%<\1%>", analysis).replace("+", "%+")


def main():
    langdir, freq_path, out = (os.path.expanduser(a) for a in sys.argv[1:4])
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    freq, capshare = {}, {}
    with gzip.open(freq_path, "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            v = line.rstrip("\n").split("\t")
            freq[v[0]] = int(v[1])
            capshare[v[0]] = float(v[4]) if v[4] else 0.0  # mid-sentence capitalised share
    entries = []  # (lemma, surface, class) from LEXICON Common
    in_common = False
    for line in open(os.path.join(langdir, "apertium-uzb.uzb.lexc"), encoding="utf-8"):
        if line.startswith("LEXICON "):
            in_common = line.split()[1] == "Common"
            continue
        m = ENTRY.match(line) if in_common else None
        if m and "%" not in m.group(2):
            entries.append((m.group(1), m.group(2), m.group(3)))

    # ---- R4 ------------------------------------------------------------------------------------
    r4 = {}
    for path in ("results/triage/triage_top2000.csv", "results/triage/hidden_unknowns.csv"):
        for r in csv.DictReader(open(os.path.join(root, path), encoding="utf-8")):
            if r["rule_id"] == "R4" and r["category"] == "missing_suffix_rule" and r["proposed_analysis"].endswith("+ki<cnjadv>"):
                r4[r["word"]] = r["proposed_analysis"]
    votes = {}
    for run in json.load(open(os.path.join(root, "results/triage/work/tail_judgements.json"), encoding="utf-8")):
        for v in run["verdicts"]:
            if v["rule"] == "R4":
                votes.setdefault(v["key"], []).append(v["verdict"])
    cand = [k for k, vs in votes.items() if len(vs) == 2 and all(x == "valid" for x in vs)
            and freq.get(k, 0) >= 500 and k not in r4 and k.endswith("ki")]
    an = analyse(langdir, [k[:-2] for k in cand])
    for k in cand:
        simple = [a for a in an.get(k[:-2], []) if "<mistake>" not in a and "+" not in a]
        base = next(iter(simple), None)
        if base:
            r4[k] = base + "+ki<cnjadv>"
    with open(os.path.join(out, "r4_ki_words.tsv"), "w", encoding="utf-8") as f:
        f.write("word\tanalysis\tcount\n")
        for w, a in sorted(r4.items(), key=lambda x: -freq.get(x[0], 0)):
            f.write(f"{w}\t{a}\t{freq.get(w, 0)}\n")

    # ---- R8 ------------------------------------------------------------------------------------
    grad = {}
    for lemma, surf, cls in entries:
        kind = "adj" if re.match(r"^(A1|A2|A5)", cls) and not cls.endswith("V") else \
               "adv" if re.match(r"^ADV(1|2|3)?$|^ADV$", cls) else None
        if kind and len(surf.replace(OK, "")) >= 3 and freq.get(surf + "roq", 0) >= 20:
            grad.setdefault(surf, set()).add(kind)
    known = analyse(langdir, [s + "roq" for s in grad])
    grad = {s: k for s, k in grad.items() if not known[s + "roq"]}
    with open(os.path.join(out, "r8_gradable.tsv"), "w", encoding="utf-8") as f:
        f.write("lemma\tclasses\troq_count\n")
        for s, k in sorted(grad.items(), key=lambda x: -freq.get(x[0] + "roq", 0)):
            f.write(f"{s}\t{','.join(sorted(k))}\t{freq.get(s + 'roq', 0)}\n")

    # ---- R29 -----------------------------------------------------------------------------------
    verbs = {}
    for lemma, surf, cls in entries:
        if re.match(r"^(V-TV|VERB-TV|V-IV|VERB-IV|V$|VERB-TD)", cls) and lemma == surf:
            verbs.setdefault(surf, set()).add("tv" if "TV" in cls or cls in ("V", "VERB-TD") else "iv")
    forms = {}
    vowel_final = lambda s: s[-1:] in "aeiou" or s.endswith("o" + OK)  # noqa: E731
    for v, trans in verbs.items():
        if vowel_final(v) or len(v.replace(OK, "")) < 2:
            continue  # archaic -ur/-ub/-gʻil attach to consonant-final stems
        last = v[-1]
        g = "q" if last == "q" else "k" if last == "k" else None
        opts = [("ur", "<aor><arch><p3><sg>"), ("urlar", "<aor><arch><p3><pl>"), ("ub", "<gna_perf><arch>"),
                ("sun", "<opt><p3><sg><arch>")]
        opts += [((g or "gʻ") + "il", "<imp><p2><sg><arch>"), ("gil", "<imp><p2><sg><arch>")]
        opts += [((g or "gʻ") + "ay", "<imp><arch><p3><sg>")]
        for suf, tags in opts:
            w = v + suf
            # names (Tursun, Artur, Yoqub) are capitalised mid-sentence; oʻq is a junk verb entry (oʻqi is the verb)
            if freq.get(w, 0) >= 100 and capshare.get(w, 0) < 0.5 and v not in ("oʻq",):
                for t in sorted(trans):
                    forms[(w, f"{v}<v><{t}>{tags}")] = freq[w]
    for base in ("bor", "yoʻq", "kerak", "emas", "erur", "ekan", "lozim", "zarur", "mumkin", "ham", "shul", "ul", "bu",
                 "ne", "kim", "nedur", "qayda"):
        w = base + "dur"
        if freq.get(w, 0) >= 100:
            forms[(w, None)] = freq[w]
    an = analyse(langdir, sorted({w for w, _ in forms} | {w[:-3] for w, a in forms if a is None}))
    rows = []
    for (w, a), c in forms.items():
        if an.get(w):
            continue  # already a word for the original analyser: no archaic reading
        if a is None:
            b = next((x for x in an.get(w[:-3], []) if re.search(r"<(adj|n|post|cop|prn|adv)>", x) and "+" not in x), None)
            if not b:
                continue
            a = b + "+e<cop><aor><p3><frm><sg><arch>"
        rows.append((w, a, c))
    with open(os.path.join(out, "r29_archaic.tsv"), "w", encoding="utf-8") as f:
        f.write("word\tanalysis\tcount\n")
        for w, a, c in sorted(rows, key=lambda x: -x[2]):
            f.write(f"{w}\t{a}\t{c}\n")
    print(f"R4: {len(r4)} words; R8: {len(grad)} gradable lemmas; R29: {len(rows)} archaic forms")


if __name__ == "__main__":
    main()
