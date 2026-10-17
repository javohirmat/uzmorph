# SPDX-License-Identifier: GPL-3.0-only
"""Batch wrapper around a compiled apertium-uzb directory.

Words are sent one per line to the *same* pipeline the `uzb-morph` mode runs
(lt-proc -w uzb.automorf.bin); one output line comes back per input line.
A word counts as recognised when its line is a single ^surface/analysis...$ unit
whose first analysis does not start with '*'. If lt-proc splits the word into
several units (characters outside the analyser's alphabet), it is unknown.

Casing: lt-proc lets an upper-case input letter match either case in the lexicon, but a
lower-case input letter only matches lower case. So 'XX' finds the entry XX and 'Toshkent'
finds Toshkent, while 'xx', 'Xx' and 'toshkent' find nothing. A lower-cased counting key must
therefore be looked up in every casing it occurs in: key, Key, KEY, and the lexicon's own
mixed-case spellings (OʻzR, AQSh, iPhone); see `cased_forms`.
"""
from __future__ import annotations

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

_UNIT_RE = re.compile(r"\^((?:\\.|[^$\\])*)\$")
_SPLIT_RE = re.compile(r"(?<!\\)/")
_SPECIAL = set("^$/<>[]{}\\@")
_LEXC_ENTRY = re.compile(r"^([^!\s:%][^:]*?):(\S+)\s+(\S+)\s*;")
_HYPH = re.compile(r"[-‐‑]")


def is_mixed_case(s: str) -> bool:
    """Neither lower, Titlecase nor ALL-CAPS: OʻzR, AQSh, iPhone, KamAZ."""
    if s.islower() or s.isupper() or not any(ch.isalpha() for ch in s):
        return False
    return not (s[0].isupper() and (s[1:].islower() or not any(ch.isalpha() for ch in s[1:])))


def title_parts(key: str) -> str:
    """'abu-ali' -> 'Abu-Ali' (each part of a hyphenated word capitalised)."""
    return "".join(p[:1].upper() + p[1:] if i % 2 == 0 else p
                   for i, p in enumerate(re.split(r"([-‐‑])", key)))


