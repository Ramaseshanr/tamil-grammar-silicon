#!/usr/bin/env python3
"""
The noun generator, as an executable specification shaped like the hardware.

hdl/rtl/tamil_noun_gen.sv is a transliteration of this file. It is not a second derivation: it is
phon_rules.derive() restated as the machine that would run it, so the structure the RTL needs can be
checked first, in software, against every cell of the reference:

    class ROM      truncate, increment bytes, geminates, doubles-final, plain-ok, ன்->ர்
    morpheme ROM   per slot, the alternative endings (bytes), and whether each begins இன்
    eight slots    pl, in, case, ben, cmpr, vp, foc, sandhi -- active as the bundle says (vp: one of the
                   vowel particles உம் ஏ ஓ ஆ)
    choices        at each slot the options are counted from the current state, and the generator
                   walks them like an odometer: every leaf is one licensed surface
    seam           tools/phon_rules.join(), which hdl/rtl/tamil_join.sv matches on 927,200 vectors

    python3 tools/noun_gen_model.py              # all 1,554,418 cells against phon_rules.derive()
    python3 tools/noun_gen_model.py --particles  # the cells with a vowel particle added, which the grid does not list
"""
import sys, pathlib, itertools
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import phon_rules as P

B = P.B
CLASSES = list(P.STEMFORM)                      # the class code is the index
CLITIC = {"cmpr", "foc"}
SLOTS = ("pl", "in", "case", "ben", "cmpr", "vp", "foc", "sandhi")
VPART = P.VCLITIC                                # the vowel particles, in the order of the hardware's flag code 1..4
CASE_ORDER = ("acc", "inst", "dat", "loc", "abl", "gen", "soc", "nom", "so")
SANDHI = ("sandhik", "sandhic", "sandhip", "sandhit")

# morpheme ROM: slot kind -> list of alternatives as bytes (empty bytes = the slot may be empty)
ALTS = {"pl": [B(x) for x in P.MORPH["pl"]], "in": [B("இன்"), b""],
        "ben": [B(x) for x in P.MORPH["ben"]], "cmpr": [B(x) for x in P.MORPH["cmpr"]],
        "foc": [B(x) for x in P.MORPH["foc"]]}
for c in CASE_ORDER:
    if P.MORPH.get(c): ALTS[c] = [B(x) for x in P.MORPH[c]]
for s in SANDHI: ALTS[s] = [B(x) for x in P.MORPH[s]]
for s in VPART: ALTS[s] = [B(x) for x in P.MORPH[s]]
IN_START = B("இன்")                              # a case alternative that begins இன் is barred after the சாரியை இன்
DAT_U = B("உக்கு"); DAT_KU = B("கு")
FRONT_IU = lambda cur: bool(cur) and T.is_uyir(cur[-1]) and (cur[-1] & 7) in (1, 5)    # P12: இ ஈ ஐ


def bundle(feat):
    """feature string -> the fields the hardware takes."""
    tags = [t for t in feat.split("+") if t and t != "noun"]
    case = next((c for c in CASE_ORDER if c in tags and P.MORPH.get(c)), None)
    return {"pl": "pl" in tags, "in": any(c in tags for c in ("acc", "inst", "gen", "abl")),
            "case": case, "ben": "ben" in tags, "cmpr": "cmpr" in tags, "foc": "foc" in tags,
            "vp": next((s for s in VPART if s in tags), None),
            "sandhi": next((s for s in SANDHI if s in tags), None),
            "obl": ("infInc" in tags) or P.needs_obl(feat)}


def seam(cur, right, **flags):
    return P.join(bytes(cur), bytes(right), **flags)


def stem_form(stem_b, cls, bf):
    """-> list of (bytes, kural) base alternatives, and (gem, dblfin)."""
    trunc, inc, gem, dblfin = P.STEMFORM[cls]
    kural = False
    b = bytes(stem_b)
    if bf["obl"]:
        if trunc: b = b[:-trunc]
        if inc:
            ib = B(inc)
            if not (len(b) >= 2 and T.is_mey(b[-1]) and b[-1] == b[-2] and ib[0] == b[-1]):
                out = [(seam(b, ib, inc=True), ib[-1] == P.U)]
                if cls in P.PLAIN_OK: out.append((bytes(stem_b), False))
                return out, gem, dblfin
        return [(b, kural)], gem, dblfin
    if cls in P.KURAL_CLASSES and bf["vp"] and not bf["pl"] and b and b[-1] == P.U:
        b = b[:-1]                                 # the final குற்றியலுகரம் drops before a vowel particle [Naṉṉūl 164]
    elif bf["pl"] and cls in P.UYAR and b and b[-1] == P.NA:
        b = b[:-1] + bytes([P.RA])
    return [(b, kural)], gem, dblfin


