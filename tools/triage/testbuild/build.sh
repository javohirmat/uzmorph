#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# Build the test copy of apertium-uzb from scratch. Never touches the original.
#   build.sh <path-to-apertium-uzb> <path-to-apertium-uzb-test>
set -e
SRC="${1:?usage: build.sh <path-to-apertium-uzb> <path-to-apertium-uzb-test>}"
DST="${2:?usage: build.sh <path-to-apertium-uzb> <path-to-apertium-uzb-test>}"
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
[ "$DST" != "$SRC" ] || { echo "refusing: DST == SRC"; exit 1; }
rm -rf "$DST"
cp -RP "$SRC" "$DST"                       # -P: keep the dangling eval/ symlink as a symlink
cd "$DST"
./configure > .configure-test.log 2>&1     # Makefile paths now point at the copy
"$HERE/.venv/bin/python" "$HERE/scripts/testbuild/apply_changes.py" "$DST" "$HERE/results/testbuild"
make -j4 > .make-test.log 2>&1
rm -rf modes && make > .make-modes.log 2>&1   # the copied modes still point at the original's .bin files; make regenerates them
grep -q "$DST/uzb.automorf.bin" modes/uzb-morph.mode
echo "built $DST"
