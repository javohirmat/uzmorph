# SPDX-License-Identifier: GPL-3.0-only
"""Automatic guess of *why* Apertium does not know a frequent word.

Labels are exactly the four requested: "new stem", "missing suffix", "typo or OCR junk", "name".
These are rule-based guesses written by an AI assistant, NOT linguistic judgements: every
row carries an `evidence` string so a native speaker can overrule it quickly.

Rules, first match wins:
 1. spelling junk: digits, mixed Latin/Cyrillic, letters outside the Uzbek Latin alphabet
    (c outside "ch", w, ä ...), ʻ not after o/g, 3 identical letters in a row, no vowel, >30 letters
 2. short word (<=5 letters) seen in ALL CAPS and capitalised in >=70% of uses -> name (abbreviation)
 3. lost-diacritic spelling: u/o->oʻ, k->q, g->gʻ, x<->h (up to 3 changes) gives a known word
    >=10x more frequent (bulgan->boʻlgan, kanday->qanday, xalkaro->xalqaro) -> typo or OCR junk
 4. Titlecase in >=70% of its mid-sentence uses                            -> name
 5. one edit away from a known word >=20x more frequent                    -> typo or OCR junk
 6. two frequent known words glued together and seen in <=2 documents      -> typo or OCR junk
 7. known prefix (3+ letters) + remainder made only of inflectional morphs -> missing suffix
    (a remainder that needs a derivational morph, e.g. uslub+iyat+i, counts as a new stem:
    lexicalised derivatives get their own lexicon entry in Apertium)
 8. otherwise                                                              -> new stem
Hyphenated words (ranked as wholes because Apertium analyses known pair words as one unit) get
their own branch: hyphen inside a known word -> junk; junk part -> junk; capitalised -> name;
known hyphenated prefix + inflection -> missing suffix; otherwise -> new stem (add as one entry).
"""
from __future__ import annotations

from itertools import combinations

from .textnorm import HYPHENS, OKINA, TUTUQ, parts_of

NEW_STEM, MISSING_SUFFIX, JUNK, NAME = "new stem", "missing suffix", "typo or OCR junk", "name"

UZ_LETTERS = set("abdefghijklmnopqrstuvxyz") | {OKINA, TUTUQ}  # + 'c' only inside "ch"
VOWELS = set("aeiou")
EDIT_ALPHABET = "abdefghijklmnopqrstuvxyz" + OKINA + TUTUQ

# Suffix morphs (inflection + productive derivation), Latin spelling, common allomorphs.
_MORPHS = """
lar ning ni ga ka qa da ta dan tan dagi gi ki qi niki cha dek day
im ing si imiz miz ingiz ngiz ng lari
man san siz dir mi chi ku yu dur
di dim ding dik dingiz dilar
gan kan qan ganda gandan gani guncha gancha gach kach qach gunga kuncha
ib ar mas may ma mag maslik
yap yapti yapman yapsan yotgan yotir yotib moqda moq moqchi
sa sam sang sak sangiz salar
in il ish sh tir giz kiz qiz gaz kaz qaz ir ol ber
lik li chilik dosh kor xona zor gar iy viy at iyat ona choq gina kina qina roq mtir imtir
uv uvchi gich kich qich
ydi adi aman asan yman ysan ylik aylik sin sinlar gin gil inglar
digan ydigan adigan ajak ayotgan emish mikan misiz
mu yu
""".split()
MORPHS = set(_MORPHS)
SINGLE = {"i", "a", "y", "b", "m"}  # px3/px1sg, converb a/y/b
# Derivational morphs: a chain that needs one of these is treated as a new (lexicalised) stem.
DERIV = set("""lik li chilik dosh kor xona zor gar iy viy at iyat ona choq mtir imtir
uv uvchi gich kich qich in il ish sh tir giz kiz qiz gaz kaz qaz ir""".split())
MAX_LEN = max(map(len, MORPHS))