class Apertium:
    def __init__(self, langdir: str, mode: str = "uzb-morph", gen_mode: str = "uzb-gener",
                 batch_size: int = 100_000, workers: int = 1):
        self.langdir = os.path.abspath(langdir)
        self.pipeline = self._read_mode(mode)
        self.gen_pipeline = self._read_mode(gen_mode, required=False)
        self.batch_size = batch_size
        self.workers = max(1, workers)
        self._mixed = None

    def _read_mode(self, mode: str, required: bool = True):
        path = os.path.join(self.langdir, "modes", mode + ".mode")
        if not os.path.exists(path):
            if required:
                raise FileNotFoundError(f"{path} not found -- did you build apertium-uzb (make)?")
            return None
        with open(path, encoding="utf-8") as f:
            return f.read().strip()

    # ---------------------------------------------------------------- low level
    def _run(self, pipeline: str, lines: list[str]) -> list[str]:
        inp = ("\n".join(lines) + "\n").encode("utf-8")
        p = subprocess.run(["sh", "-c", pipeline], input=inp, capture_output=True)
        if p.returncode != 0:
            raise RuntimeError(f"apertium pipeline failed: {p.stderr.decode('utf-8', 'replace')[:500]}")
        out = p.stdout.decode("utf-8").split("\n")
        if out and out[-1] == "":
            out.pop()
        if len(out) != len(lines):
            if len(lines) == 1:  # analyser emitted extra newlines: glue them back
                return [" ".join(out)]
            mid = len(lines) // 2  # find the offending line by bisection
            return self._run(pipeline, lines[:mid]) + self._run(pipeline, lines[mid:])
        return out

    @staticmethod
    def parse_line(line: str) -> list[str]:
        """Analyses for one input word; [] means unknown (or split by the tokenizer)."""
        units = _UNIT_RE.findall(line)
        if len(units) != 1:
            return []
        parts = _SPLIT_RE.split(units[0])
        analyses = parts[1:]
        if not analyses or analyses[0].startswith(("*", "#", "@")):
            return []
        return analyses

    # ---------------------------------------------------------------- analysis
    def analyses(self, words: Iterable[str]) -> list[list[str]]:
        words = list(words)
        res: list[list[str]] = [[] for _ in words]
        todo = [(i, w) for i, w in enumerate(words)
                if w and not any(c in _SPECIAL or c.isspace() for c in w)]
        chunks = [todo[s:s + self.batch_size] for s in range(0, len(todo), self.batch_size)]
        run = lambda chunk: self._run(self.pipeline, [w for _, w in chunk])  # noqa: E731
        if self.workers > 1 and len(chunks) > 1:
            with ThreadPoolExecutor(self.workers) as ex:
                outs = list(ex.map(run, chunks))
        else:
            outs = map(run, chunks)
        for chunk, out in zip(chunks, outs):
            for (i, _), line in zip(chunk, out):
                res[i] = self.parse_line(line)
        return res

    def known(self, words: Iterable[str]) -> list[bool]:
        return [bool(a) for a in self.analyses(words)]

    def known_unique(self, words: Iterable[str]) -> dict[str, bool]:
        uniq = sorted(set(words))
        return dict(zip(uniq, self.known(uniq)))

    # ---------------------------------------------------------------- casing
    def mixed_case_stems(self) -> dict[str, list[str]]:
        """Lexicon surface forms in mixed case, keyed by their lower-case spelling."""
        if self._mixed is None:
            self._mixed = {}
            path = os.path.join(self.langdir, f"{os.path.basename(self.langdir)}.uzb.lexc")
            if not os.path.exists(path):  # a copy such as apertium-uzb-test keeps the original file name
                path = os.path.join(self.langdir, "apertium-uzb.uzb.lexc")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        m = _LEXC_ENTRY.match(line)
                        s = m.group(2) if m else ""
                        if len(s) >= 3 and "%" not in s and is_mixed_case(s) and s not in \
                                self._mixed.get(s.lower(), ()):
                            self._mixed.setdefault(s.lower(), []).append(s)
            self._mixed3 = {k[:3] for k in self._mixed}
            self._mixed_max = max(map(len, self._mixed), default=0)
        return self._mixed

    def mixed_forms(self, key: str) -> list[str]:
        """Spellings of a lower-cased key that start with a mixed-case lexicon stem
        ('oʻzrda' -> ['OʻzRda']), plus 'Abu-Ali' for a hyphenated key."""
        out = []
        mixed = self.mixed_case_stems()
        if mixed and key[:3] in self._mixed3:
            for n in range(min(len(key), self._mixed_max), 2, -1):
                for stem in mixed.get(key[:n], ()):
                    out.append(stem + key[n:])
        if _HYPH.search(key):
            tp = title_parts(key)
            if tp != key[:1].upper() + key[1:]:
                out.append(tp)
        return out

    def cased_forms(self, key: str, lower=True, title=True, upper=True, mixed=True) -> list[str]:
        """The spellings in which a lower-cased key can occur, in the order they are tried."""
        forms = [key] if lower else []
        if title:
            forms.append(key[:1].upper() + key[1:])
        if upper:
            forms.append(key.upper())
        if mixed:
            forms += self.mixed_forms(key)
        seen = set()
        return [f for f in forms if not (f in seen or seen.add(f))]

    def known_keys(self, keys: list[str], try_cap: list[bool] | None = None,
                   try_upper: list[bool] | None = None) -> list[bool]:
        """keys are lower-cased; a key is known if it is analysed in some casing it occurs in:
        'key', 'Key' (proper nouns: 'Toshkentda'), 'KEY' (XX, BMT, SSSR) or a mixed-case
        lexicon spelling (OʻzR, AQSh). try_cap[i] / try_upper[i] say whether the word occurs
        capitalised / in ALL CAPS (default: try every casing)."""
        res = self.known(keys)
        for kind in ("title", "upper", "mixed"):
            todo = []
            for i, ok in enumerate(res):
                if ok:
                    continue
                if kind == "title" and (try_cap is None or try_cap[i]):
                    todo.append((i, keys[i][:1].upper() + keys[i][1:]))
                elif kind == "upper" and (try_upper is None or try_upper[i]):
                    todo.append((i, keys[i].upper()))
                elif kind == "mixed" and (try_cap is None or try_cap[i]):
                    todo += [(i, f) for f in self.mixed_forms(keys[i])]
            for (i, _), ok in zip(todo, self.known([f for _, f in todo])):
                res[i] = res[i] or ok
        return res

    # ---------------------------------------------------------------- generation
    def generate(self, analyses: list[str]) -> list[list[str]]:
        """'qil<v><tv><neg><aor><p1><sg>' -> ['qilmayman', 'qilishmayman'] ([] if not generable)."""
        if not self.gen_pipeline:
            raise RuntimeError("no uzb-gener mode found")
        out = self._run(self.gen_pipeline, ["^" + a + "$" for a in analyses])
        res = []
        for line in out:
            line = line.strip()
            res.append([] if (not line or line.startswith(("#", "*", "@"))) else line.split("/"))
        return res

    def describe(self) -> str:
        sha = ""
        try:
            sha = subprocess.run(["git", "-C", self.langdir, "log", "-1", "--format=%h %ci"],
                                 capture_output=True, text=True).stdout.strip()
        except OSError:
            pass
        return f"apertium-uzb at {self.langdir} ({sha or 'no git info'}); pipeline: {self.pipeline}"
