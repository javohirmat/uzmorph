# Pre-release review checklist

Run from the repository root.

- [ ] **Fresh venv with only `lttoolbox` installed:**
  - `pip install .` works;
  - `python -m unittest discover tests` passes;
  - the wheel and the sdist both install;
  - the sdist contains `apertium-uzb/` (the Corresponding Source).
- [ ] **CLI:** `uzmorph analyze` (`--json`, `-n 0`, `--no-guess`, `--script cyr|new|lat`) and `uzmorph generate` behave as documented.
  - Bad tags give a clear error.
  - A missing `lt-proc` gives a clear error.
- [ ] **README examples:** every example prints exactly what the README shows.
- [ ] **Rebuild:** a rebuild of `apertium-uzb/` (`./autogen.sh && make`) reproduces the three `.bin` files in `uzmorph/data/` byte for byte.
- [ ] **README numbers:** every number has a source file in `eval/results/`, `eval/nonsense/` or `eval/evidence/` (see `eval/evidence/README.md`).
- [ ] **With access to the private set:** `python eval/scripts/score_uzmorph.py` reproduces `eval/results/score_uzmorph.md`.
- [ ] **No private data:**
  - no sentences from books, news or Telegram;
  - no personal names other than the authors;
  - no absolute paths, e-mail addresses or tokens;
  - no `eval/private/`.
- [ ] **Licences:**
  - GPL-3.0-only everywhere;
  - modified apertium-uzb files carry the "MODIFIED VERSION" notice;
  - the bundled data licences are listed in the README.
