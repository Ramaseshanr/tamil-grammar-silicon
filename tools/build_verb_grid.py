#!/usr/bin/env python3
"""
Generate the full verb paradigm over every root in the lexicon.

audit/VERB_AUDIT.md's fix reached only 34% of corpus -கின்றனர் tokens, and 14% of the
shortfall was not a lexicon gap but an artefact: verbs_gold.tsv derives from
ThamizhiMorph's *sample* output (Generated-Verbs/), not from the full FST language, so
most cells were never there to correct. This regenerates them.

    root -> class          from ThamizhiVerbs-*.lexc
    class -> feature cells from each LEXICON C<n>Vinf block
    (root + features)      generated through that class's FST model

Output has the same shape as the noun grid, so the same machinery applies:

    root  class  features  surf1|surf2

  data/derived/verbs_grid.tsv

Every precondition is checked through tools/buildcheck.py and the grid is written to a
temporary file that is only moved into place once they all pass. Two of the five verb
coverage gains in audit/STEM_ALTERNATION.md were silent failures of this build, not Tamil:
a missing .fst and a mis-picked cell list, each of which made a whole class vanish while
the run exited 0. Nothing here is allowed to exit 0 with a class missing again.
"""
import re, os, sys, glob, pathlib, collections

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildcheck as B

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = pathlib.Path(os.environ.get("TAMILOS_LEXC", str(ROOT / "data/gold/thamizhi-morph/foma/src")))
FST  = pathlib.Path(os.environ.get("TAMILOS_FST", str(ROOT / "data/gold/thamizhi-morph/FST-Models")))
OUT  = ROOT / os.environ.get("TAMILOS_VGRID", "data/derived/verbs_grid.tsv")

# which compiled model holds which class (FST-Models/ReadMe.md)
DEDICATED = {"C3": "verb-c3.fst", "C4": "verb-c4.fst", "C62": "verb-c62.fst",
             "C11": "verb-c11.fst", "C12": "verb-c12.fst"}
REST = "verb-c-rest.fst"

# A grid far below the known size means a stage no-oped. Overwriting a good grid with a
# truncated one is how a silent failure becomes a permanent one.
FLOOR = int(os.environ.get("TAMILOS_GRID_FLOOR", "1200000"))


def parse():
    roots = collections.defaultdict(list)     # class -> [root]
    cells = {}                                # class -> [feature string]
    files = sorted(glob.glob(str(SRC / "ThamizhiVerbs-*.lexc")))
    if not files:
        B.record("LEXC", f"no ThamizhiVerbs-*.lexc under {SRC}",
                 "set TAMILOS_LEXC to the foma/src directory")
    for f in files:
        txt = pathlib.Path(f).read_text(encoding="utf-8")
        for m in re.finditer(r'^(\S+)\s+(C[0-9A-Za-z]+)Vinf\s*;', txt, re.M):
            roots[m.group(2)].append(m.group(1))
        for m in re.finditer(r'^LEXICON (C[0-9A-Za-z]+)Vinf\s*$(.*?)(?=^LEXICON |\Z)',
                             txt, re.M | re.S):
            cls, body = m.group(1), m.group(2)
            feats = [x.replace("%", "") for x in re.findall(r'^(\+verb\S*?):', body, re.M)]
            # UNION, not setdefault. C6Vinf is declared THREE times with three
            # different past markers -- க் in ThamizhiVerbs-C62.lexc, ட் and ற் in
            # the otherthan file. Taking the first block by glob order locked in க்,
            # so every C6 root generated ZERO past cells: காணப்பட்டது (1,649 tokens)
            # was absent although the FST generates it correctly. The FST decides
            # which marker a given root accepts, so offering all of them is right.
            if feats:
                # Dedup against what is already there AND within this block: a LEXICON
                # block can list the same feature string twice, and `seen` computed once
                # before extend() let those through -- 2 per class in C6/C7/C8/C9/
                # CPadu61/CPeru63, which wrote 19,559 duplicate grid rows.
                have = cells.setdefault(cls, [])
                seen = set(have)
                for x in feats:
                    if x not in seen:
                        seen.add(x)
                        have.append(x)

    # The gold declares 332 roots TWICE -- 306 in the otherthan file, 20 in C11, 2 in C4,
    # plus the ClassPannu ones (பகர்க்கப்பண்ணு at lines 27217 and 30297, identically).
    # Appending each occurrence wrote every one of those roots' cells twice: 64,467
    # duplicate rows, 5.0% of the grid. Coverage was never affected -- it is measured
    # against a SET of surfaces -- but every "cells" count was inflated by 5%.
    # A root declared twice is one root. See audit/FOMA.md.
    dupes = 0
    for cls, rs in roots.items():
        seen, uniq = set(), []
        for r in rs:
            if r in seen:
                dupes += 1
                continue
            seen.add(r)
            uniq.append(r)
        roots[cls] = uniq
    if dupes:
        print(f"  collapsed {dupes} duplicate root declaration(s) in the gold lexc")
    return roots, cells

