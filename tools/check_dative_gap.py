#!/usr/bin/env python3
"""
The dative after a stem ending in இ, ஈ or ஐ, in the ThamizhiMorph grid as ThamizhiMorph generates it.

Arden (A Progressive Grammar of Common Tamil, §110) has the dative as கு after a base ending in இ, ஈ or ஐ, and
உக்கு after any other letter. This counts, in the raw grid (data/derived/nouns_grid.tsv: the analyser's own output,
before any of this project's patches), the stems that end in இ, ஈ or ஐ, how many list the plain கு form, and how many
list an உக்கு form.

    python3 tools/check_dative_gap.py
"""
import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

stems, plain, uform = set(), set(), set()
for line in (ROOT / "data/derived/nouns_grid.tsv").open(encoding="utf-8"):
    p = line.rstrip("\n").split("\t")
    if len(p) < 4 or p[2] != "noun+dat": continue
    s = p[0]
    try: b = T.encode(s)
    except T.TLP1Error: continue
    if not (T.is_uyir(b[-1]) and (b[-1] & 7) in (1, 5)): continue      # இ ஈ (quality 1) or ஐ (quality 5)
    stems.add(s)
    forms = p[3].split("|")
    if s + "க்கு" in forms: plain.add(s)
    if any(f.startswith(s) and f.endswith("ுக்கு") for f in forms): uform.add(s)
print(f"stems ending in இ, ஈ or ஐ with a dative cell : {len(stems):,}")
print(f"  that list the plain கு form (மொழிக்கு)     : {len(plain):,}")
print(f"  that list an உக்கு form (மொழியுக்கு)       : {len(uform):,}")