def segment_suffixes(rem: str):
    """Split `rem` into suffix morphs (fewest pieces, <=2 one-letter pieces, <=6 pieces)."""
    n = len(rem)
    best = [None] * (n + 1)  # best[j] = (pieces, singles, path)
    best[0] = (0, 0, [])
    for j in range(1, n + 1):
        for k in range(max(0, j - MAX_LEN), j):
            if best[k] is None:
                continue
            m = rem[k:j]
            single = len(m) == 1
            if not (m in MORPHS or (single and m in SINGLE)):
                continue
            cand = (best[k][0] + 1, best[k][1] + single, best[k][2] + [m])
            if best[j] is None or cand[:2] < best[j][:2]:
                best[j] = cand
    b = best[n]
    if b is None or b[1] > 2 or b[0] > 6:
        return None
    return b[2]


# --------------------------------------------------------------------------- candidates
def edit1(word: str) -> set[str]:
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = {a + b[1:] for a, b in splits if b}
    transposes = {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1}
    replaces = {a + c + b[1:] for a, b in splits if b for c in EDIT_ALPHABET}
    inserts = {a + c + b for a, b in splits for c in EDIT_ALPHABET}
    out = deletes | transposes | replaces | inserts
    out.discard(word)
    return out


_LOST = {"u": "o" + OKINA, "o": "o" + OKINA, "k": "q", "g": "g" + OKINA, "x": "h", "h": "x"}


def lost_diacritic_variants(word: str, max_changes: int = 3, max_positions: int = 10) -> set[str]:
    pos = [i for i, ch in enumerate(word) if ch in _LOST
           and not (ch in "og" and i + 1 < len(word) and word[i + 1] == OKINA)][:max_positions]
    out = set()
    for r in range(1, min(max_changes, len(pos)) + 1):
        for combo in combinations(pos, r):
            chars = list(word)
            for i in combo:
                chars[i] = _LOST[word[i]]
            out.add("".join(chars))
    out.discard(word)
    return out


def splits_in_two(word: str) -> list[tuple[str, str]]:
    return [(word[:i], word[i:]) for i in range(2, len(word) - 1)
            if word[i] not in (OKINA, TUTUQ)]


def prefixes(word: str) -> list[str]:
    """Proper prefixes (longest first) that do not cut oʻ/gʻ or the tutuq."""
    return [word[:i] for i in range(len(word) - 1, 1, -1) if word[i] not in (OKINA, TUTUQ)]


def candidate_strings(word: str) -> set[str]:
    s = edit1(word) | lost_diacritic_variants(word)
    for a, b in splits_in_two(word):
        s.add(a)
        s.add(b)
    return s


# --------------------------------------------------------------------------- rules
def spelling_junk(word: str):
    if any(ch.isdigit() for ch in word):
        return "contains digits"
    if any("\u0400" <= ch <= "\u04ff" for ch in word):
        return "mixed Latin/Cyrillic letters"
    bad = sorted({ch for ch in word if ch not in UZ_LETTERS and ch != "c"})
    if bad:
        return "letters outside the Uzbek Latin alphabet: " + " ".join(bad)
    if any(ch == "c" and (i + 1 >= len(word) or word[i + 1] != "h") for i, ch in enumerate(word)):
        return "'c' outside 'ch' (foreign word?)"
    if any(ch == OKINA and (i == 0 or word[i - 1] not in "og") for i, ch in enumerate(word)):
        return "ʻ not after o/g"
    if any(word[i] == word[i + 1] == word[i + 2] for i in range(len(word) - 2)):
        return "three identical letters in a row"
    if len(word) > 30:
        return "longer than 30 letters"
    return None