def main():
    # ---- preconditions, before a single cell is generated
    B.need("flookup")
    B.check_map(DEDICATED, REST)
    roots, cells = parse()
    B.check_cells(roots, cells)
    # EVERY verb model, not only the ones DEDICATED selects. C6 is the reason: its roots
    # are split across two lexc files, so seven of them are compiled into verb-c62.fst
    # and are not in verb-c-rest.fst at all. A root's cells can live in a model its class
    # does not name, so all six must be available to fall back on.
    B.require_models(FST, sorted(B.VERB_MODELS))
    B.report("preflight")

    allroots = sum(len(v) for v in roots.values())
    print(f"models     : {FST}")
    print(f"classes with roots : {len(roots)}   roots: {allroots:,}")
    print(f"classes with cells : {len(cells)}")

    # write to a temp file; a failed run must not replace a good grid
    tmp = OUT.with_suffix(OUT.suffix + ".part")
    fh = open(tmp, "w", encoding="utf-8")
    grand = surfaces = 0
    for cls in sorted(roots, key=lambda c: -len(roots[c])):
        feats = cells.get(cls)
        if not feats:
            continue                      # already recorded by check_cells as NO CELLS
        model = DEDICATED.get(cls, REST)
        items = [r + f for r in roots[cls] for f in feats]
        got = B.flookup(FST, model, items)
        # a class may also be accepted by the rest-model; try it as a fallback. The
        # fallback used to be silent, which let a missing dedicated model look like a
        # class the rest-model simply did not know -- say how much it rescued.
        note = ""
        if len(got) < len(items) * 0.5 and model != REST:
            before = len(got)
            got2 = B.flookup(FST, REST, [x for x in items if x not in got])
            for k, v in got2.items(): got[k] |= v
            note = f"  [fallback {REST} rescued {len(got)-before:,}]"
        # Any root that produced NOTHING is offered to every other model. ThamizhiMorph
        # splits a class across lexc files -- C6's 31 original roots are 24 in the
        # otherthan file and 7 in ThamizhiVerbs-C62.lexc -- so those 7 compile only into
        # verb-c62.fst while C6 is routed to verb-c-rest.fst. நெகு, இகு, தொகு and நகு
        # generated zero cells for exactly this reason, and no per-class check could see
        # it: C6 as a whole looked healthy on 91 of its 95 roots.
        for m in sorted(B.VERB_MODELS):
            if m in (model, REST):
                continue
            zero = [r for r in roots[cls] if not any((r + f) in got for f in feats)]
            if not zero:
                break
            rescued = B.flookup(FST, m, [r + f for r in zero for f in feats])
            if rescued:
                for k, v in rescued.items(): got[k] |= v
                note += f"  [{m} rescued {len(rescued):,} for {len(zero)} root(s)]"
        n = 0
        produced = set()
        for r in roots[cls]:
            for f in feats:
                key = r + f
                if key in got:
                    fh.write(f"{r}\t{cls}\t{f}\t{'|'.join(sorted(got[key]))}\n")
                    n += 1; surfaces += len(got[key]); produced.add(f)
        grand += n
        B.check_class(cls, feats, produced)
        B.check_roots(cls, roots[cls], got, feats)
        print(f"  {cls:<10} roots={len(roots[cls]):>5}  cells={len(feats):>4}  "
              f"generated={n:>8,}  ({model}){note}", flush=True)
    fh.close()

    B.check_total(grand, FLOOR)
    B.report(B.rel(OUT))      # raises -> tmp is left, OUT untouched
    tmp.replace(OUT)
    print(f"\ngrid cells : {grand:,}")
    print(f"surfaces   : {surfaces:,}")
    print(f"written    : {B.rel(OUT)}")

if __name__ == "__main__":
    try:
        main()
    except B.BuildError as e:
        print(f"\nBUILD FAILED\n{e}", file=sys.stderr)
        sys.exit(2)
