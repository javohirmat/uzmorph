# SPDX-License-Identifier: GPL-3.0-only
"""Uzbek text normalisation, tokenisation and a basic Cyrillic->Latin converter.

Canonical characters used everywhere in this repo (they match the apertium-uzb lexicon):
    oʻ gʻ   o/g + U+02BB MODIFIER LETTER TURNED COMMA
    tutuq   U+02BC MODIFIER LETTER APOSTROPHE

Why this matters: apertium-uzb accepts ' ‘ ’ ` ´ as variants of oʻ/gʻ, but it only
accepts the tutuq as U+02BC. uz-books-v2 writes the tutuq as ’ (U+2019), and lt-proc
then splits "ta’lim" into "ta" + "’" + "lim" -- both halves get (wrong) analyses, so
un-normalised text silently inflates coverage.

Both modifier letters are Unicode category Lm, so after normalisation a plain
[^\\W_]+ regex keeps "oʻqiyapman" and "taʼlim" as single tokens.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

OKINA = "\u02bb"  # ʻ
TUTUQ = "\u02bc"  # ʼ

_APOS_CHARS = "'`\u00b4\u2018\u2019\u02bb\u02bc\u02b9\u02bf\u2032"
_APOS = "[" + re.escape(_APOS_CHARS) + "]"
_L = r"[^\W\d_]"  # any letter (note: ʻ and ʼ count as letters)

_INVISIBLE = dict.fromkeys(map(ord, "\u00ad\u200b\u200c\u200d\u2060\ufeff"), None)
_BREVE = str.maketrans({"ŏ": "o" + OKINA, "Ŏ": "O" + OKINA})
_MAP2026 = str.maketrans({"ö": "o" + OKINA, "Ö": "O" + OKINA, "ğ": "g" + OKINA,
                          "Ğ": "G" + OKINA, "ş": "sh", "Ş": "Sh", "ç": "ch", "Ç": "Ch"})

_OG_AFTER_LETTER = re.compile(r"(?<=" + _L + r")([oOgG])" + _APOS)
_OG_BEFORE_LETTER = re.compile(r"([oOgG])" + _APOS + r"(?=" + _L + r")")
_TUTUQ_RE = re.compile(r"(?<=" + _L + r")(?<![oOgG])" + _APOS + r"(?=" + _L + r")")
_STRAY_OKINA = re.compile(r"(?<![oOgG])\u02bb")
_STRAY_TUTUQ = re.compile(r"(?<!" + _L + r")\u02bc|\u02bc(?!" + _L + r")")
_LINEBREAK_HYPHEN = re.compile(r"(" + _L + r")[-\u2010\u2011]\s*\n\s*(" + _L + r")")

WORD_RE = re.compile(r"[^\W_]+")  # plain words, hyphens split (used for duplicate detection)
# Word tokens keep hyphenated words together (xilma-xil, bir-biri): lt-proc analyses them as one
# unit when the lexicon has them, and splits them into parts only when it does not.
TOKEN_RE = re.compile(r"[^\W_]+(?:[-\u2010\u2011][^\W_]+)*")
HYPHENS = re.compile(r"[-\u2010\u2011]")
# first token after a sentence boundary or at the start of a line
_SENT_INIT_RE = re.compile(r"(?:^|(?<=[.!?\u2026]))[\s\"'\u00ab\u00bb\u201c\u201d\u2018\u2019(\[\u2014\u2013-]*([^\W_]+(?:[-\u2010\u2011][^\W_]+)*)",
                           re.MULTILINE)
_CYR_RE = re.compile(r"[\u0400-\u04ff]")
_LAT_RE = re.compile(r"[A-Za-z\u00c0-\u024f]")


def _join_hyphen(m: re.Match) -> str:
    # join "kito-\nblar" -> "kitoblar" only when the continuation is lowercase
    return m.group(1) + m.group(2) if m.group(2).islower() else m.group(0)


def normalize(text: str, dehyphenate: bool = True, map2026: bool = False) -> str:
    """NFC, remove invisible chars, join line-break hyphenation, canonical apostrophes."""
    text = unicodedata.normalize("NFC", text).translate(_INVISIBLE).translate(_BREVE)
    if map2026:
        text = text.translate(_MAP2026)
    if dehyphenate and "\n" in text:
        text = _LINEBREAK_HYPHEN.sub(_join_hyphen, text)
    text = _OG_AFTER_LETTER.sub(lambda m: m.group(1) + OKINA, text)
    # second pass: in word-final "yo‘g‘" the lookbehind of g‘ saw the unconverted ‘ (not a letter)
    text = _OG_AFTER_LETTER.sub(lambda m: m.group(1) + OKINA, text)
    text = _OG_BEFORE_LETTER.sub(lambda m: m.group(1) + OKINA, text)
    text = _TUTUQ_RE.sub(TUTUQ, text)
    # modifier letters left outside a word context are really quote marks
    text = _STRAY_OKINA.sub("\u2018", text)
    text = _STRAY_TUTUQ.sub("\u2019", text)
    return text


def is_word(tok: str) -> bool:
    """A word token must contain at least one letter (pure numbers are not words)."""
    return any(ch.isalpha() for ch in tok)


def parts_of(tok: str) -> list[str]:
    """'xilma-xil' -> ['xilma', 'xil']; a word without hyphens -> [word]."""
    return [p for p in HYPHENS.split(tok) if p]


def letters(tok: str) -> int:
    return sum(1 for ch in tok if ch.isalpha() and ch not in (OKINA, TUTUQ))


def word_tokens(norm_text: str) -> list[str]:
    """Word tokens of already-normalised text (hyphenated words stay one token)."""
    return [t for t in TOKEN_RE.findall(norm_text) if is_word(t)]


def sentence_initial_tokens(norm_text: str) -> list[str]:
    return _SENT_INIT_RE.findall(norm_text)


def script_of(tok: str) -> str:
    c = _CYR_RE.search(tok) is not None
    l = _LAT_RE.search(tok) is not None
    if c and l:
        return "mixed"
    return "cyr" if c else ("lat" if l else "other")


def has_cyrillic(text: str) -> bool:
    return _CYR_RE.search(text) is not None


def is_clean(tok: str) -> bool:
    """Clean = letters only (hyphens inside pair words allowed), 3+ letters (ʻ ʼ not counted), not ALL-CAPS."""
    core = HYPHENS.sub("", tok).replace(OKINA, "").replace(TUTUQ, "")
    return len(core) >= 3 and core.isalpha() and not tok.isupper()


def is_clean_key(key: str) -> bool:
    """Same as is_clean for a lower-cased key (the all-caps test is done on counts)."""
    core = HYPHENS.sub("", key).replace(OKINA, "").replace(TUTUQ, "")
    return len(core) >= 3 and core.isalpha()


# --------------------------------------------------------------------------------------
# Basic Cyrillic -> Latin (1995 alphabet). No exception table: Russian loans with ц/е/ъ
# are approximated. Plug in your own converter with --cyr2lat module:path.py:function.
# --------------------------------------------------------------------------------------
_CYR_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ч": "ch", "ш": "sh",
    "щ": "sh", "ы": "i", "э": "e", "ю": "yu", "я": "ya", "ў": "o" + OKINA, "қ": "q",
    "ғ": "g" + OKINA, "ҳ": "h",
}
_CYR_VOWELS = set("аеёиоуэюяўы")


def _cyr2lat_basic(word: str) -> str:
    low = word.lower()
    out = []
    for i, ch in enumerate(low):
        prev = low[i - 1] if i else ""
        nxt = low[i + 1] if i + 1 < len(low) else ""
        if ch == "е":
            out.append("ye" if (not prev or prev in _CYR_VOWELS or prev in "ъь") else "e")
        elif ch == "ц":
            out.append("ts" if prev in _CYR_VOWELS and prev else "s")
        elif ch == "ъ":
            out.append("" if nxt in "еёюя" else TUTUQ)
        elif ch == "ь":
            out.append("")
        else:
            out.append(_CYR_MAP.get(ch, ch))
    lat = "".join(out)
    if not lat:
        return lat
    if len(word) > 1 and word.isupper():
        return lat.upper()
    if word[0].isupper():
        return lat[0].upper() + lat[1:]
    return lat


_cyr2lat_impl = _cyr2lat_basic


def set_cyr2lat(func) -> None:
    """Replace the word-level converter (e.g. with your exception-table converter)."""
    global _cyr2lat_impl
    _cyr2lat_impl = func
    key_of.cache_clear()


def load_cyr2lat(spec: str):
    """spec = 'builtin' or 'module:/path/to/file.py:function_name'."""
    if spec in ("", "builtin", None):
        return
    import importlib.util
    _, path, fn = spec.split(":", 2)
    mod_spec = importlib.util.spec_from_file_location("user_cyr2lat", path)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    set_cyr2lat(getattr(mod, fn))


def cyr2lat_word(word: str) -> str:
    return _cyr2lat_impl(word)


def cyr2lat_text(text: str) -> str:
    return re.sub(r"[\u0400-\u04ff]+", lambda m: cyr2lat_word(m.group()), text)


@lru_cache(maxsize=1 << 21)
def key_of(tok: str) -> str:
    """Counting key: pure-Cyrillic tokens converted to Latin, then lower-cased.
    Mixed-script tokens are left alone so they stay visibly broken (OCR junk)."""
    if script_of(tok) == "cyr":
        tok = cyr2lat_word(tok)
    return tok.lower()


def case_class(tok: str) -> str:
    """U = ALL-CAPS (2+ letters), T = Titlecase, L = lowercase, O = other."""
    if len(tok) > 1 and tok.isupper():
        return "U"
    c = tok[0]
    if c.isupper():
        return "T"
    if c.islower():
        return "L"
    return "O"
