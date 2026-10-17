# SPDX-License-Identifier: GPL-3.0-only
"""Case-correct recognition of a lower-cased type, and step-3 style token accounting.

Step 3 counts lower-cased types. For each type it stores the total count and how many
occurrences were ALL-CAPS (UP), mid-sentence Titlecase (MT) and mid-sentence lowercase (ML).
The rest (R = count - UP - ML) are mid-sentence Titlecase plus sentence-initial and
digit-initial occurrences; sentence-initial words are assumed capitalised.

lt-proc lets an upper-case input letter match either case in the lexicon and a lower-case
letter only lower case. So for a type `key`:
    L  'key' is analysed                   -> lowercase occurrences are recognised
    T  'Key' is analysed (includes L)      -> Titlecase occurrences are recognised
    U  'KEY' is analysed (includes T)      -> ALL-CAPS occurrences are recognised
    M  a mixed-case lexicon spelling ('OʻzRda', 'Abu-Ali') is analysed
Each flag also exists without readings that are only <mistake> (LEXICON MIST: a lone 'ning').

Definitions of "known" used by 03b_recompute_coverage.py and the triage:
    A  step 3 as published: L, or T when the word occurs capitalised at all
    B  type level, fixed: known in some casing the word occurs in; every occurrence counts
    C  occurrence level: ALL-CAPS occurrences by U, lowercase by L, the rest by T or M
"""
from __future__ import annotations

from dataclasses import dataclass

from . import textnorm as tn

# column order of work/all_types.tsv.gz after the key
C, CYR, UP, MT, ML, DF, KNOWN = range(7)


def only_mistake(analyses: list[str]) -> bool:
    return bool(analyses) and all("<mistake>" in a for a in analyses)


@dataclass
class Flags:
    L: bool = False
    T: bool = False
    U: bool = False
    M: bool = False
    # first analysis that made each casing known (for reports)
    form: str = ""
    analysis: str = ""


def forms_needed(ap, key: str, stats, skip_lower_title: bool = False) -> list[str]:
    """Strings to analyse for one piece of a type with the given stats."""
    up, r = stats[UP], stats[C] - stats[UP] - stats[ML]
    out = []
    if not skip_lower_title:
        out += [key, key[:1].upper() + key[1:]]
    if up > 0:
        out.append(key.upper())
    if r > 0:
        out += ap.mixed_forms(key)
    return out


def flags_of(ap, key: str, stats, an: dict, mistakes: bool, skip_lower_title=False) -> Flags:
    """an: string -> analyses. mistakes=False ignores readings that are only <mistake>."""
    ok = (lambda a: bool(a)) if mistakes else (lambda a: bool(a) and not only_mistake(a))
    f = Flags()
    if not skip_lower_title:
        title = key[:1].upper() + key[1:]
        f.L = ok(an.get(key, []))
        f.T = f.L or ok(an.get(title, []))
        if f.T:
            f.form = key if f.L else title
    f.U = f.T
    if not f.U and stats[UP] > 0:
        f.U = ok(an.get(key.upper(), []))
        if f.U:
            f.form = key.upper()
    if stats[C] - stats[UP] - stats[ML] > 0:
        for m in ap.mixed_forms(key):
            if ok(an.get(m, [])):
                f.M = True
                f.form = f.form or m
                break
    if f.form:
        f.analysis = (an.get(f.form) or [""])[0]
    return f


def known_A(f: Flags, stats, is_part: bool) -> bool:
    try_cap = is_part or stats[C] != stats[ML]
    return f.L or (try_cap and f.T)


def known_B(f: Flags, stats) -> bool:
    c, up, ml = stats[C], stats[UP], stats[ML]
    r = c - up - ml
    return f.L or (c - ml > 0 and f.T) or (up > 0 and f.U) or (r > 0 and f.M)


def known_C(f: Flags, cls: str) -> bool:
    return {"U": f.U, "L": f.L, "R": f.T or f.M}[cls]


def class_counts(stats) -> dict[str, int]:
    c, up, ml = stats[C], stats[UP], stats[ML]
    return {"U": up, "L": ml, "R": c - up - ml}


def account(key: str, stats, whole: Flags, parts: dict[str, Flags]) -> dict[str, list[int]]:
    """Token tallies for one type under A, B and C, as step 3 counts them.
    Returns {def: [tokens, known, clean, known_clean]}. An unknown hyphenated word counts as
    its word parts (number parts are dropped), each with the type's count."""
    c, up = stats[C], stats[UP]
    out = {}
    plist = [p for p in tn.parts_of(key) if tn.is_word(p)] if tn.HYPHENS.search(key) else []

    def pieces(whole_known: bool):
        if whole_known or not plist:
            return [(key, whole, False)]
        return [(p, parts[p], True) for p in plist]

    for d in ("A", "B"):
        test = (lambda f, part: known_A(f, stats, part)) if d == "A" else (lambda f, part: known_B(f, stats))
        t = [0, 0, 0, 0]
        for p, f, is_part in pieces(test(whole, False)):
            k = test(f, is_part)
            clean = c - up if tn.is_clean_key(p) else 0
            t[0] += c
            t[1] += c * k
            t[2] += clean
            t[3] += clean * k
        out[d] = t
    t = [0, 0, 0, 0]
    for cls, n in class_counts(stats).items():
        if n <= 0:
            continue
        for p, f, _ in pieces(known_C(whole, cls)):
            k = known_C(f, cls)
            clean = n if (cls != "U" and tn.is_clean_key(p)) else 0
            t[0] += n
            t[1] += n * k
            t[2] += clean
            t[3] += clean * k
    out["C"] = t
    return out
