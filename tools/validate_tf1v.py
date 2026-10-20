#!/usr/bin/env python3
"""
Validate the TF1 verb codec against the whole verb grid, and freeze the bundle table.

    python3 tools/validate_tf1v.py            # check; fails if the grid disagrees with the table
    python3 tools/validate_tf1v.py --write    # (re)write spec/tf1v_bundles.tsv

Checked:
  1. every distinct feature string in verbs_grid_final.tsv encodes and passes check();
  2. EXACT round trip of the features: decode_features(encode(s)) equals the source string
     with its exponents stripped, character for character. This is stronger than the noun side,
     which could only round-trip atom sets, because the verb strings obey one global atom order;
  3. the global order is real: topological sort is acyclic and ATOM_ORDER is a linear extension;
  4. no information is lost or merged: distinct registers == distinct atom sets;
  5. every ROW is covered;
  6. the frozen table matches the grid, and dense/bundle_of/reg_of are mutually inverse, with
     bundle_of(dense(s)) == s exactly, exponents included;
  7. every invariant in check() actually holds on the data it was derived from (they are
     asserted, not assumed -- an earlier draft assumed 'tense iff finite' and was wrong);
  8. the guards fire;
  9. agreement behaves on SYNTHETIC subjects, labelled as such.
"""
import sys, csv, collections, itertools, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tf1 as N
import tf1v as V

GRID = ROOT / "data/derived/verbs_grid_final.tsv"
TABLE = ROOT / "spec/tf1v_bundles.tsv"
m = N._m

class Fail(Exception): pass
def need(c, msg):
    if not c: raise Fail(msg)

