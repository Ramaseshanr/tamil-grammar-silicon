#!/usr/bin/env python3
"""
Can the grammar's consonant classes be tested by a codepoint range?

This is the measurement that positions TLP1 against its closest prior art. Indic NLP
tooling (e.g. Kunchukuttan's `indicnlp/langinfo.py`) derives phonetic class predicates by
comparing a character's offset within its Unicode script block against a range -- which
works because Brahmi block orderings are phonetically meaningful. That observation is prior
art and is credited as such.

It does not transfer to Tamil's இனம் classes. The traditional Tamil order pairs each
plosive with its homorganic nasal (க ங, ச ஞ, ட ண, த ந, ப ம), so வல்லினம் and மெல்லினம்
interleave, and ற் sits inside the இடையினம் run. No இனம் class is a contiguous range.

    python3 tools/inam_ranges.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tlp1 as T

VAL = "க ச ட த ப ற".split()
MEL = "ங ஞ ண ந ம ன".split()
IDAI = "ய ர ல வ ழ ள".split()
GROUPS = (("வல்லினம்", VAL), ("மெல்லினம்", MEL), ("இடையினம்", IDAI))
LAB = {**{c: "val" for c in VAL}, **{c: "mel" for c in MEL}, **{c: "idai" for c in IDAI}}

def main():
    allc = sorted((ord(c), c) for c in VAL + MEL + IDAI)
    print("  Tamil Unicode consonants in codepoint order, labelled by இனம்")
    print("    " + "  ".join(f"{c}:{LAB[c]}" for _, c in allc))
    print("\n  as a codepoint range test")
    bad = 0
    for name, grp in GROUPS:
        o = sorted(ord(c) for c in grp)
        span = o[-1] - o[0] + 1
        intr = [c for cp, c in allc if o[0] <= cp <= o[-1] and c not in grp]
        ok = span == len(grp)
        bad += not ok
        print(f"    {name:12s} U+{o[0]:04X}..U+{o[-1]:04X}  span {span:2d} for {len(grp)}"
              f"  contiguous: {ok}" + (f"  intruders: {' '.join(intr)}" if intr else ""))
    print("\n  as a TLP1 mask")
    for name, grp in GROUPS:
        b = sorted(T.encode(c + T.PULLI)[0] for c in grp)
        span = b[-1] - b[0] + 1
        print(f"    {name:12s} 0x{b[0]:02X}..0x{b[-1]:02X}  span {span:2d} for {len(grp)}"
              f"  contiguous: {span == len(grp)}"
              f"   (b & 0xF0) == 0x{b[0] & 0xF0:02X}")
    print(f"\n  {bad} of 3 இனம் classes are NOT a contiguous Unicode range; "
          f"all 3 are one TLP1 mask")
    return 0

if __name__ == "__main__":
    sys.exit(main())