def classify(word: str, st: dict, cand: dict, prefix_known: dict):
    """
    word          lower-cased key
    st            {'count','df','upper','mid_title','mid_lower','cyr'} for the word
    cand          {string: (count, known)} for attested candidate strings
    prefix_known  {prefix: bool} from Apertium (prefixes need not be attested)
    Returns (label, evidence).
    """
    count = max(st["count"], 1)
    if HYPHENS.search(word):
        return _classify_hyphenated(word, st, cand, prefix_known)
    why = spelling_junk(word)
    if why:
        return JUNK, why

    capital = st["upper"] + st["mid_title"]
    if (len(word.replace(OKINA, "")) <= 5 and st["upper"] and capital >= 2
            and capital >= 0.7 * (capital + st["mid_lower"])):
        return NAME, (f"capitalised in {capital} of {capital + st['mid_lower']} uses, "
                      f"{st['upper']} in ALL CAPS (abbreviation?)")
    if not (set(word) & VOWELS):
        return JUNK, "no vowel"

    best = None
    for v in lost_diacritic_variants(word):
        c, k = cand.get(v, (0, False))
        if k and c >= 10 * count and c >= 50 and (best is None or c > best[1]):
            best = (v, c)
    if best:
        return JUNK, f"spelling without Uzbek letters; known '{best[0]}' is {best[1] / count:.0f}x more frequent"

    mid = st["mid_title"] + st["mid_lower"]
    if mid >= 3 and st["mid_title"] / mid >= 0.7:
        return NAME, f"capitalised in {st['mid_title'] / mid:.0%} of {mid} mid-sentence uses"

    best = None
    for v in edit1(word):
        c, k = cand.get(v, (0, False))
        if k and c >= 20 * count and c >= 100 and (best is None or c > best[1]):
            best = (v, c)
    if best:
        return JUNK, f"1 edit from known '{best[0]}' ({best[1] / count:.0f}x more frequent)"

    glued = None
    for a, b in splits_in_two(word):
        ca, ka = cand.get(a, (0, False))
        cb, kb = cand.get(b, (0, False))
        if ka and kb and min(ca, cb) >= 1000 and min(len(a), len(b)) >= 2:
            glued = (a, b)
            break
    if glued and st["df"] <= 2:
        return JUNK, f"looks like '{glued[0]} {glued[1]}' with the space missing (only {st['df']} docs)"

    derived = None
    for p in prefixes(word):
        if len(p) < 3 or not prefix_known.get(p):
            continue
        segs = segment_suffixes(word[len(p):])
        if not segs or (len(p) == 3 and (len(segs) > 3 or any(len(m) == 1 for m in segs))):
            continue
        if any(m in DERIV for m in segs):
            singles = sum(len(m) == 1 for m in segs)
            if derived is None or singles < derived[2]:
                derived = (p, segs, singles)
            continue
        return MISSING_SUFFIX, f"known '{p}' + suffixes {'·'.join(segs)}"
    if derived:
        return NEW_STEM, f"derived from known '{derived[0]}' + {'·'.join(derived[1])} (lexicalised derivative?)"

    note = f"; maybe compound '{glued[0]}+{glued[1]}'" if glued else ""
    known_pref = next((p for p in prefixes(word) if prefix_known.get(p) and len(p) >= 3), None)
    if known_pref:
        return NEW_STEM, f"longest known prefix '{known_pref}', rest '{word[len(known_pref):]}' is not a suffix chain{note}"
    return NEW_STEM, "no known prefix of 3+ letters" + note


def _classify_hyphenated(word, st, cand, known):
    parts = parts_of(word)
    joined = "".join(parts)
    if known.get(joined):
        cj, count = cand.get(joined, (0, False))[0], max(st["count"], 1)
        if cj >= 5 * count:
            return JUNK, f"hyphen inside the known word '{joined}' ({cj / count:.0f}x more frequent without it)"
        return NEW_STEM, (f"Apertium knows the solid spelling '{joined}' but not '{word}', which is the more "
                          f"common spelling here: add it as a variant?")
    for p in parts:
        why = spelling_junk(p)
        if why:
            return JUNK, f"part '{p}': {why}"
    mid = st["mid_title"] + st["mid_lower"]
    if mid >= 3 and st["mid_title"] / mid >= 0.7:
        return NAME, f"capitalised in {st['mid_title'] / mid:.0%} of {mid} mid-sentence uses"
    for p in prefixes(word):
        if "-" in p and not p.endswith("-") and known.get(p):
            segs = segment_suffixes(word[len(p):])
            if segs and not any(m in DERIV for m in segs):
                return MISSING_SUFFIX, f"known '{p}' + suffixes {'·'.join(segs)}"
    status = " ".join(p + ("✓" if known.get(p) else "✗") for p in parts)
    return NEW_STEM, f"hyphenated word, parts {status}: add '{word}' as one entry?"
