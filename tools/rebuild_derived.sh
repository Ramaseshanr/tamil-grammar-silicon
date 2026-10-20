#!/usr/bin/env bash
# Rebuild data/derived from a fresh clone, in the one order that works, and check every
# output against data/frozen/MANIFEST.sha256 (byte for byte). About six minutes.
#
#   tools/rebuild_derived.sh           build, then verify
#   tools/rebuild_derived.sh --verify  only compare what is already in data/derived
#
# Needs: python3, foma + flookup (the FST generator), git and unzip, and
# network access to fetch the frequency table (tools/fetch_freq.sh; see docs/REBUILD.md).
# Refuses to overwrite an existing data/derived/nouns_grid.tsv.
set -euo pipefail
cd "$(dirname "$0")/.."
D=data/derived
MANIFEST=data/frozen/MANIFEST.sha256

check() {
  echo; echo "=== checking against $MANIFEST"
  if shasum -a 256 -c "$MANIFEST" --quiet; then
    echo "  all $(wc -l < "$MANIFEST" | tr -d ' ') files byte-identical"
  else
    echo "  MISMATCH: see the lines above" >&2; return 1
  fi
}

if [ "${1:-}" = "--verify" ]; then check; exit $?; fi

stage() { printf '\n\033[1m=== %s\033[0m\n' "$*"; }

stage "0. toolchain and inputs"
for t in python3 foma flookup git unzip shasum; do
  command -v "$t" >/dev/null || { echo "missing tool: $t" >&2; exit 1; }
done
[ -e "$D/nouns_grid.tsv" ] && { echo "refusing: $D/nouns_grid.tsv exists. Move data/derived aside first." >&2; exit 1; }
tools/fetch_thamizhi_morph.sh
FREQ=data/gold/freq/tawiki_freq.tsv
want=$(grep " $FREQ\$" "$MANIFEST" | cut -d' ' -f1)
[ -f "$FREQ" ] || tools/fetch_freq.sh
[ -f "$FREQ" ] || { echo "missing $FREQ -- see docs/REBUILD.md ('The frequency table')" >&2; exit 1; }
[ "$(shasum -a 256 "$FREQ" | cut -d' ' -f1)" = "$want" ] || {
  echo "$FREQ is not the table this repository was measured with (checksum differs)." >&2
  echo "Everything built from it will differ: see docs/REBUILD.md." >&2; exit 1; }
mkdir -p "$D"

stage "1. base noun grid from ThamizhiMorph (tools/generate_noun_grid.py)"
python3 tools/generate_noun_grid.py > /dev/null
python3 tools/list_noun_stems.py

stage "2. frozen inputs (data/frozen)"
cp data/frozen/noun_rules.json "$D/noun_rules.json"
cp data/frozen/new_roots.tsv "$D/new_roots.tsv"

stage "3. noun patch chain: Arden, Naṉṉūl 181-182, register tags, corpus, n-stems"
for s in patch_gold relabel_nannul build_tagged_gold retag_by_corpus fix_nstems; do
  echo "  $s"; python3 "tools/$s.py" > /dev/null
done

stage "4. verbs (tools/build_verbs.sh)"
tools/build_verbs.sh "${TMPDIR:-/tmp}/tamilos-build"

stage "5. vikarpam grids (Naṉṉūl 243)"
python3 tools/build_vikarpam_grid.py > /dev/null
python3 tools/build_vikarpam_verbs.py > /dev/null

stage "6. paired noun rules, and the nūṟpā citations"
TAMILOS_PAIRED=1 python3 tools/derive_nouns.py learn > /dev/null
python3 tools/cite_rules.py > /dev/null
python3 tools/cite_verbs.py > /dev/null

check

stage "7. HDL regenerates identically from the rebuilt data"
python3 tools/gen_hdl.py > /dev/null
if git diff --quiet -- hdl/; then echo "  hdl/ unchanged"; else
  echo "  hdl/ differs from what is committed:" >&2; git status --short hdl >&2; exit 1; fi
