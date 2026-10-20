#!/usr/bin/env python3
"""
Validate the TF1 noun codec against the whole noun grid, and freeze the bundle table.

    python3 tools/validate_tf1.py            # check; fails if the grid disagrees with the table
    python3 tools/validate_tf1.py --write    # (re)write spec/tf1_bundles.tsv

What is checked:
  1. every distinct bundle in nouns_grid_final.tsv encodes, is valid, and decodes to the
     same ATOM SET (the string is canonicalised, so equality is on sets, not text);
  2. encode(decode(r)) == r for every register;
  3. every ROW of the grid is covered, counted;
  4. the one set-level collision is harmless: (class, bundle) -> (class, register) must be
     injective, i.e. no declension class holds both orderings;
  5. the frozen table matches the grid, so the ROM address field cannot drift silently;
  6. the guards fire: unknown atom, reserved bit, two cases, BEN without DAT, SG+PL.
"""
import sys, csv, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tf1 as F

GRID = ROOT / "data/derived/nouns_grid_final.tsv"
TABLE = ROOT / "spec/tf1_bundles.tsv"

class Fail(Exception): pass

def need(cond, msg):
    if not cond: raise Fail(msg)

def main(write):
    rows = collections.Counter(); pairs = set(); total = 0
    with open(GRID, encoding="utf-8") as f:
        for line in f:
            q = line.split("\t", 3)
            if len(q) < 3: continue
            total += 1; rows[q[2]] += 1; pairs.add((q[1], q[2]))
    print(f"  grid: {total:,} rows   {len(rows)} distinct bundle strings   "
          f"{len(pairs)} (class, bundle) pairs")

    # 1, 2
    reg_of, by_reg = {}, collections.defaultdict(list)
    for b in rows:
        r = F.encode(b)
        need(F.is_valid(r), f"invalid register for {b}")
        need(set(F.atoms(F.decode(r))) == set(F.atoms(b)), f"atom set changed: {b}")
        need(F.encode(F.decode(r)) == r, f"decode/encode not idempotent: {b}")
        reg_of[b] = r; by_reg[r].append(b)
    print(f"  [1,2] all {len(rows)} bundles encode, validate, and round-trip as atom sets")

    # 3
    covered = sum(rows[b] for b in reg_of)
    need(covered == total, f"{total - covered} rows not covered")
    print(f"  [3]   rows covered: {covered:,} / {total:,}")

    # 4
    coll = {r: bs for r, bs in by_reg.items() if len(bs) > 1}
    for r, bs in coll.items():
        print(f"        set-level collision: {sorted(bs)} -> {F.to_hex(r)}")
    keyed = {(c, reg_of[b]) for c, b in pairs}
    need(len(keyed) == len(pairs),
         f"(class, register) is NOT injective: {len(pairs)} pairs -> {len(keyed)}")
    print(f"  [4]   (class, bundle) -> (class, register) is injective: "
          f"{len(pairs)} -> {len(keyed)}; the collision is harmless")

    # 5, table
    table = sorted(by_reg)
    new = [(i, F.to_hex(r), F.decode(r), "|".join(sorted(by_reg[r])),
            sum(rows[b] for b in by_reg[r])) for i, r in enumerate(table)]
    if write:
        with open(TABLE, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["code", "reg", "canonical", "source_strings", "rows"])
            for i, h, c, s, n in new: w.writerow([i, h, c, s, n])
        print(f"  [5]   wrote {TABLE.relative_to(ROOT)}  ({len(new)} registers, "
              f"dense codes 0..{len(new)-1})")
    else:
        need(TABLE.exists(), "spec/tf1_bundles.tsv missing; run with --write")
        old = list(csv.DictReader(TABLE.open(encoding="utf-8"), delimiter="\t"))
        need([(int(r["reg"], 16), r["canonical"]) for r in old] ==
             [(int(h, 16), c) for _, h, c, _, _ in new],
             "the frozen table no longer matches the grid -- the ROM address field would drift")
        print(f"  [5]   frozen table matches the grid ({len(old)} registers)")
    need(F.universe_size() == len(by_reg), "dense table size differs from the register count")
    for r in table:
        need(F.from_dense(F.dense(r)) == r, "dense/from_dense not inverse")
    bits = (len(by_reg) - 1).bit_length()
    print(f"        dense code fits {bits} bits; ROM address = {{class[4:0], code[{bits-1}:0]}} "
          f"= {5 + bits} bits")

    # 6
    cases = [("unknown atom",      lambda: F.encode("noun+nom+bogus")),
             ("repeated atom",     lambda: F.encode("noun+nom+nom")),
             ("not a noun bundle", lambda: F.encode("verb+nom")),
             ("reserved bit",      lambda: F.check(F.encode("noun+nom") | (1 << 40))),
             ("VOC is reserved",   lambda: F.check(F.encode("noun+nom") | (1 << F.VOC))),
             ("SG and PL",         lambda: F.check((1 << F.SG) | (1 << F.PL))),
             ("two cases",         lambda: F.check((1 << F.SG) | (1 << F.NOM) | (1 << F.ACC))),
             ("BEN without DAT",   lambda: F.encode("noun+acc+ben")),
             ("two sandhi",        lambda: F.encode("noun+nom+sandhik+sandhic"))]
    for name, fn in cases:
        try: fn()
        except F.TF1Error: continue
        raise Fail(f"guard did not fire: {name}")
    print(f"  [6]   {len(cases)}/{len(cases)} guards fire")

    # matching, the software twin of the AND gates
    a, b, c = F.encode("noun+pl+loc"), F.encode("noun+pl+acc"), F.encode("noun+loc")
    need(F.same_number(a, b) and not F.same_number(a, c), "same_number wrong")
    need(F.same_case(a, c) and not F.same_case(a, b), "same_case wrong")
    need(not F.same_case(F.encode("noun+foc"), F.encode("noun+foc")),
         "an absent case field must never match")
    print("        same_number / same_case behave, and an absent field never matches")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main("--write" in sys.argv))
    except (Fail, F.TF1Error) as e:
        print(f"\nTF1 VALIDATION FAILED\n  {e}", file=sys.stderr); sys.exit(2)
