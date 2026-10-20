#!/bin/sh
# Fetch the frequency table this repository was measured with. tools/build_freq.py would rebuild
# it from "latest" Wikipedia, and that moves, so the exact table is a release asset instead.
# Counts only (word form, count); CC BY-SA 4.0, Wikimedia contributors. See data/gold/freq/README.md.
# FREQ_URL may be set to fetch from somewhere else (a mirror, or file:// for a local copy).
set -e
cd "$(dirname "$0")/.."
URL="${FREQ_URL:-https://github.com/Ramaseshanr/tamil-grammar-silicon/releases/download/freq-2026-09-29/tawiki_freq.tsv.gz}"
OUT=data/gold/freq/tawiki_freq.tsv
WANT=$(grep " $OUT\$" data/frozen/MANIFEST.sha256 | cut -d' ' -f1)
if [ -f "$OUT" ] && [ "$(shasum -a 256 "$OUT" | cut -d' ' -f1)" = "$WANT" ]; then echo "already present: $OUT"; exit 0; fi
mkdir -p data/gold/freq
curl -fsSL "$URL" | gunzip -c > "$OUT.part"
GOT=$(shasum -a 256 "$OUT.part" | cut -d' ' -f1)
if [ "$GOT" != "$WANT" ]; then rm -f "$OUT.part"; echo "checksum mismatch for $URL (got $GOT, want $WANT)" >&2; exit 1; fi
mv "$OUT.part" "$OUT"
echo "fetched $OUT ($(wc -l < "$OUT" | tr -d ' ') forms)"
