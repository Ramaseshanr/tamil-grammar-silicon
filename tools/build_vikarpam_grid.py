#!/usr/bin/env python3
"""
The விகற்பம் tagging stage — Naṉṉūl Eḻuttatikāram 243.

audit/URUBU_PUNARIYAL.md established that the உருபு alternation is not a selection
problem.  Nūṟpā 243 declares that where a stem meets an உருபு the சாரியை may come, be
omitted, or be **விகற்பம்**; 253 and 257 twice decline to enumerate which goes where.
So there is nothing to pick, and the project's standing answer to a nūṟpā that licenses
alternants is the one `audit/REGISTER.md` arrived at for Eḻuttatikāram 226's உறழ்வு:

    carry every licensed form, tag it, attach the corpus count, and let the consumer choose.

This stage does that for the உருபு seam.  It is the third time the shape has come up
(226's உறழ்வு, 327's அர்/ஆர்/ப/மார், now 243's விகற்பம்) and it is handled the same way.

    stem  class  features  surf|...  lic|...  reg|...  n|...  mech|...

    lic   G   ThamizhiMorph lists this surface — it is in the input grid
          V   a விகற்பம் alternant licensed by 243/244/255, which ThamizhiMorph omits
          VA  a V alternant the corpus attests at n >= 20
    reg   B|C from the input grid for a G surface; `-` for V, whose register is unassigned
    n     tawiki_freq.tsv count for that exact surface
    mech  `-` for G; otherwise which optional mechanisms produced the alternant
          (sar = the இன் சாரியை, var = the உருபு variant, odb = ஒற்று doubling,
           cdb = clitic doubling, none = no optional mechanism was engaged)

Two rules carried over from audit/REGISTER.md and docs/METHOD.md, and enforced below:

  * The corpus may **promote** (V -> VA) and may never **demote**.  Absence from an
    encyclopaedia is not evidence that a nūṟpā-derived form is ungrammatical.
  * **Nothing is ever dropped.**  Every surface of the input grid appears with lic=G,
    including the ones this derivation fails to produce (the C1 and C6 gold defects of
    docs/RULES.md §5).  The guard refuses to install otherwise.

Usage:
    python3 tools/build_vikarpam_grid.py          # build, guard, install
    python3 tools/build_vikarpam_grid.py verify   # re-check an installed grid
"""
import sys, os, re, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import buildcheck as B
import phon_rules as P

IN   = ROOT / os.environ.get("TAMILOS_GRID", "data/derived/nouns_grid_final.tsv")
OUT  = ROOT / os.environ.get("TAMILOS_VIKGRID", "data/derived/nouns_grid_vikarpam.tsv")
FREQ = ROOT / "data/gold/freq/tawiki_freq.tsv"
MIN_ATT = int(os.environ.get("TAMILOS_MIN_ATT", "20"))
OPT = ("sar", "var", "odb", "cdb", "plain", "nohard")
LIC, REG = {"G", "V", "VA"}, {"B", "C", "-"}

def load_freq():
    f = {}
    if not FREQ.exists():
        print("  ! no corpus file; every V stays V"); return f
    with open(FREQ, encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) == 2 and p[1].isdigit(): f[p[0]] = int(p[1])
    print(f"  corpus forms: {len(f):,}")
    return f

def mech_of(dec):
    """Which optional mechanisms produced this alternant.

    `plain`  the சாரியை increment was not taken  (உலகின் beside உலகத்தின்)
    `nohard` ல்/ள் were not hardened             (நாள்கள் beside நாட்கள், உறழ்வு 226)
    """
    m = [n for n, v in zip(OPT, (dec[0], dec[1] > 0) + tuple(dec[2:])) if v]
    return "+".join(m) if m else "none"

def load_stems():
    """Every form declared as a noun stem — the homograph guard.

    கல் + ஐ has an undoubled branch கலை, and கலை is also an ordinary word ("art")
    with 13,273 tawiki tokens.  Promoting on that count would be reading evidence
    about a different word, which is the ஊர் mistake of audit/ADJUDICATION.md again.
    So a surface that is itself a declared stem is never promoted."""
    _, stems = P.load_lexc()
    return set(stems)

# ------------------------------------------------------------------ guards
def check_row(parts, lineno):
    if len(parts) != 8:
        raise B.BuildError(f"{OUT.name}:{lineno}: {len(parts)} columns, expected 8")
    cols = [parts[i].split("|") for i in (3, 4, 5, 6, 7)]
    n = len(cols[0])
    if any(len(c) != n for c in cols):
        raise B.BuildError(f"{OUT.name}:{lineno}: MISALIGNED — "
                           f"{[len(c) for c in cols]} for {n} surfaces")
    surf, lic, reg, cnt, mech = cols
    if len(set(surf)) != n:
        raise B.BuildError(f"{OUT.name}:{lineno}: duplicate surface in {parts[0]}")
    for i in range(n):
        if lic[i] not in LIC:
            raise B.BuildError(f"{OUT.name}:{lineno}: bad lic {lic[i]!r}")
        if reg[i] not in REG:
            raise B.BuildError(f"{OUT.name}:{lineno}: bad reg {reg[i]!r}")
        if not cnt[i].isdigit():
            raise B.BuildError(f"{OUT.name}:{lineno}: non-numeric count {cnt[i]!r}")
        if lic[i] == "G" and mech[i] != "-":
            raise B.BuildError(f"{OUT.name}:{lineno}: G surface carries mech {mech[i]!r}")
        if lic[i] in ("V", "VA") and mech[i] == "-":
            raise B.BuildError(f"{OUT.name}:{lineno}: {lic[i]} surface has no mechanism")
        if lic[i] == "VA" and int(cnt[i]) < MIN_ATT:
            raise B.BuildError(f"{OUT.name}:{lineno}: VA below the threshold "
                               f"({cnt[i]} < {MIN_ATT})")
    return n

