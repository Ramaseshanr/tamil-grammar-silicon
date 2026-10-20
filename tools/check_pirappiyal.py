#!/usr/bin/env python3
"""
Does the TLP1 place field reproduce Tolkāppiyam's பிறப்பியல்?

The claim behind the encoding is that bits 2-0 hold place of articulation in the order the
grammar gives. Tolkāppiyam states it one pair at a time, each nūṟpā naming a stop, its
nasal, and the articulator they share. If the encoding is right, each of those pairs must
come out with identical place bits, and no two pairs may share a place.

    python3 tools/check_pirappiyal.py
"""
import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

# nūṟpā number -> (வல்லினம், மெல்லினம், the articulator it names)
PAIRS = [(7,  "க", "ங", "முதல் நா அண்ணம்    root of the tongue, palate"),
         (8,  "ச", "ஞ", "இடை நா அண்ணம்      middle of the tongue, palate"),
         (9,  "ட", "ண", "நுனி நா அண்ணம்     tip of the tongue, palate"),
         (11, "த", "ந", "நா நுனி … பல் முதல் tongue tip spread, at the teeth"),
         (15, "ப", "ம", "இதழ் இயைந்து        the lips meeting"),
         (12, "ற", "ன", "அணரி நுனி நா அண்ணம் curled tongue tip, palate")]

def main():
    doc = json.loads((ROOT / "data/gold/tolkappiyam/pirappiyal.json")
                     .read_text(encoding="utf-8"))
    byn = {v["n"]: " / ".join(v["lines"]) for v in doc["nurpa"]}
    print(f"  {doc['work']} · {doc['atikaram']} · {doc['iyal']} "
          f"({doc['count']} nūṟpā)\n")
    seen, bad = {}, 0
    for n, hard, soft, gloss in PAIRS:
        verse = byn.get(n, "")
        hb, sb = T.encode(hard + T.PULLI)[0], T.encode(soft + T.PULLI)[0]
        ph, ps = T.place(hb), T.place(sb)
        named = hard in verse and soft in verse
        ok = (ph == ps) and named and ph not in seen
        seen[ph] = (hard, soft)
        bad += not ok
        print(f"  {n:3d}  {hard}் 0x{hb:02X}  {soft}் 0x{sb:02X}   place {ph}"
              f"{'' if ph == ps else ' != ' + str(ps)}"
              f"   {'OK' if ok else '** '}   {gloss}")
        if not named:
            print(f"       !! the nūṟpā does not name both letters: {verse[:60]}")
    print(f"\n  distinct places used : {len(seen)} of 6")
    print(f"  pairs verified       : {len(PAIRS) - bad} / {len(PAIRS)}")
    if bad == 0 and len(seen) == 6:
        print("\n  ok: every pair Tolkāppiyam names shares one place in TLP1, and the six\n"
              "      pairs occupy the six place values exactly once each.")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
