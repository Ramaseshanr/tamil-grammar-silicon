#!/usr/bin/env python3
"""
The விகுதி seam — Naṉṉūl Eḻuttatikāram 243, applied to the verb grid.

243 names the விகுதி **first**:

> பதம்முன் **விகுதியும்** பதமும் உருபும் / புணர்வழி ஒன்றும் பலவும் சாரியை /
> வருதலும் தவிர்தலும் விகற்பமும் ஆகும்

So the same licence that governs the உருபு seam (audit/URUBU_PUNARIYAL.md,
audit/VIKARPAM_GRID.md) governs the verb விகுதி seam, and 244's பொதுச்சாரியை inventory
supplies the material:

> அன் ஆன் இன் **அல்** அற்று இற்று அத்து அம் / தம் நம் நும் ஏ அ **உ** ஐ **கு** ன /
> இன்ன பிறவும் பொதுச் சாரியையே

**அல், உ, கு and அன் are all in that list.** That is the citation for the two families
`tools/add_nurpa327.py` left explicitly unimplemented, which Vellaivaranar names in his
commentary on Collatikāram 327:

    ப     உண்ப · **உண்குப** (குகரச் சாரியை) · **உணுப** (உகரச் சாரியை)
    மார்  உண்மார் · சென்மார் · கொண்மார் · **காணன்மார்** · **பாடன்மார்**

    காண் + அன் + மார்            -> காணன்மார்      [அன் சாரியை, 244]
    பாடு -> பாடல் + மார்          -> பாடன்மார்      [அல் சாரியை, 244; ல் -> ன் by
                                                     மெய்யீற்றுப் புணரியல்]

Which roots take which சாரியை is **not enumerated**, because nūṟpā **253** says it cannot
be: "இதற்கு இது சாரியை எனின் அளவு இன்மையின்". So, following the practice of
add_nurpa327.py, the forms are generated for every root that already has the corresponding
விகுதி cell and tagged classical; the corpus may promote and may never demote.

Output: data/derived/verbs_grid_vikarpam.tsv, one row per surface, eight columns —
the grid's own five, then licence, corpus count, and the mechanism.

    lic   G  the grid already has this surface
          V  a விகற்பம் alternant licensed by 243/244, which the grid omits
          VA a V the corpus attests at n >= 20
    mech  `-` for G, else sar=கு · sar=உ · sar=அன் · sar=அல்

Usage:
    python3 tools/build_vikarpam_verbs.py          # build, guard, install
    python3 tools/build_vikarpam_verbs.py verify   # re-check an installed grid
"""
import os, re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import buildcheck as B

SRC  = ROOT / os.environ.get("TAMILOS_VGRID", "data/derived/verbs_grid_final.tsv")
OUT  = ROOT / os.environ.get("TAMILOS_VVIK", "data/derived/verbs_grid_vikarpam.tsv")
FREQ = ROOT / "data/gold/freq/tawiki_freq.tsv"
MIN_ATT = int(os.environ.get("TAMILOS_MIN_ATT", "20"))
LIC, REG = {"G", "V", "VA"}, {"B", "C", "-"}

U, A = T.encode("உ")[0], T.encode("அ")[0]
KU, AN, AL, PA = T.encode("கு"), T.encode("அன்"), T.encode("அல்"), T.encode("ப")
MAAR = T.encode("மார்")

# ல் -> ன், ள் -> ண் before ம். NOT a mask-and-OR: இடையினம் is numbered on its own scale,
# so this is an explicit pair map (spec/TLP1.md, closing note).
# Draft 2 of the layout makes this T.nasalize() -- one AND, one OR. The set is which
# consonants the rule applies to, not a translation table.
_NASALISES = {T.encode("ல்")[0], T.encode("ள்")[0]}

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

def dec(b):
    try: return T.decode(b)
    except Exception: return None

def nasalize_final(b):
    if b and b[-1] in _NASALISES:
        return b[:-1] + bytes([T.nasalize(b[-1])])
    return b

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

# ------------------------------------------------------------------ the சாரியை
def sariyai_pa(root_b):
    """உண் -> உண்குப [குகரச் சாரியை] · உணுப [உகரச் சாரியை].

    Both only after a consonant-final root: the சாரியை is what supplies the vowel.
    A உ-final root already has its உ, so there is nothing for them to do."""
    if not root_b or not T.is_mey(root_b[-1]): return []
    return [(dec(root_b + KU + PA), "sar=கு"),
            (dec(root_b + bytes([U]) + PA), "sar=உ")]

