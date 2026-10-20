#!/usr/bin/env python3
"""
Generate the base noun grid from ThamizhiMorph: the reference the derivation is measured against.

Builds an explicit declension grid: every lexicon stem x every case x {sg, pl},
generates each cell, then analyses the result back and checks the round trip.

Unlike Sanskrit's 24-cell paradigm this grid is SET-VALUED: a cell may licence
several equally correct surfaces (maram+noun+pl+abl -> marangkalin / marangkalil /
marangkalilirunthu). Gold is the SET, and a kernel is correct if it produces a
member of the set, not one designated string.

Emits:
  derived/nouns_grid.tsv       stem <TAB> features <TAB> surface1|surface2|...
  derived/nouns_empty.tsv      cells the generator refuses (defective cells)
  derived/nouns_oneway.tsv     generated but does not analyse back to the stem
"""
import subprocess, pathlib, collections, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLD = ROOT / "data/gold/thamizhi-morph"
FST  = GOLD / "FST-Models" / "noun.fst"
OUT  = ROOT / "data/derived"
OUT.mkdir(parents=True, exist_ok=True)

# The cell inventory is EXTRACTED from Nouns.lexc, not guessed: each noun class
# there enumerates its own (features -> suffix) pairs, e.g. "+noun+pl+loc:^kkalil #;".
import re
_LEXC = (GOLD / "foma/src/Nouns.lexc").read_text(encoding="utf-8")
BUNDLES_ALL  = sorted({m.group(0) for m in re.finditer(r'^\+noun[+a-zA-Z0-9-]*', _LEXC, re.M)})
BUNDLES_CORE = [b for b in BUNDLES_ALL if "+psp" not in b]   # true veerrumai paradigm
BUNDLES_PSP  = [b for b in BUNDLES_ALL if "+psp" in b]       # postpositional tail
BUNDLES = BUNDLES_CORE
LIMIT   = int(sys.argv[1]) if len(sys.argv) > 1 else 0   # 0 = all stems

def flookup(items, invert=False):
    cmd = ["flookup"] + (["-i"] if invert else []) + [str(FST)]
    p = subprocess.run(cmd, input="\n".join(items) + "\n",
                       capture_output=True, text=True)
    res = collections.defaultdict(set)
    for line in p.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1] != "+?":
            res[parts[0]].add(parts[1])
    return res

def main():
    # The Lexicons/ wordlists are RAW SOURCE, not what is compiled: only ~4% of
    # Nouns-AUKBC appears in Nouns.lexc. The real stem inventory is the set of
    # "<stem>  C<n>SgRoot ;" declarations inside Nouns.lexc, which also carries
    # each stem's declension class.
    import re as _re
    _t = (GOLD / "foma/src/Nouns.lexc").read_text(encoding="utf-8")
    classed = _re.findall(r'^(\S+)\s+(C\d+[A-Za-z]*Root)\s*;', _t, _re.M)
    stem2cls = dict(classed)
    stems = sorted(stem2cls)
    if LIMIT:
        stems = stems[:LIMIT]
    print(f"stems: {len(stems):,} in {len(set(stem2cls.values()))} declension classes", flush=True)

    print(f"cell inventory: {len(BUNDLES_CORE)} core + {len(BUNDLES_PSP)} psp "
          f"= {len(BUNDLES_ALL)} bundles (extracted from Nouns.lexc)", flush=True)
    cells = [st + b for st in stems for b in BUNDLES]
    print(f"grid cells to generate: {len(cells):,} "
          f"({len(stems):,} stems x {len(BUNDLES)} core cells)", flush=True)

    gen = flookup(cells, invert=True)
    filled = {k: v for k, v in gen.items() if v}
    empty  = [c for c in cells if c not in filled]
    print(f"cells filled : {len(filled):,} ({100*len(filled)/len(cells):.1f}%)", flush=True)
    print(f"cells empty  : {len(empty):,}", flush=True)

    surfaces = sorted({s for v in filled.values() for s in v})
    print(f"distinct surfaces generated: {len(surfaces):,}", flush=True)

    back = flookup(surfaces)
    rows, oneway = [], []
    for cell in sorted(filled):
        stem = cell.split("+")[0]
        ok = [s for s in sorted(filled[cell]) if any(a.split("+")[0] == stem
                                                     for a in back.get(s, ()))]
        bad = [s for s in sorted(filled[cell]) if s not in ok]
        if ok:
            rows.append((stem, stem2cls.get(stem, "?"), cell.split("+", 1)[1], "|".join(ok)))
        for s in bad:
            oneway.append((cell, s))

    (OUT / "nouns_grid.tsv").write_text(
        "".join(f"{a}\t{b}\t{c}\t{d}\n" for a, b, c, d in rows), encoding="utf-8")
    (OUT / "nouns_empty.tsv").write_text(
        "".join(f"{c}\n" for c in empty), encoding="utf-8")
    (OUT / "nouns_oneway.tsv").write_text(
        "".join(f"{a}\t{b}\n" for a, b in oneway), encoding="utf-8")

    multi = sum(1 for r in rows if "|" in r[-1])
    import collections as _c
    percls = _c.Counter(r[1] for r in rows)
    print()
    print(f"round-trip VERIFIED cells : {len(rows):,}")
    print(f"  of which set-valued     : {multi:,} ({100*multi/max(len(rows),1):.1f}%)")
    print(f"one-way surfaces          : {len(oneway):,}")
    print("\ncells per declension class:")
    for k, v in percls.most_common():
        n = sum(1 for st, c in stem2cls.items() if c == k)
        print(f"   {k:<16} {v:>9,} cells  from {n:,} stems  ({v/max(n,1):.1f}/stem)")

if __name__ == "__main__":
    main()
