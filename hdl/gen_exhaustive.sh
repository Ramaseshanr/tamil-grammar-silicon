#!/usr/bin/env bash
# The exhaustive gate for the noun generator: every cell of the reference, through the RTL.
#
# Generates one record per (stem, class, bundle) cell with the set of forms phon_rules.derive() licenses
# (about 210 MB), splits it across the cores, runs tb_noun_gen on each part, and sums the result. Any
# mismatch, or any part that does not finish, fails the run. About ten minutes on ten cores.
#
#   hdl/gen_exhaustive.sh
set -euo pipefail
cd "$(dirname "$0")"
W="${TMPDIR:-/tmp}/tamilos-gen-exhaustive"
rm -rf "$W"; mkdir -p "$W"
python3 ../tools/gen_noun_gen_hdl.py --full --out "$W/all.hex"
iverilog -g2012 -I. -o "$W/tb.vvp" tb/tb_noun_gen.v rtl/tamil_noun_gen.sv rtl/tamil_noun_gen_core.sv rtl/tamil_join.sv
N=$(sysctl -n hw.ncpu 2>/dev/null || nproc)
LINES=$(wc -l < "$W/all.hex")
split -l $(( (LINES + N - 1) / N )) "$W/all.hex" "$W/part_"
for f in "$W"/part_??; do
  ( vvp "$W/tb.vvp" +vec="$f" > "$f.log" 2>&1; echo "EXIT $?" >> "$f.log" ) &
done
wait
python3 - "$W" <<'PY'
import re, sys, glob
cells = forms = eq = bad = 0; ok = True
for f in sorted(glob.glob(sys.argv[1] + "/part_??.log")):
    t = open(f, errors="replace").read()
    m = [re.search(p, t) for p in (r"cells driven\s*:\s*(\d+)", r"forms from hw\s*:\s*(\d+)", r"sets equal\s*:\s*(\d+)",
                                    r"MISMATCHES\s*:\s*(\d+)", r"EXIT (\d+)")]
    if not all(m): print("part did not finish:", f); ok = False; continue
    c, fo, e, b, x = (int(g.group(1)) for g in m)
    cells += c; forms += fo; eq += e; bad += b
    if x != 0 or b != 0: ok = False
print(f"  cells driven   : {cells:,}\n  forms from hw  : {forms:,}\n  sets equal     : {eq:,}\n  MISMATCHES     : {bad:,}")
sys.exit(0 if ok and bad == 0 and eq == cells else 1)
PY
