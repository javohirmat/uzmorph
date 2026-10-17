# SPDX-License-Identifier: GPL-3.0-only
"""Random-access corpus readers.

A corpus spec is one of
  hf:NAME[@CONFIG][:SPLIT]   a Hugging Face dataset (downloaded once into the HF cache)
  /path/to/dir               a folder: parquet / jsonl shards, or one book per file
  /path/to/files-*.parquet   a glob
Every reader gives len(), doc(i) and domain(i), so sampling never has to read the
whole corpus.

Duplicate-split guard: tahrirchi/uz-books(-v2) ships the *same* books twice
(split `lat` and split `cyr`/`original`). If a dataset or folder has a `lat` split and
no split is named, only `lat` is read and a warning is printed. Name splits explicitly
to override (e.g. hf:tahrirchi/uz-books-v2:cyr).
"""
from __future__ import annotations

import glob
import gzip
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from typing import Iterator, Optional

TEXT_COLS = ("text", "content", "body", "matn", "raw_text", "document", "article")
TITLE_COLS = ("title", "book_title", "name", "nomi", "sarlavha", "file_name", "filename",
              "path", "source_file", "url")
DOMAIN_COLS = ("domain", "genre", "category", "type", "subset", "source", "kind", "turi", "manba")
BOOK_EXTS = (".txt", ".md", ".pdf", ".docx", ".epub", ".fb2", ".html", ".htm", ".doc", ".djvu",
             ".rtf", ".odt")
_HF_SHARD = re.compile(r"^(?P<split>[A-Za-z0-9_]+)-\d{5}-of-\d{5}")


def warn(msg: str) -> None:
    print(f"[corpus] {msg}", file=sys.stderr)


@dataclass
class Doc:
    source: str
    doc_id: str
    title: Optional[str]
    domain: str
    text: str


def _pick(names, wanted):
    low = {n.lower(): n for n in names}
    for w in wanted:
        if w in low:
            return low[w]
    return None


class Source:
    name = "?"

    def __len__(self) -> int:
        raise NotImplementedError

    def doc(self, i: int) -> Doc:
        raise NotImplementedError

    def domain(self, i: int) -> str:
        return "all"

    def title(self, i: int) -> Optional[str]:
        return self.doc(i).title

    def iter_range(self, start: int, stop: int) -> Iterator[Doc]:
        for i in range(start, stop):
            yield self.doc(i)


# ------------------------------------------------------------------ parquet shards
class ParquetSource(Source):
    def __init__(self, files: list[str], name: str, domain_hint: str = "all"):
        import pyarrow.parquet as pq
        self.pq = pq
        self.files = sorted(files)
        self.name = name
        self.domain_hint = domain_hint
        self.rg_index = []  # (file_idx, row_group, n_rows, global_start)
        self.file_start = []
        start = 0
        for fi, f in enumerate(self.files):
            self.file_start.append(start)
            md = pq.ParquetFile(f).metadata
            for rg in range(md.num_row_groups):
                n = md.row_group(rg).num_rows
                self.rg_index.append((fi, rg, n, start))
                start += n
        self.n = start
        names = pq.read_schema(self.files[0]).names
        self.text_col = _pick(names, TEXT_COLS)
        if self.text_col is None:
            raise ValueError(f"{name}: no text column among {names}")
        self.title_col = _pick(names, TITLE_COLS)
        self.domain_col = _pick(names, DOMAIN_COLS)
        self._domains = None
        self._titles = None
        self._cache = (None, None)

    def __len__(self):
        return self.n

    def _locate(self, i):
        lo, hi = 0, len(self.rg_index) - 1
        while lo < hi:  # binary search on global_start
            mid = (lo + hi + 1) // 2
            if self.rg_index[mid][3] <= i:
                lo = mid
            else:
                hi = mid - 1
        return lo, i - self.rg_index[lo][3]

    def _table(self, j):
        if self._cache[0] != j:
            fi, rg, _, _ = self.rg_index[j]
            cols = [c for c in (self.text_col, self.title_col, self.domain_col) if c]
            self._cache = (j, self.pq.ParquetFile(self.files[fi]).read_row_group(rg, columns=cols))
        return self._cache[1]

    def _column(self, col):
        vals = []
        for f in self.files:
            vals.extend(self.pq.read_table(f, columns=[col]).column(col).to_pylist())
        return vals

    def domain(self, i):
        if not self.domain_col:
            return self.domain_hint
        if self._domains is None:
            self._domains = [str(v) if v is not None else "?" for v in self._column(self.domain_col)]
        return self._domains[i]

    def title(self, i):
        if not self.title_col:
            return None
        if self._titles is None:
            self._titles = self._column(self.title_col)
        return self._titles[i]

    def doc(self, i):
        j, k = self._locate(i)
        t = self._table(j)
        text = t.column(self.text_col)[k].as_py() or ""
        title = t.column(self.title_col)[k].as_py() if self.title_col else None
        fi = self.rg_index[j][0]
        return Doc(self.name, f"{os.path.basename(self.files[fi])}#{i - self.file_start[fi]}",
                   str(title) if title is not None else None, self.domain(i), text)