def active(bf):
    return [("pl", bf["pl"] and "pl"), ("in", bf["in"] and "in"), ("case", bf["case"]),
            ("ben", bf["ben"] and "ben"), ("cmpr", bf["cmpr"] and "cmpr"), ("vp", bf["vp"]),
            ("foc", bf["foc"] and "foc"), ("sandhi", bf["sandhi"])]


def options(kind, cur, k, first, d0, gem, dblfin, pada_here):
    """Every (alternative, join-flags) the slot offers from this state: the odometer's digit."""
    opts = []
    for ai, a in enumerate(ALTS[kind]):
        g = gem
        if kind == "dat" and a != DAT_U and FRONT_IU(cur):
            continue                               # after இ ஈ ஐ the dative is கு only: no இற்கு
        if kind == "dat" and a == DAT_U and FRONT_IU(cur):
            a = DAT_KU; g = True
        if not a:
            opts.append((a, None)); continue
        if kind in CASE_ORDER and d0 and a[:len(IN_START)] == IN_START:
            continue
        base = dict(pada=pada_here, gem=g, clitic=kind in CLITIC, kural=k)
        opts.append((a, base))
        if dblfin and first:   opts.append((a, dict(base, mono=True)))
        if kind in CLITIC:     opts.append((a, dict(clitic=True, dbl=True)))
        if first:              opts.append((a, dict(base, nohard=True)))
    return opts


def generate(stem_b, cls, feat):
    bf = bundle(feat)
    bases, gem, dblfin = stem_form(stem_b, cls, bf)
    slots = [(s, k) for s, k in active(bf) if k]
    out = set()

    def walk(si, cur, k, first, d0):
        if si == len(slots):
            out.add(bytes(cur)); return
        slot, kind = slots[si]
        pada_here = bf["sandhi"] is not None and si == len(slots) - 1
        for a, fl in options(kind, cur, k, first, d0, gem, dblfin, pada_here):
            if fl is None:
                walk(si + 1, cur, k, first, d0)
            else:
                nxt = seam(cur, a, **fl)
                walk(si + 1, nxt, a[-1] == P.U, False, d0 or kind == "in")
    for b, kural in bases:
        walk(0, b, kural, True, False)
    return out


def particle_cells():
    """(stem, class, bundle) for every vowel particle added to every particle-free bundle the grid lists for a stem.
    The reference grid has no such cell; these are the cells the derivation adds."""
    plain = {}
    for stem, cl, feat, _ in P.rows():
        if not any(x in feat for x in P.PARTICLE_TAGS):
            plain.setdefault((stem, P.re.sub(r"(Sg|pl)Root$", "", cl)), set()).add(feat)
    for (stem, c), feats in sorted(plain.items()):
        for feat in sorted(feats):
            for v in VPART: yield stem, c, feat + "+" + v


def check(cells, label):
    ok = bad = skip = 0
    shown = 0
    for stem, c, feat in cells:
        want = P.derive(stem, c, feat)
        if want is None: skip += 1; continue
        got = {T.decode(bytes(x)) for x in generate(B(stem), c, feat)}
        if got == want: ok += 1
        else:
            bad += 1
            if shown < 8:
                shown += 1; print("  DIFF", stem, c, feat, "only model:", sorted(got - want)[:2], "only derive:", sorted(want - got)[:2])
    print(f"  noun generator model{label}: {ok:,} / {ok + bad:,} cells identical to phon_rules.derive()   skipped {skip:,}")
    return 1 if bad else 0


def main():
    if "--particles" in sys.argv:
        return check(particle_cells(), " (vowel-particle cells)")
    return check(((s, P.re.sub(r"(Sg|pl)Root$", "", cl), f) for s, cl, f, _ in P.rows()), "")


if __name__ == "__main__":
    sys.exit(main())