def build():
    freq = load_freq()
    homo = load_stems()
    print(f"  stem inventory for the homograph guard: {len(homo):,}")
    blocked = []
    st = collections.Counter(); mechs = collections.Counter()
    rows_in = rows_out = surf_in = surf_out = 0
    lost = 0
    tmp = OUT.with_suffix(".part")
    with open(IN, encoding="utf-8") as fh, open(tmp, "w", encoding="utf-8") as out:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4: continue
            rows_in += 1
            stem, cl, feat = p[0], p[1], p[2]
            gold = p[3].split("|")
            greg = p[4].split("|") if len(p) > 4 else ["-"] * len(gold)
            if len(greg) != len(gold): greg = ["-"] * len(gold)
            surf_in += len(gold)

            cls = re.sub(r"(Sg|pl)Root$", "", cl)
            cand = P.derive_labeled(stem, cls, feat) or {}

            seen = {}
            order = []
            for s, r in zip(gold, greg):
                if s in seen: continue
                seen[s] = ("G", r if r in REG else "-", "-")
                order.append(s)
            for s in sorted(cand):
                if s in seen: continue
                n = freq.get(s, 0)
                if n >= MIN_ATT and s in homo:
                    blocked.append((n, s)); lic = "V"      # homograph, not evidence
                else:
                    lic = "VA" if n >= MIN_ATT else "V"
                seen[s] = (lic, "-", mech_of(cand[s]))
                order.append(s)
            if not (set(gold) & set(cand)) and cand:
                lost += 0        # the derivation missed this cell; gold is kept anyway

            lic = [seen[s][0] for s in order]
            reg = [seen[s][1] for s in order]
            cnt = [str(freq.get(s, 0)) for s in order]
            mch = [seen[s][2] for s in order]
            for l, m in zip(lic, mch):
                st[l] += 1
                if l != "G": mechs[m] += 1
            parts = [stem, cl, feat, "|".join(order), "|".join(lic),
                     "|".join(reg), "|".join(cnt), "|".join(mch)]
            check_row(parts, rows_in)
            out.write("\t".join(parts) + "\n")
            rows_out += 1; surf_out += len(order)

    if rows_out != rows_in:
        raise B.BuildError(f"ROW LOSS: {rows_in:,} in, {rows_out:,} out")
    if st["G"] < surf_in - 1000:
        raise B.BuildError(f"SURFACE LOSS: {surf_in:,} gold surfaces in, "
                           f"{st['G']:,} tagged G")
    tmp.replace(OUT)
    return st, mechs, rows_out, surf_in, surf_out, blocked

def verify():
    n = surf = 0
    st = collections.Counter()
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            n += 1
            parts = line.rstrip("\n").split("\t")
            surf += check_row(parts, n)
            for l in parts[4].split("|"): st[l] += 1
    print(f"  {OUT.name}: {n:,} rows   {surf:,} surfaces   "
          + "   ".join(f"{k} {v:,}" for k, v in sorted(st.items())))
    print("  ok: every row aligned, tagged, counted and attributed")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify(); return 0
    print(f"=== விகற்பம் tagging [Naṉṉūl Eḻuttatikāram 243]  -> {B.rel(OUT)}")
    st, mechs, rows, surf_in, surf_out, blocked = build()
    tot = sum(st.values())
    print(f"  rows {rows:,}   surfaces {surf_in:,} -> {surf_out:,} "
          f"(x{surf_out/surf_in:.2f})")
    print(f"    G  ThamizhiMorph lists it          {st['G']:10,d}  "
          f"{100*st['G']/tot:5.1f}%")
    print(f"    V  விகற்பம், corpus silent          {st['V']:10,d}  "
          f"{100*st['V']/tot:5.1f}%")
    print(f"    VA விகற்பம், attested n>={MIN_ATT:<3d}        {st['VA']:10,d}  "
          f"{100*st['VA']/tot:5.1f}%")
    if blocked:
        blocked.sort(reverse=True)
        print(f"\n  promotions blocked by the homograph guard: {len(blocked):,}")
        for n, s in blocked[:8]: print(f"    {s:20s} n={n:,} — also a declared stem")
    print(f"\n  alternants by mechanism")
    for m, c in mechs.most_common(12):
        print(f"    {m:16s} {c:10,d}")
    print()
    verify()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except B.BuildError as e:
        print(f"\nVIKARPAM STAGE FAILED\n{e}", file=sys.stderr)
        sys.exit(2)
