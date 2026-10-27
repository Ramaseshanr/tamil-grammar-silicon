#!/usr/bin/env bash
# Regenerate, build, VERIFY against the Python, and synthesize the Tamil noun datapath.
#
# The order matters and a stage that fails must stop the run -- audit/BUILD_GUARDS.md is
# this project's record of what silent build failures cost. Nothing here is allowed to
# report success with the RTL disagreeing with tools/derive_nouns.py.
#
#   hdl/build.sh
set -euo pipefail
cd "$(dirname "$0")"

stage() { printf '\n\033[1m=== %s\033[0m\n' "$*"; }

stage "1. generate the decision logic and the oracle vectors from the fitted rules"
python3 ../tools/gen_hdl.py

stage "2. RustHDL -> Verilog  (same generator as SanskritOS/hdl_synth)"
cargo run --quiet

stage "3. GATE: the decision, over every distinct window in the gold"
iverilog -g2005 -o tb/tb.vvp tb/tb_noun_class.v gen/tamil_noun_class.v
vvp tb/tb.vvp

stage "4. GATE: the whole datapath, streaming every stem one phoneme per cycle"
iverilog -g2012 -o tb/tbs.vvp tb/tb_noun_stream.v rtl/tamil_noun_front.sv gen/tamil_noun_class.v
vvp tb/tbs.vvp

stage "5. GATE: the juncture unit (the sūtra rules), over every valid phoneme pair and flag setting"
python3 ../tools/gen_join_hdl.py
iverilog -g2012 -I. -o tb/tbj.vvp tb/tb_join.v rtl/tamil_join.sv
vvp tb/tbj.vvp

stage "6. GATE: the noun generator, on a stratified sample of cells (every class x bundle pair, plus random cells)"
python3 ../tools/gen_noun_gen_hdl.py --sample 4000
iverilog -g2012 -I. -o tb/tbg.vvp tb/tb_noun_gen.v rtl/tamil_noun_gen.sv rtl/tamil_noun_gen_core.sv rtl/tamil_join.sv
vvp tb/tbg.vvp
echo "  (the exhaustive run over every cell: tools/gen_noun_gen_hdl.py --full --out PATH, then vvp tb/tbg.vvp +vec=PATH)"

stage "7. synthesize for ECP5"
echo "  --- tamil_noun_class (the decision) ---"
yosys -s syn/ecp5.ys 2>&1 | sed -n '/=== tamil_noun_class ===/,/design hierarchy/p' \
  | grep -E "LUT4|PFUMX|L6MUX21|TRELLIS_FF" | awk '!s[$0]++'
echo "  --- tamil_noun_front (the datapath) ---"
yosys -s syn/ecp5_front.ys 2>&1 | sed -n '/=== tamil_noun_front ===/,/design hierarchy/p' \
  | grep -E "LUT4|PFUMX|L6MUX21|TRELLIS_FF" | awk '!s[$0]++'

echo "  --- tamil_join (the juncture rules) ---"
yosys -s syn/ecp5_join.ys 2>&1 | sed -n '/=== tamil_join ===/,/design hierarchy/p' \
  | grep -E "LUT4|PFUMX|L6MUX21|TRELLIS_FF" | awk '!s[$0]++'

echo "  --- tamil_noun_gen (the generator) ---"
yosys -s syn/ecp5_gen.ys 2>&1 | sed -n '/=== tamil_noun_gen ===/,/design hierarchy/p' \
  | grep -E "LUT4|PFUMX|L6MUX21|TRELLIS_FF|TRELLIS_DPR16X4" | awk '!s[$0]++'

stage "done -- RTL verified against tools/derive_nouns.py and tools/phon_rules.py"