def sariyai_maar(root_b):
    """காண் -> காணன்மார் [அன் சாரியை] · பாடு -> பாடல் -> பாடன்மார் [அல் சாரியை]."""
    out = []
    if root_b and T.is_mey(root_b[-1]):
        out.append((dec(nasalize_final(root_b + AN) + MAAR), "sar=அன்"))
    elif len(root_b) >= 2 and root_b[-1] == U and T.is_mey(root_b[-2]):
        out.append((dec(nasalize_final(root_b[:-1] + AL) + MAAR), "sar=அல்"))
    return out

GEN = {"3ple=ப": sariyai_pa, "3ple=மார்": sariyai_maar}

# ------------------------------------------------------------------ guards
def check_row(p, lineno):
    if len(p) != 8:
        raise B.BuildError(f"{OUT.name}:{lineno}: {len(p)} columns, expected 8")
    stem, cls, feat, surf, reg, lic, n, mech = p
    if not surf:  raise B.BuildError(f"{OUT.name}:{lineno}: empty surface")
    if "|" in surf:
        raise B.BuildError(f"{OUT.name}:{lineno}: pipe in surface — one per row")
    if lic not in LIC: raise B.BuildError(f"{OUT.name}:{lineno}: bad lic {lic!r}")
    if reg not in REG: raise B.BuildError(f"{OUT.name}:{lineno}: bad reg {reg!r}")
    if not n.isdigit(): raise B.BuildError(f"{OUT.name}:{lineno}: bad count {n!r}")
    if lic == "G" and mech != "-":
        raise B.BuildError(f"{OUT.name}:{lineno}: G carries mech {mech!r}")
    if lic in ("V", "VA") and not mech.startswith("sar="):
        raise B.BuildError(f"{OUT.name}:{lineno}: {lic} has no சாரியை attribution")
    if lic == "VA" and int(n) < MIN_ATT:
        raise B.BuildError(f"{OUT.name}:{lineno}: VA below threshold ({n} < {MIN_ATT})")