# ------------------------------------------------------------------ jsonl shards
class JsonlSource(Source):
    def __init__(self, files: list[str], name: str, domain_hint: str = "all"):
        self.files = sorted(files)
        self.name = name
        self.domain_hint = domain_hint
        self.offsets = []  # (file_idx, byte_offset)
        for fi, f in enumerate(self.files):
            if f.endswith(".gz"):
                raise ValueError(f"{f}: gunzip .jsonl.gz files first (random access needs plain jsonl)")
            with open(f, "rb") as fh:
                pos = 0
                for line in fh:
                    if line.strip():
                        self.offsets.append((fi, pos))
                    pos += len(line)
        first = self._row(0) if self.offsets else {}
        self.text_col = _pick(first.keys(), TEXT_COLS)
        self.title_col = _pick(first.keys(), TITLE_COLS)
        self.domain_col = _pick(first.keys(), DOMAIN_COLS)
        if self.offsets and not self.text_col:
            raise ValueError(f"{name}: no text field among {list(first)}")

    def __len__(self):
        return len(self.offsets)

    def _row(self, i):
        fi, pos = self.offsets[i]
        with open(self.files[fi], "rb") as fh:
            fh.seek(pos)
            return json.loads(fh.readline())

    def domain(self, i):
        if not self.domain_col:
            return self.domain_hint
        return str(self._row(i).get(self.domain_col, "?"))

    def doc(self, i):
        r = self._row(i)
        title = r.get(self.title_col) if self.title_col else None
        dom = str(r.get(self.domain_col, "?")) if self.domain_col else self.domain_hint
        return Doc(self.name, f"{os.path.basename(self.files[self.offsets[i][0]])}#{i}",
                   str(title) if title is not None else None, dom, r.get(self.text_col) or "")


# ------------------------------------------------------------------ Hugging Face
class HFSource(Source):
    """hf:NAME[@CONFIG][:SPLIT] via `datasets` (non-streaming => memory-mapped, random access)."""

    def __init__(self, spec: str):
        from datasets import (concatenate_datasets, get_dataset_config_names,
                              get_dataset_split_names, load_dataset)
        body = spec[3:]
        split = None
        if ":" in body:
            body, split = body.split(":", 1)
        name, config = (body.split("@", 1) + [None])[:2] if "@" in body else (body, None)
        self.name = name
        configs = [config] if config else (get_dataset_config_names(name) or [None])
        parts = []  # (dataset, domain)
        for cfg in configs:
            splits = [split] if split else get_dataset_split_names(name, cfg)
            if not split and "lat" in splits and len(splits) > 1:
                warn(f"{name}: splits {splits} hold the same books in different scripts; "
                     f"reading only 'lat' (name a split to override)")
                splits = ["lat"]
            for sp in splits:
                ds = load_dataset(name, cfg, split=sp)
                dom = cfg if (cfg and len(configs) > 1) else "all"
                parts.append((ds, dom, sp))
        cols = parts[0][0].column_names
        self.text_col = _pick(cols, TEXT_COLS)
        if not self.text_col:
            raise ValueError(f"{name}: no text column among {cols}")
        self.title_col = _pick(cols, TITLE_COLS)
        self.domain_col = _pick(cols, DOMAIN_COLS)
        self.parts = parts
        self.starts = []
        s = 0
        for ds, _, _ in parts:
            self.starts.append(s)
            s += len(ds)
        self.n = s
        self._domain_cache = {}

    def __len__(self):
        return self.n

    def _loc(self, i):
        j = max(k for k, s in enumerate(self.starts) if s <= i)
        return j, i - self.starts[j]

    def domain(self, i):
        j, k = self._loc(i)
        ds, dom, _ = self.parts[j]
        if not self.domain_col:
            return dom
        if j not in self._domain_cache:
            self._domain_cache[j] = [str(v) for v in ds[self.domain_col]]
        return self._domain_cache[j][k]

    def doc(self, i):
        j, k = self._loc(i)
        ds, dom, sp = self.parts[j]
        row = ds[k]
        title = row.get(self.title_col) if self.title_col else None
        if self.domain_col:
            dom = str(row.get(self.domain_col))
        return Doc(self.name, f"{sp}#{k}", str(title) if title is not None else None, dom,
                   row.get(self.text_col) or "")


