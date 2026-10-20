#!/usr/bin/env python3
"""
Build the register-tagged gold.

audit/LPLURAL.md ended at a scope decision: Naṉṉūl 226 licenses BOTH கல்கள் and கற்கள்
(அல்வழி உறழ்வு), but applying that wholesale produces அகக்கடற்களுக்கு -- classical, and
not the Tamil anyone writes now. Option 3 was chosen: carry both, tagged by register.

Format: a fifth column of tags, pipe-aligned with the surfaces.

    stem  class  features  surf1|surf2  B|C

    B  valid in BOTH registers -- the default
    C  CLASSICAL only: a Naṉṉūl 226 உறழ்வு alternant that ThamizhiMorph does not license

Only one rule applied in this project is classical-and-not-modern: 226's alternation.
Everything else -- Arden §110/§145/§129/§134 and Naṉṉūl 181-182 -- produces forms that
are standard modern Tamil (வயிற்றில், மொழிக்கு, விற்களை), so they stay B.

⚠️ Known imprecision, recorded rather than hidden: the உறழ்வு alternants in the ள்
direction (தோள்கள் beside தோட்கள்) are tagged C although modern Tamil uses them too.
Separating those needs frequency evidence from a modern corpus, which this project does
not yet have. C therefore means "classically licensed, not attested in our modern source",
not "archaic".

  data/derived/nouns_grid_tagged.tsv
"""
import sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

BASE = ROOT / "data/derived/nouns_grid_nannul.tsv"     # every surface here is B
OUT  = ROOT / "data/derived/nouns_grid_tagged.tsv"
L, LL = T.encode("ல்")[0], T.encode("ள்")[0]
R, TT = T.encode("ற்")[0], T.encode("ட்")[0]
MUT = {L: R, LL: TT}

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

def main():
    out = []; nC = 0; nB = 0
    for line in BASE.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) != 4: continue
        stem, cls, feat, surfs = p[0], p[1], p[2], p[3].split("|")
        tags = {s: "B" for s in surfs}
        b = enc(stem)
        if b and b[-1] in MUT and "+pl" in feat:
            alt = b[:-1] + bytes([MUT[b[-1]]])
            for s in list(surfs):
                u = enc(s)
                if not u: continue
                if u[:len(b)] == b:                       # plain -> classical mutated
                    cand = T.decode(alt + u[len(b):])
                elif u[:len(alt)] == alt:                 # mutated -> classical plain
                    cand = T.decode(b + u[len(alt):])
                else:
                    continue
                if cand not in tags:
                    tags[cand] = "C"; nC += 1
        nB += sum(1 for v in tags.values() if v == "B")
        ordered = sorted(tags)
        out.append("\t".join([stem, cls, feat,
                              "|".join(ordered),
                              "|".join(tags[s] for s in ordered)]))
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"cells written : {len(out):,} -> {OUT.relative_to(ROOT)}")
    print(f"  B (both registers)  : {nB:,}")
    print(f"  C (classical only)  : {nC:,}")

if __name__ == "__main__":
    main()
