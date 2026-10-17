#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# apertium-uzb-v4 = test-build source + apply_v4 (F1-F4, 400 lemmas) + apply_v5 (F5-F11, 571 lemmas) + apply_v6 (G1-G5 [+ batch-2 lemmas]).
set -e
M=work/morph
SRC=$M/tb/morph/apertium-uzb-test
DST=${DST:-$M/apertium-uzb-v4}
python3 $M/phase2/scripts/apply_v4.py "$SRC" "$DST" --lemmas $M/phase2/lemmas_v4.tsv
python3 $M/phase2/scripts/apply_v5.py "$DST" --lemmas $M/phase2/lemmas_v5.tsv
python3 $M/phase2/scripts/apply_v6.py "$DST" "$@"
[ -n "$V7" ] && python3 $M/phase2/scripts/apply_v7.py "$DST"
[ -n "$V8" ] && python3 $M/phase2/scripts/apply_v8.py "$DST"
for b in $EXTRA; do python3 $M/phase2/scripts/apply_batch.py "$DST" "$b"; done
cd "$DST" && make -j8 > .make.log 2>&1 || { tail -30 .make.log; exit 1; }
rm -rf modes && make > .modes.log 2>&1
grep -q "$DST/uzb.automorf.bin" modes/uzb-morph.mode && echo "built $DST"