def main(write):
    rows = collections.Counter(); pairs = set(); total = 0
    with open(GRID, encoding="utf-8") as f:
        for line in f:
            q = line.split("\t", 4)
            if len(q) < 3: continue
            total += 1; rows[q[2]] += 1; pairs.add((q[1], q[2]))
    print(f"  grid: {total:,} rows   {len(rows)} distinct feature strings   "
          f"{len(pairs):,} (class, string) pairs")

    # 3  the global order
    seqs = {s: [a for a, _ in V.parse(s)] for s in rows}
    atoms = sorted({a for q in seqs.values() for a in q} | {"verb"})
    after = collections.defaultdict(set)
    for q in seqs.values():
        q = ["verb"] + q
        for i in range(len(q)):
            for b in q[i + 1:]: after[q[i]].add(b)
    contra = [(a, b) for a in atoms for b in after[a] if a in after[b]]
    need(not contra, f"atoms appear in both orders: {contra[:3]}")
    need(set(V.ATOM_ORDER) == set(atoms), "ATOM_ORDER does not list exactly the atoms in the grid")
    pos = {a: i for i, a in enumerate(V.ATOM_ORDER)}
    need(all([pos[a] for a in ["verb"] + q] == sorted(pos[a] for a in ["verb"] + q)
             for q in seqs.values()), "a source string violates ATOM_ORDER")
    print(f"  [3]   {len(atoms)} atoms, no pair in both orders, ATOM_ORDER respected by all "
          f"{len(rows)} strings")

    # 1, 2, 4
    reg_of, by_reg = {}, collections.defaultdict(list)
    for s in rows:
        r = V.encode(s)
        need(V.is_valid(r), f"invalid register for {s}")
        need(V.decode_features(r) == V.strip_exponents(s),
             f"features do not round-trip exactly: {s} -> {V.decode_features(r)}")
        reg_of[s] = r; by_reg[r].append(s)
    print(f"  [1,2] all {len(rows)} strings encode, validate, and round-trip EXACTLY as features")
    sets = {frozenset(["verb"] + [a for a, _ in V.parse(s)]) for s in rows}
    need(len(by_reg) == len(sets),
         f"registers {len(by_reg)} != atom sets {len(sets)}: a distinction was lost or merged")
    print(f"  [4]   {len(rows)} strings -> {len(by_reg)} registers == {len(sets)} atom sets; "
          f"up to {max(len(v) for v in by_reg.values())} exponent combinations share a register")

    # 5
    need(sum(rows[s] for s in reg_of) == total, "rows not covered")
    print(f"  [5]   rows covered: {total:,} / {total:,}")

    # 6  the frozen table
    order = sorted(rows, key=lambda s: (reg_of[s], s))
    new = [(i, N.to_hex(reg_of[s]), s, rows[s]) for i, s in enumerate(order)]
    if write:
        with open(TABLE, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t"); w.writerow(["code", "reg", "bundle", "rows"])
            w.writerows(new)
        print(f"  [6]   wrote {TABLE.relative_to(ROOT)}  ({len(new)} bundles, codes 0..{len(new)-1})")
    else:
        need(TABLE.exists(), "spec/tf1v_bundles.tsv missing; run with --write")
        old = list(csv.DictReader(TABLE.open(encoding="utf-8"), delimiter="\t"))
        need([(int(r["reg"], 16), r["bundle"]) for r in old] ==
             [(int(h, 16), s) for _, h, s, _ in new],
             "the frozen table no longer matches the grid; the ROM address field would drift")
        print(f"  [6]   frozen table matches the grid ({len(old)} bundles)")
    need(V.universe_size() == len(rows), "dense table size != string count")
    for s in rows:
        c = V.dense(s)
        need(V.bundle_of(c) == s and V.reg_of(c) == reg_of[s], f"dense not inverse for {s}")
    bits = (len(rows) - 1).bit_length()
    print(f"        bundle_of(dense(s)) == s for all, exponents included; code fits {bits} bits;\n"
          f"        ROM address = {{class[4:0], code[{bits-1}:0]}} = {5 + bits} bits; "
          f"{len(pairs):,} of {20 * len(rows):,} addresses populated")

    # 7  the invariants hold on the data
    stat = collections.Counter()
    for r in by_reg:
        stat["fin_no_tense"] += bool(r & m(V.FIN)) and not r & V.TENSE_MASK
        stat["nonfin_tense"] += bool(r & m(V.NONFIN)) and bool(r & V.TENSE_MASK)
        stat["fin_no_png"] += bool(r & m(V.FIN)) and not r & V.PNG_MASK
        stat["sandhi_on_fin"] += bool(r & V.SANDHI_MASK) and bool(r & m(V.FIN))
    print(f"  [7]   invariants hold on all {len(by_reg)} registers. What the data does NOT enforce:\n"
          f"          finite forms with no tense        : {stat['fin_no_tense']}  (imperative, optative, மார்)\n"
          f"          non-finite forms WITH a tense     : {stat['nonfin_tense']}  (tensed participles)\n"
          f"          finite forms with no PNG slot     : {stat['fin_no_png']}  (optative; negative imperative)\n"
          f"          sandhi flag on a finite form      : {stat['sandhi_on_fin']}")
    need(stat["sandhi_on_fin"] == 0, "sandhi on a finite form: the claim in the spec is wrong")

    # 8  the guards
    base = V.encode("+verb+fin+sim+past=ட்+3sgm=அன்")
    g = [("unknown atom",        lambda: V.encode("+verb+fin+sim+bogus")),
         ("repeated atom",       lambda: V.encode("+verb+fin+fin+sim")),
         ("not a verb bundle",   lambda: V.encode("noun+nom")),
         ("noun case bit",       lambda: V.check(base | m(N.NOM))),
         ("reserved plane 3",    lambda: V.check(base | m(100))),
         ("FIN and NONFIN",      lambda: V.check(base | m(V.NONFIN))),
         ("SIM and COMPLEX",     lambda: V.check(base | m(V.COMPLEX))),
         ("PASSIVE alone",       lambda: V.check(base | m(V.PASSIVE))),
         ("two tenses",          lambda: V.check(base | m(V.PRES))),
         ("two PNG slots",       lambda: V.check(base | m(48))),
         ("PNG on NONFIN",       lambda: V.check((base & ~m(V.FIN)) | m(V.NONFIN))),
         ("wrong பால்",          lambda: V.check((base & ~m(N.AAN)) | m(N.PEN))),
         ("agreement w/o PNG",   lambda: V.check(V.encode("+verb+fin+sim+imp=∅+neg=ஆத்+euph=ஏ") | m(N.TANMAI))),
         ("ANY without OPT",     lambda: V.check(base | m(N.ANY))),
         ("ANY dropped from OPT",lambda: V.check(V.encode("+verb+fin+sim+opt=க") & ~m(N.ANY))),
         ("hyphen w/o sandhi",   lambda: V.check(base | m(V.SANDHI_HYPHEN))),
         ("two sandhi",          lambda: V.check(V.encode("+verb+nonfin+sim+vpart=உ+sandhic=ச்") | m(V.SANDHI_K))),
         ("a noun register",     lambda: V.check(N.encode("noun+nom")))]
    for name, fn in g:
        try: fn()
        except N.TF1Error: continue
        raise Fail(f"guard did not fire: {name}")
    print(f"  [8]   {len(g)}/{len(g)} guards fire")

    # 9  agreement, on SYNTHETIC subjects: no noun has plane-1 data
    def subj(*bits): return m(*bits)
    s3m = subj(N.PADARKKAI, N.UYAR, N.AAN, N.SG)
    v = lambda s: V.encode(s)
    tests = [
      ("3sgm verb, 3rd masc sg subject",  V.agrees(s3m, v("+verb+fin+sim+past=ட்+3sgm=அன்")), True),
      ("3sgf verb, 3rd masc sg subject",  V.agrees(s3m, v("+verb+fin+sim+past=ட்+3sgf=அள்")), False),
      ("3pln verb, 3rd masc sg subject",  V.agrees(s3m, v("+verb+fin+sim+past=ட்+3pln=அன")), False),
      ("1sg verb, 3rd person subject",    V.agrees(s3m, v("+verb+fin+sim+past=ட்+1sg=ஏன்")), False),
      ("1sg verb, 1st sg subject",        V.agrees(subj(N.TANMAI, N.SG), v("+verb+fin+sim+past=ட்+1sg=ஏன்")), True),
      ("3sghe verb: HON not required",    V.agrees(subj(N.PADARKKAI, N.UYAR, N.PALAR, N.SG),
                                                    v("+verb+fin+sim+past=ட்+3sghe=ஆர்")), True),
      ("optative agrees with anything",   V.agrees(s3m, v("+verb+fin+sim+opt=க")), True),
      ("optative, even the empty subject",V.agrees(0, v("+verb+fin+sim+opt=க")), True),
    ]
    for name, got, want in tests:
        need(got == want, f"agreement wrong: {name}: got {got}")
    try: V.agrees(s3m, v("+verb+nonfin+sim+vpart=உ")); raise Fail("participle did not raise")
    except V.TF1VError: pass
    print(f"  [9]   {len(tests)} agreement cases correct on SYNTHETIC subjects; a participle raises")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main("--write" in sys.argv))
    except (Fail, N.TF1Error) as e:
        print(f"\nTF1 VERB VALIDATION FAILED\n  {e}", file=sys.stderr); sys.exit(2)
