#!/usr/bin/env python3
"""Round-trip TLP1 over the whole staged gold corpus and report every failure."""
import sys, pathlib, collections, unicodedata
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import tlp1

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLD = ROOT / "data/gold"

def check(tokens, label):
    ok = bad = skipped = 0
    reasons = collections.Counter(); samples = collections.defaultdict(list)
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        try:
            if tlp1.decode(tlp1.encode(t)) == unicodedata.normalize("NFC", t):
                ok += 1
            else:
                bad += 1; reasons["round-trip mismatch"] += 1
                if len(samples["round-trip mismatch"]) < 4:
                    samples["round-trip mismatch"].append(
                        (t, tlp1.decode(tlp1.encode(t))))
        except tlp1.TLP1Error as e:
            skipped += 1
            r = str(e).split(" at ")[0]
            reasons[r] += 1
            if len(samples[r]) < 3: samples[r].append((t, ""))
    tot = ok + bad + skipped
    print(f"\n=== {label} ===")
    print(f"  tokens        {tot:,}")
    print(f"  round-trip OK {ok:,}  ({100*ok/max(tot,1):.3f}%)")
    print(f"  MISMATCH      {bad:,}")
    print(f"  non-Tamil     {skipped:,}")
    for r, c in reasons.most_common(6):
        print(f"     {c:>7,}  {r}")
        for a, b in samples[r][:3]:
            print(f"              {a!r}" + (f" -> {b!r}" if b else ""))
    return bad

fails = 0
stems = [l.split("\t")[0] for l in
         (ROOT/"data/derived/noun_stems_classed.tsv").read_text(encoding="utf-8").splitlines() if l]
fails += check(stems, "noun stems (Nouns.lexc)")

verbs = []
for f in sorted((GOLD/"thamizhi-morph/Generated-Verbs").glob("words-*")):
    verbs.extend(f.read_text(encoding="utf-8").splitlines())
fails += check(verbs, "generated verb forms")

ud = []
for f in list((GOLD/"UD_Tamil-TTB").glob("*.conllu")) + list((GOLD/"UD_Tamil-MWTT").glob("*.conllu")):
    for line in f.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            p = line.split("\t")
            if len(p) > 1: ud.append(p[1])
fails += check(ud, "UD treebank tokens (real running text)")

print(f"\n{'='*54}\nTOTAL ROUND-TRIP MISMATCHES: {fails:,}")
