#!/bin/sh
# ThamizhiMorph (Apache-2.0, Sarveswaran, Dias and Butt) is not vendored here. This fetches
# the exact upstream commit this project was built and measured against, then reproduces the
# two local steps the project took:
#   1. drop upstream's stray Archive.zip (an accidentally committed macOS directory)
#   2. unzip the foma/*.zip archives flat into foma/src, where tools/ expect the lexc files
# DEST may be set to fetch somewhere else (used to check the result against an existing copy).
set -e
DEST="${DEST:-$(cd "$(dirname "$0")/.." && pwd)/data/gold/thamizhi-morph}"
COMMIT=adbacceda5e8aa902e4b6ed58a3edf5f78cd46fb
if [ -d "$DEST" ]; then echo "already present: $DEST"; exit 0; fi
git clone --quiet https://github.com/sarves/thamizhi-morph "$DEST"
git -C "$DEST" checkout --quiet "$COMMIT"
rm -rf "$DEST/.git" "$DEST/Archive.zip"
mkdir -p "$DEST/foma/src"
for z in "$DEST"/foma/*.zip; do unzip -q -o "$z" -d "$DEST/foma/src"; done
echo "fetched thamizhi-morph @ $COMMIT into $DEST"
