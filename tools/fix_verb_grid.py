#!/usr/bin/env python3
"""
Apply the three audit/VERB_AUDIT.md corrections to the full regenerated verb grid.

Same three rules as tools/fix_anar.py, now over verbs_grid.tsv (1,291,450 cells from
9,275 roots) instead of the 1.86M sample pairs. The grid keeps features and surfaces in
separate columns, so the transformations are cleaner here.

  1  -அர் -> -அனர், for past and LITERARY PRESENT only. The future keeps -அர்
     (வர் 377,188 vs வனர் 2,137), and the இன் past is already correct by haplology.
  2  the doubled euphonic (euph=அன் with a -அன்/-அள் person suffix) is TAGGED CLASSICAL,
     not dropped. It scores 0 in 39M tokens of modern Tamil -- but Naṉṉūl 325 gives
     "அன் ஆன் இறுமொழி ஆண்பால் படர்க்கை" and the Collatikāram paradigm lists நடந்தான்
     AND நடந்தனன்; Vellaivaranar corroborates with உண்டாள் / உண்டனள். Deleting a form
     the nūṟpā licenses because a modern corpus lacks it is the அருட்கள் error --
     absence of evidence is not evidence. See docs/METHOD.md.
  3  causative future வ் -> ப்ப் after the வி causative, in EVERY person-number-gender.
     Scoped to 1pl/2sgh/2pl originally; that left 2,904 surfaces wrong across 363
     இ-final roots (கடிவிவேன் for கடிவிப்பேன்).

Output gains a fifth column of register tags, one per surface, exactly as the noun grid:
B = both registers, C = classical only.

  data/derived/verbs_grid_fixed.tsv
"""
import re, os, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import buildcheck as B

SRC = ROOT / os.environ.get("TAMILOS_VGRID","data/derived/verbs_grid.tsv")
OUT = ROOT / os.environ.get("TAMILOS_VOUT","data/derived/verbs_grid_fixed.tsv")

N, A, R, V, P = (T.encode(x)[0] for x in ("ன்", "அ", "ர்", "வ்", "ப்"))
ANAR, AR = bytes([A, N, A, R]), bytes([A, R])

TENSE = re.compile(r'\+(past|pres)=(\S+?)\+')
SGE   = re.compile(r'\+3sge=அர்$')
EUPH  = re.compile(r'\+euph=அன்\+')
# ALL person-number-gender, not just 1pl/2sgh/2pl. The original audit read the model as
# "getting 1sg/3sgm/3sgf/3sge/3ple right", which is true of most roots -- but NOT of
# இ-final ones. கடி, தணி, அணி, கவி, அரி and 358 others emit வ் after the வி causative in
# every PNG, so the narrow fix left 2,904 surfaces wrong across 363 roots:
# கடிவிவேன் for கடிவிப்பேன். Found by cross-checking Arden's paradigms (audit/ARDEN_OCR).
CAUS  = re.compile(r'caus=வி.*fut=வ்\+([0-9a-z]+)=(\S+)$')

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

def main():
    n_anar = n_euph = n_caus = kept = 0
    with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as o:
        for line in f:
            p = line.rstrip("\n").split("\t")
            # accept 4 or 5 columns. `!= 4` was the guard that silently emptied a grid
            # when a column was added last time -- see audit/BUILD_GUARDS.md.
            if len(p) < 4: continue
            root, cls, feat, surfs = p[0], p[1], p[2], p[3].split("|")

            # Naṉṉūl 325 licenses these; the modern corpus does not have them. Both facts
            # are recorded, which is what the register column is for.
            tag = "C" if EUPH.search(feat) else "B"
            if tag == "C":
                n_euph += 1

            m = CAUS.search(feat)
            if m:
                png = enc(m.group(2)); new = []
                for s in surfs:
                    sb = enc(s)
                    if sb and png and sb[-len(png):] == png and sb[:-len(png)][-1:] == bytes([V]):
                        new.append(T.decode(sb[:-len(png)][:-1] + bytes([P, P]) + png))
                    else:
                        new.append(s)
                if new != surfs: n_caus += 1
                surfs = new

            elif SGE.search(feat):
                tm = TENSE.search(feat)
                mk = enc(tm.group(2)) if tm else None
                if mk and mk[-1] != N:
                    new = []
                    for s in surfs:
                        sb = enc(s)
                        # Skip a surface that ALREADY ends -அனர். C11 implements the
                        # suffix correctly (வசிக்கின்றனர், வசித்தனர்) even though its
                        # tag still reads 3sge=அர்; the ன் comes from the class's own
                        # rules, not the tag. A first version transformed these too and
                        # produced வசித்தனனர் -- 8,852 already-correct cells doubled.
                        if sb and len(sb) >= 4 and sb[-4:] == ANAR:
                            new.append(s)
                        elif sb and sb[-2:] == AR:
                            new.append(T.decode(sb[:-2] + ANAR))
                        else:
                            new.append(s)
                    if new != surfs:
                        n_anar += 1
                        feat = feat.replace("+3sge=அர்", "+3sge=அனர்")
                    surfs = new

            uniq = sorted(set(surfs))
            o.write(f"{root}\t{cls}\t{feat}\t{'|'.join(uniq)}\t"
                    f"{'|'.join([tag] * len(uniq))}\n")
            kept += 1
    print(f"cells written        : {kept:,} -> {B.rel(OUT)}")
    print(f"  -அர் -> -அனர்      : {n_anar:,}")
    print(f"  euph tagged CLASSICAL: {n_euph:,}   [Naṉṉūl 325]")
    print(f"  causative fut fixed  : {n_caus:,}")

if __name__ == "__main__":
    main()
