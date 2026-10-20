#!/usr/bin/env python3
"""
Relabel ṭu/ṟu-final stems by Naṉṉūl 181-182 instead of ThamizhiMorph's C6/C7/C8.

audit/NANNUL.md showed that split is wrong for 33% of its members, which is why no
phonological rule could predict it. Here the classes are REPLACED by the classical
kuṟṟiyalukaram taxonomy, which is rule-governed by construction:

    NDBLT   நெடில்/உயிர்த்தொடர், ṭ   -> ṭ doubles     காடு  -> காட்ட் + marker
    NDBLR   நெடில்/உயிர்த்தொடர், ṟ   -> ṟ doubles     வயிறு -> வயிற்ற் + marker
    NCLUST  cluster types (Naṉṉūl 181) -> no doubling  தொண்டு -> தொண்ட் + marker
    NMURRI  முற்றியலுகரம், two short  -> base = nom    நடு   -> நடு + glide + marker

It also REMOVES the oblique surfaces inconsistent with that verdict -- an undoubled
form for a doubling stem, or vice versa. That is a second removal pass and it is the
riskiest edit in the project, so it is confined to singular oblique cells, it never
empties a cell, and every removal is logged.

  data/derived/nouns_grid_nannul.tsv   relabelled + pruned grid
  data/derived/nannul_relabel.log
"""
import sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import derive_nouns as D

SRC = ROOT / "data/derived/nouns_grid_arden.tsv"
OUT = ROOT / "data/derived/nouns_grid_nannul.tsv"
LOG = ROOT / "data/derived/nannul_relabel.log"
U, TU, RU = T.encode("உ")[0], T.encode("ட்")[0], T.encode("ற்")[0]

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

def nannul_class(b):
    """-> (label, doubles?) or None if the rule does not apply."""
    if b is None or len(b) < 3 or b[-1] != U or b[-2] not in (TU, RU): return None
    if len(b) >= 4 and b[-3] == b[-2]: return None          # already geminate
    prev = b[-3]
    if T.is_mey(prev): return ("NCLUST", False)             # Naṉṉūl 181
    if T.is_nedil(prev): return ("NDBLT" if b[-2] == TU else "NDBLR", True)
    if sum(1 for x in b if T.is_uyir(x)) > 2:
        return ("NDBLT" if b[-2] == TU else "NDBLR", True)  # உயிர்த்தொடர்
    return ("NMURRI", False)                                # முற்றியலுகரம்

def main():
    log = []; relab = collections.Counter(); removed = 0; kept_empty = 0
    out = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) != 4: continue
        stem, cls, feat, surfs = p[0], p[1], p[2], p[3].split("|")
        b = enc(stem); nc = nannul_class(b)
        if nc is None:
            out.append(line); continue
        label, doubles = nc
        if label != cls: relab[(cls, label)] += 1
        cls = label

        # prune oblique surfaces that contradict the verdict
        if D.form(feat) == "obl" and "+pl" not in feat:
            dbl = b[:-1] + bytes([b[-2]])
            keep = []
            for s in surfs:
                ub = enc(s)
                if ub is None: keep.append(s); continue
                is_dbl = ub[:len(dbl)] == dbl
                if doubles and not is_dbl and ub[:len(b)-1] == b[:-1]:
                    log.append(f"-\t{stem}\t{feat}\t{s}\t(Naṉṉūl 182: must double)"); removed += 1
                elif (not doubles) and is_dbl:
                    log.append(f"-\t{stem}\t{feat}\t{s}\t(Naṉṉūl 181: must not double)"); removed += 1
                else:
                    keep.append(s)
            if not keep: keep = surfs; kept_empty += 1
            surfs = keep
        out.append("\t".join([stem, cls, feat, "|".join(sorted(set(surfs)))]))

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"cells written        : {len(out):,} -> {OUT.relative_to(ROOT)}")
    print(f"surfaces removed     : {removed:,}")
    print(f"cells rescued (empty): {kept_empty:,}")
    print("\nrelabelling (cells):")
    for (a, bl), n in relab.most_common():
        print(f"  {a:<12} -> {bl:<8} {n:>7,}")

if __name__ == "__main__":
    main()
