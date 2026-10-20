#!/usr/bin/env bash
# Place and route the noun datapath for Fmax. Fmax is a PNR result, not obtainable from
# synthesis alone -- the same point SanskritOS's measurement note makes.
#
# Only the 85k part is packaged in this nextpnr build; the design uses <1% of it either way.
set -euo pipefail
cd "$(dirname "$0")/.."
yosys -q -s syn/ecp5_pnr.ys
nextpnr-ecp5 --85k --package CABGA381 \
  --json syn/tamil_noun_front.json --textcfg syn/tamil_noun_front.cfg \
  --freq "${1:-100}" 2>&1 | grep -iE "Device utilisation|TRELLIS_|Max frequency|Program finished"
