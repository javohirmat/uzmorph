#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Rebuild apertium-uzb-v4 from the test-build source + apply_v4.py. Never touches the original or the test copy.
set -e
M=work/morph
SRC=$M/tb/morph/apertium-uzb-test
DST=${DST:-$M/apertium-uzb-v4}
[ -d "$DST" ] || { cp -RP "$SRC" "$DST"; (cd "$DST" && ./configure > .cfg.log 2>&1); }
python3 $M/phase2/scripts/apply_v4.py "$SRC" "$DST" "$@"
cd "$DST" && make -j8 > .make.log 2>&1 || { tail -30 .make.log; exit 1; }
rm -rf modes && make > .modes.log 2>&1
grep -q "$DST/uzb.automorf.bin" modes/uzb-morph.mode && echo "built $DST"
