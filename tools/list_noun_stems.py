#!/usr/bin/env python3
"""
data/derived/noun_stems_classed.tsv: every noun stem declaration in ThamizhiMorph's Nouns.lexc
with its declension class, one `stem<TAB>class` per line.

tools/generate_noun_grid.py extracts the same pairs to know what to generate; this writes them out,
because tools/validate_tlp1.py and audit/test_derivability.py read the list.

    python3 tools/list_noun_stems.py
"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data/gold/thamizhi-morph/foma/src/Nouns.lexc"
OUT = ROOT / "data/derived/noun_stems_classed.tsv"
rows = re.findall(r"^(\S+)\s+(C\d+[A-Za-z]*Root)\s*;", SRC.read_text(encoding="utf-8"), re.M)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("".join(f"{a}\t{b}\n" for a, b in rows), encoding="utf-8")
print(f"{len(rows):,} stem declarations -> {OUT.relative_to(ROOT)}")