def build():
    freq = load_freq()
    rows, roots, have = [], {}, set()
    src_surf = 0
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4: continue
            surfs = p[3].split("|")
            regs = p[4].split("|") if len(p) > 4 else ["-"] * len(surfs)
            if len(regs) != len(surfs): regs = ["-"] * len(surfs)
            for s, r in zip(surfs, regs):
                rows.append((p[0], p[1], p[2], s, r if r in REG else "-"))
                have.add(s); src_surf += 1
            tail = p[2].rsplit("+", 1)[-1]
            # Only a PLAIN SIMPLE frame may seed a சாரியை form. The சாரியை attaches to
            # the bare root, so seeding from a causative cell would file உண்குப under
            # `+caus=பி+fut=ப்`, claiming a causative and a tense marker the surface does
            # not contain -- a wrong analysis for a right surface, which is worse than
            # no analysis. Caught by inspecting the first build's own output.
            if tail in GEN and "+sim+" in p[2] and "caus=" not in p[2]:
                roots.setdefault((p[0], p[1], p[2], tail), None)
    print(f"  grid: {src_surf:,} surfaces   "
          f"{len(roots):,} cells at a விகுதி this nūṟpā reaches")

    # the homograph guard of docs/METHOD.md: a count on a surface that is also an
    # independent word is evidence about that word, not about this form.
    import phon_rules as P
    _, nstems = P.load_lexc()
    homo = set(nstems) | {r[0] for r in rows}
    print(f"  homograph inventory: {len(homo):,} nouns + verb roots")

    gen, blocked = {}, []
    for (root, cls, feat, tail) in sorted(roots):
        rb = enc(root)
        if rb is None: continue
        for cand, mech in GEN[tail](rb):
            if cand is None or cand in have or cand in gen: continue
            # the சாரியை-borne விகுதி carries the future itself, as மார் does, so the
            # analysis drops the +fut= group and records the சாரியை instead
            nf = re.sub(r"\+fut=[^+]+", "", feat)
            nf = nf[: nf.rfind("+")] + f"+{mech}+{tail}"
            n = freq.get(cand, 0)
            # A மார் surface is NEVER unambiguous. Naṉṉūl's own clause in 327 --
            # `மார் வினையொடு முடிமே`, "மார் concludes with a verb" -- is a SYNTACTIC
            # condition, and a frequency list has no syntax, so it cannot tell the verb
            # விகுதி from the homographic noun plural (தந்தைமார், அண்ணன்மார்). The first
            # build promoted அண்ணன்மார் on n=25, which is the noun plural "elder
            # brothers"; அண்ணன் is not even in Nouns.lexc, so no stem-inventory guard
            # could have caught it. Under AUTHORITY.md rank 4 a count may promote only an
            # unambiguous surface, so மார் forms are never promoted on corpus evidence.
            if n >= MIN_ATT and tail == "3ple=மார்":
                blocked.append((n, cand, "மார் வினையொடு முடிமே — no syntax in a count"))
                lic = "V"
            elif n >= MIN_ATT and cand in homo:
                blocked.append((n, cand, "also a declared stem or root")); lic = "V"
            else:
                lic = "VA" if n >= MIN_ATT else "V"
            gen[cand] = (root, cls, nf, lic, n, mech)

    tmp = OUT.with_suffix(".part")
    st = collections.Counter(); mechs = collections.Counter()
    out_n = 0
    with open(tmp, "w", encoding="utf-8") as o:
        for stem, cls, feat, s, reg in rows:
            p = [stem, cls, feat, s, reg, "G", str(freq.get(s, 0)), "-"]
            check_row(p, out_n + 1); o.write("\t".join(p) + "\n")
            st["G"] += 1; out_n += 1
        for cand, (root, cls, feat, lic, n, mech) in sorted(gen.items()):
            p = [root, cls, feat, cand, "-", lic, str(n), mech]
            check_row(p, out_n + 1); o.write("\t".join(p) + "\n")
            st[lic] += 1; mechs[mech] += 1; out_n += 1

    if st["G"] != src_surf:
        raise B.BuildError(f"SURFACE LOSS: {src_surf:,} in, {st['G']:,} tagged G")
    tmp.replace(OUT)
    return st, mechs, src_surf, out_n, blocked

def verify():
    st = collections.Counter(); n = 0
    with open(OUT, encoding="utf-8") as f:
        for line in f:
            n += 1
            p = line.rstrip("\n").split("\t")
            check_row(p, n); st[p[5]] += 1
    print(f"  {OUT.name}: {n:,} rows   "
          + "   ".join(f"{k} {v:,}" for k, v in sorted(st.items())))
    print("  ok: every row tagged, counted and attributed to a சாரியை")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify(); return 0
    print(f"=== விகுதி seam [Naṉṉūl Eḻuttatikāram 243, 244]  -> {B.rel(OUT)}")
    st, mechs, src_surf, out_n, blocked = build()
    print(f"  surfaces {src_surf:,} -> {out_n:,}")
    print(f"    G  the grid has it                  {st['G']:9,d}")
    print(f"    V  விகற்பம், corpus silent           {st['V']:9,d}")
    print(f"    VA விகற்பம், attested n>={MIN_ATT:<3d}         {st['VA']:9,d}")
    print(f"\n  alternants by சாரியை [Naṉṉūl 244]")
    for m, c in mechs.most_common():
        print(f"    {m:12s} {c:9,d}")
    if blocked:
        blocked.sort(reverse=True)
        print(f"\n  promotions blocked by the homograph guard: {len(blocked):,}")
        for n, s, why in blocked[:6]: print(f"    {s:18s} n={n:,} — {why}")
    print(f"\n  Vellaivaranar's own examples")
    for w in ("உண்குப", "உணுப", "காணன்மார்", "பாடன்மார்"):
        print(f"    {w:14s} {'generated' if _has(w) else 'MISSING'}")
    print()
    verify()
    return 0

def _has(w):
    with open(OUT, encoding="utf-8") as f:
        for line in f:
            if line.split("\t")[3] == w: return True
    return False

if __name__ == "__main__":
    try:
        sys.exit(main())
    except B.BuildError as e:
        print(f"\nVIKUTI SEAM FAILED\n{e}", file=sys.stderr)
        sys.exit(2)
