#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""R7: find noun/adjective stems in vowel + k/q that do not voice before vowel-initial suffixes.

    python scripts/testbuild/r7_nonvoicing_stems.py <path-to-apertium-uzb>/apertium-uzb.uzb.lexc \\
        results/step3/word_freq.tsv.gz > results/testbuild/r7_stems.tsv

The twol voicing rule makes every vowel + k/q stem voice before possessives (huquq -> *huqugʻi*).
A stem is listed when, in the corpus, its unvoiced vowel-initial possessive forms (huquqi, huquqini,
huquqiga ...) are at least twice as frequent as the voiced ones (huqugʻi ...) and occur at least 100
times. Only N/A continuation classes are considered; stems that are also verbs are skipped (their
counts mix in verb forms such as oʻqi, chiqing); stems with their own stem+i entry are skipped (xashaki,
oʻynoqi); mostly capitalised forms are not counted (Suzuki); Russian-type -ik adjectives are skipped
(ekonomiki is a Russian genitive); stems of 3 letters or fewer need 1,000+ uses and a 5:1 ratio.
"""
import gzip
import re
import sys

OK = "ʻ"
# third-person possessive forms only: -im/-ing also end other words (oqim 'flow', chiqing 'go out!')
SUFFIXES = ["i", "ini", "iga", "ida", "idan", "ining", "idagi"]
# verb forms listed as N1 by mistake (edik, topildik); short stems whose -i forms are mostly other
# words or OCR (ik = Turkish iki, shak/shaq = Arabic shakk, which geminates); loanwords in -trek/-brak
# oʻtloq: oʻtloqi is a derived adjective ('meadow-type'), the possessive is oʻtlogʻi (regression check)
# ethnonyms voice normally (oʻzbegi, qozogʻi); their -ki/-qi counts come from Russian plurals (узбеки)
EXCLUDE = {"edik", "topildik", "ik", "zak", "shak", "shaq", "bok", "chik", "trek", "brak", "oʻtloq",
           "oʻzbek", "oʻzbak", "tojik", "qozoq"}
NOMINAL = re.compile(r"^(N1|N-|A1|A2|A5)")
ENTRY = re.compile(r"^([^!\s:%][^:]*?):(\S+)\s+(\S+)\s*;")


def main():
    lexc, freq = sys.argv[1], sys.argv[2]
    stems, verbs = {}, set()
    in_common = False
    for line in open(lexc, encoding="utf-8"):
        if line.startswith("LEXICON "):
            in_common = line.split()[1] == "Common"
            continue
        m = ENTRY.match(line)
        if not (in_common and m):
            continue
        if re.match(r"^(V-|VERB-|V ;)", m.group(3)) or m.group(3) == "V":
            verbs.add(m.group(2))
        elif NOMINAL.match(m.group(3)):
            surf = m.group(2)
            if re.search(r"(?:[aeiou]|o" + OK + r")[kq]$", surf) and "%" not in surf and surf not in EXCLUDE:
                stems.setdefault(surf, set()).add(m.group(3))
    stems = {s: c for s, c in stems.items() if s not in verbs}
    # a separate stem+i word (xashaki, oʻynoqi, sayroqi) inflects like a possessive and pollutes the counts
    surfaces = set()
    for line in open(lexc, encoding="utf-8"):
        m = ENTRY.match(line)
        if m:
            surfaces.add(m.group(2))
    stems = {s: c for s, c in stems.items() if s + "i" not in surfaces}
    want = {}
    for s in stems:
        voiced = s[:-1] + ("g" if s[-1] == "k" else "g" + OK)
        for suf in SUFFIXES:
            want[s + suf] = (s, "u")
            want[voiced + suf] = (s, "v")
    cnt = {s: [0, 0] for s in stems}
    with gzip.open(freq, "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            v = line.rstrip("\n").split("\t")
            w, c = v[0], int(v[1])
            if w in want:
                s, kind = want[w]
                if kind == "u" and v[4] and float(v[4]) >= 0.5:
                    continue  # mostly capitalised mid-sentence: a name or brand (Suzuki), not a possessive
                cnt[s][0 if kind == "u" else 1] += c
    print("stem\tunvoiced\tvoiced\tclasses")
    for s, (u, v) in sorted(cnt.items(), key=lambda x: -x[1][0]):
        # Russian-type -ik adjectives: their "-iki" forms are mostly transliterated Russian genitives
        if (s.endswith("ik") and stems[s] <= {"A1", "A2"}) or re.search(r"[tnmrsxg]ik$", s):
            continue
        # very short stems collide with junk and other words (ik, nak, jek): require stronger evidence
        if len(s.replace(OK, "")) <= 3 and not (u >= 1000 and u >= 5 * v):
            continue
        if u >= 100 and u >= 2 * v:
            print(f"{s}\t{u}\t{v}\t{','.join(sorted(stems[s]))}")


if __name__ == "__main__":
    main()
