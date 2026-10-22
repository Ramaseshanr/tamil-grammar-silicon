#!/usr/bin/env bash
# Place and route the noun generator for Fmax (same part and method as pnr.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
yosys -q -s syn/ecp5_gen_pnr.ys
nextpnr-ecp5 --85k --package CABGA381 \
  --json syn/tamil_noun_gen.json --textcfg syn/tamil_noun_gen.cfg \
  --freq "${1:-100}" 2>&1 | grep -iE "Device utilisation|TRELLIS_|Max frequency|Program finished"