# ------------------------------------------------------------------ folder of book files
def _strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>", "\n", html)
    html = re.sub(r"<[^>]+>", " ", html)
    import html as _h
    return _h.unescape(html)


def _decode(raw: bytes) -> str:
    encodings = ["utf-16"] if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else []
    for enc in encodings + ["utf-8-sig"]:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    try:
        txt = raw.decode("cp1251")  # old Uzbek Cyrillic files
        if sum(1 for c in txt if "\u0400" <= c <= "\u04ff") > len(txt) * 0.2:
            return txt
    except UnicodeDecodeError:
        pass
    return raw.decode("latin-1")


def extract_text(path: str) -> tuple[str, str]:
    """Return (text, status). status is 'ok', 'empty' or 'unsupported:<why>'."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".txt", ".md"):
            with open(path, "rb") as f:
                text = _decode(f.read())
        elif ext in (".html", ".htm"):
            with open(path, "rb") as f:
                text = _strip_tags(_decode(f.read()))
        elif ext == ".fb2":
            with open(path, "rb") as f:
                text = _strip_tags(_decode(f.read()))
        elif ext in (".docx", ".odt"):
            inner = "word/document.xml" if ext == ".docx" else "content.xml"
            with zipfile.ZipFile(path) as z:
                xml = z.read(inner).decode("utf-8", "replace")
            xml = re.sub(r"</w:p>|</text:p>", "\n", xml)
            text = _strip_tags(xml)
        elif ext == ".epub":
            with zipfile.ZipFile(path) as z:
                parts = [z.read(n).decode("utf-8", "replace") for n in sorted(z.namelist())
                         if n.lower().endswith((".xhtml", ".html", ".htm"))]
            text = _strip_tags("\n".join(parts))
        elif ext == ".pdf":
            text = _run_tool(["pdftotext", "-enc", "UTF-8", path, "-"])
            if text is None:
                try:
                    from pypdf import PdfReader
                    text = "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
                except ImportError:
                    return "", "unsupported:install poppler-utils (pdftotext) or pypdf"
        elif ext == ".djvu":
            text = _run_tool(["djvutxt", path])
            if text is None:
                return "", "unsupported:install djvulibre-bin (djvutxt)"
        elif ext == ".doc":
            text = _run_tool(["antiword", path])
            if text is None:
                return "", "unsupported:install antiword"
        elif ext == ".rtf":
            with open(path, "rb") as f:
                raw = _decode(f.read())
            text = re.sub(r"\\[a-z]+-?\d* ?|[{}]", " ", raw)
        else:
            return "", f"unsupported:{ext}"
    except Exception as e:  # corrupt file etc.
        return "", f"error:{type(e).__name__}"
    return text, ("ok" if text and text.strip() else "empty")


def _run_tool(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=600)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    return p.stdout.decode("utf-8", "replace")


class FileFolderSource(Source):
    """One book per file. Title = file name; domain = first sub-folder under the root."""

    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.name = os.path.basename(self.root.rstrip("/")) or self.root
        self.paths = []
        for dp, dns, fns in os.walk(self.root):
            dns.sort()
            for fn in sorted(fns):
                if fn.lower().endswith(BOOK_EXTS) and not fn.startswith("."):
                    self.paths.append(os.path.join(dp, fn))
        self.status = {}

    def __len__(self):
        return len(self.paths)

    def domain(self, i):
        rel = os.path.relpath(self.paths[i], self.root)
        return rel.split(os.sep)[0] if os.sep in rel else "all"

    def title(self, i):
        return os.path.splitext(os.path.basename(self.paths[i]))[0]

    def doc(self, i):
        text, status = extract_text(self.paths[i])
        self.status[i] = status
        return Doc(self.name, os.path.relpath(self.paths[i], self.root), self.title(i),
                   self.domain(i), text)


# ------------------------------------------------------------------ dispatch
def _dataset_files(paths: list[str], label: str, split: Optional[str]) -> list[str]:
    """Apply the duplicate-split guard to HF-style shard names (lat-00000-of-00012-*.parquet)."""
    by_split = {}
    for p in paths:
        m = _HF_SHARD.match(os.path.basename(p))
        by_split.setdefault(m.group("split") if m else "", []).append(p)
    if split:
        if split not in by_split:
            raise ValueError(f"{label}: no shards for split '{split}' (have {sorted(by_split)})")
        return by_split[split]
    if len(by_split) > 1 and "lat" in by_split:
        warn(f"{label}: shards for splits {sorted(by_split)} found; these usually hold the same "
             f"books in different scripts, reading only 'lat' (use {label}::SPLIT to override)")
        return by_split["lat"]
    return paths


def _hf_parquet_split(spec: str):
    """hf:NAME:SPLIT where the repo stores HF-style shards (SPLIT-00000-of-000NN*.parquet):
    download only those shards (no Arrow re-encoding) and read them with ParquetSource.
    `datasets.load_dataset(name, split=...)` downloads and converts *every* split: for
    tahrirchi/uz-books-v2 that is lat+cyr, ~48 GB on disk instead of ~6.4 GB."""
    body = spec[3:]
    if ":" not in body or "@" in body:
        return None
    name, split = body.split(":", 1)
    try:
        from huggingface_hub import HfApi, snapshot_download
        files = [f for f in HfApi().list_repo_files(name, repo_type="dataset")
                 if f.endswith(".parquet") and _HF_SHARD.match(os.path.basename(f))
                 and _HF_SHARD.match(os.path.basename(f)).group("split") == split]
    except Exception as e:  # offline, private without login, no huggingface_hub ...
        warn(f"{name}: cannot list repo files ({type(e).__name__}); falling back to datasets")
        return None
    if not files:
        return None
    root = snapshot_download(name, repo_type="dataset", allow_patterns=files)
    return ParquetSource([os.path.join(root, f) for f in files], f"{name}:{split}")


def open_source(spec: str) -> Source:
    if spec.startswith("hf:"):
        return _hf_parquet_split(spec) or HFSource(spec)
    split = None
    if "::" in spec:
        spec, split = spec.split("::", 1)
    if any(ch in spec for ch in "*?["):
        paths = sorted(glob.glob(spec, recursive=True))
        if not paths:
            raise FileNotFoundError(spec)
        root_label = spec
    elif os.path.isdir(spec):
        paths = sorted(glob.glob(os.path.join(spec, "**", "*.parquet"), recursive=True))
        if not paths:
            paths = sorted(glob.glob(os.path.join(spec, "**", "*.jsonl"), recursive=True))
        if not paths:
            return FileFolderSource(spec)
        root_label = spec
    elif os.path.isfile(spec):
        paths = [spec]
        root_label = spec
    else:
        raise FileNotFoundError(spec)
    paths = _dataset_files(paths, root_label, split)
    name = os.path.basename(os.path.normpath(root_label.split("*")[0])) or root_label
    if split:
        name = f"{name}:{split}"
    if all(p.endswith(".parquet") for p in paths):
        return ParquetSource(paths, name)
    if all(p.endswith(".jsonl") for p in paths):
        return JsonlSource(paths, name)
    raise ValueError(f"{spec}: mix of file types; pass parquet or jsonl shards separately")


def open_sources(specs: list[str]) -> list[Source]:
    return [open_source(s) for s in specs]
