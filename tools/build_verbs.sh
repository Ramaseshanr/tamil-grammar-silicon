#!/usr/bin/env bash
# Build the verb grid, in the one order that is correct.
#
# The pipeline has a trap in it: roots go into the .lexc files (rebuild_with_roots.py) and
# then cells go into the same files (add_aar_cell.py), so the models must be compiled AFTER
# both. Running the stages by hand is how verb-c3.fst and verb-c62.fst came to be missing
# from the build directory for a whole session while the grid builder reported success --
# see audit/BUILD_GUARDS.md. This script exists so the order is not remembered.
#
#   tools/build_verbs.sh [builddir]
#
# -e: any stage that fails stops the build.  -o pipefail: and it still fails when its
# output is piped -- `python3 ... | tail` reports tail's exit status, which is how the
# first version of this hardening looked like it had passed.
set -euo pipefail

BUILD="${1:-/tmp/tamilos-build}"
cd "$(dirname "$0")/.."
D=data/derived

stage() { printf '\n\033[1m=== %s\033[0m\n' "$*"; }

stage "0. toolchain and vendored gold"
python3 tools/buildcheck.py "$(pwd)/data/gold/thamizhi-morph/FST-Models"

stage "1. insert the new roots and compile  -> $BUILD"
python3 tools/rebuild_with_roots.py "$BUILD"

stage "2. add the 3sghe=ஆர் honorific cell"
python3 tools/add_aar_cell.py "$BUILD"

stage "3. recompile after the cell edits"
python3 tools/compile_models.py "$BUILD"

stage "4. generate the grid"
TAMILOS_LEXC="$BUILD" TAMILOS_FST="$BUILD" TAMILOS_VGRID="$BUILD/verbs_grid_raw.tsv" \
  python3 tools/build_verb_grid.py

stage "5. apply the VERB_AUDIT corrections"
TAMILOS_VGRID="$BUILD/verbs_grid_raw.tsv" TAMILOS_VOUT="$BUILD/verbs_grid_fixed.tsv" \
  python3 tools/fix_verb_grid.py

stage "6. stem alternation (வரு, ஆகு)"
TAMILOS_VGRID="$BUILD/verbs_grid_fixed.tsv" TAMILOS_VOUT="$BUILD/verbs_grid_final.tsv" \
  python3 tools/fix_stem_alternation.py

stage "6a. the ர்-final உ alternant (Naṉṉūl 149)"
TAMILOS_VGRID="$BUILD/verbs_grid_final.tsv" TAMILOS_VOUT="$BUILD/verbs_grid_rau.tsv" \
  python3 tools/add_ra_u.py
mv "$BUILD/verbs_grid_rau.tsv" "$BUILD/verbs_grid_final.tsv"

stage "6a2. the ப and மார் plural-rational விகுதி (Naṉṉūl 327)"
TAMILOS_VGRID="$BUILD/verbs_grid_final.tsv" TAMILOS_VOUT="$BUILD/verbs_grid_327.tsv" \
  python3 tools/add_nurpa327.py
mv "$BUILD/verbs_grid_327.tsv" "$BUILD/verbs_grid_final.tsv"

stage "6b. GATE: the register column is aligned"
python3 tools/check_tags.py "$BUILD/verbs_grid_final.tsv"

# Only now replace the committed grid. Every stage above writes into the build directory,
# so a build that fails anywhere leaves the last good grid in place.
stage "7. install"
NEW=$(wc -l < "$BUILD/verbs_grid_final.tsv")
OLD=$(wc -l < "$D/verbs_grid_final.tsv" 2>/dev/null || echo 0)
echo "  new $NEW cells   previous $OLD cells"
if [ "$NEW" -lt $(( OLD * 9 / 10 )) ]; then
  echo "  REFUSING: the new grid is more than 10% smaller than the one it replaces." >&2
  echo "  It is at $BUILD/verbs_grid_final.tsv if you want to look." >&2
  exit 2
fi
mv "$BUILD/verbs_grid_final.tsv" "$D/verbs_grid_final.tsv"
echo "  installed -> $D/verbs_grid_final.tsv"
