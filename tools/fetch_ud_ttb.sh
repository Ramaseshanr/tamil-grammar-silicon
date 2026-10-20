#!/bin/sh
# UD_Tamil-TTB is licensed CC BY-NC-SA 3.0 (non-commercial), so this repository does not
# redistribute it. This fetches the exact commit the evaluations were run against.
# Used by tools/eval_ud.py, tools/ud_misses.py, tools/morph_tokenizer.py, tools/validate_tlp1.py.
set -e
DEST="$(cd "$(dirname "$0")/.." && pwd)/data/gold/UD_Tamil-TTB"
COMMIT=a417c5d6433841694aa66aeac920c9a68d100187
if [ -d "$DEST" ]; then echo "already present: $DEST"; exit 0; fi
git clone --quiet https://github.com/UniversalDependencies/UD_Tamil-TTB "$DEST"
git -C "$DEST" checkout --quiet "$COMMIT"
rm -rf "$DEST/.git"
echo "fetched UD_Tamil-TTB @ $COMMIT into $DEST"
