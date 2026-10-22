#!/usr/bin/env python3
"""
Patch the ThamizhiMorph gold against Arden 1910.

audit/ADJUDICATION.md established three defects in the gold, each with a citation.
This applies them, writes a corrected grid alongside the original (never over it),
and logs every change.

  Arden 145  the particle இன் MAY be inserted before the casal affix of any case of
             any noun -- it is optional. ThamizhiMorph licenses only the இன்-inserted
             form for 6 bundles. Add the plain counterparts.
  Arden 110  the dative affix is கு after a base ending in இ, ஈ or ஐ; உக்கு only
             after other letters. ThamizhiMorph generates மொழியுக்கு (and மொழியுக்காக). Add மொழிக்கு (and மொழிக்காக).
  Arden 134  நடு and மறு -- words of two short open syllables -- belong to the FOURTH
             declension, whose base equals the nominative. They must not double.

Output: data/derived/nouns_grid_arden.tsv  +  data/derived/gold_patch.log
"""
import sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

GRID = ROOT / "data/derived/nouns_grid.tsv"
OUT  = ROOT / "data/derived/nouns_grid_arden.tsv"
LOG  = ROOT / "data/derived/gold_patch.log"

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

I, II, AI = T.encode("இ")[0], T.encode("ஈ")[0], T.encode("ஐ")[0]
FRONT = {I, II, AI}

# Arden 145 -- bundle -> (IN-form marker tail, plain counterpart tail)
IN_PAIRS = {
    "noun+pl+acc":        [("இனை", "ஐ")],
    "noun+pl+acc+foc":    [("இனைத்தான்", "ஐத்தான்")],
    "noun+pl+inst":       [("இனால்", "ஆல்")],
    "noun+pl+inst+foc":   [("இனால்தான்", "ஆல்தான்")],
    "noun+infInc+gen":    [("இனது", "அது")],
    "noun+infInc+gen+foc":[("இனதுதான்", "அதுதான்")],
}

import json
MARKERS = json.loads((ROOT / "data/derived/noun_rules.json").read_text(encoding="utf-8"))["markers"]
GLIDE_V = T.encode("வ்")     # u-final base + vowel-initial marker -> v glide
TU_, RU_ = T.encode("ட்")[0], T.encode("ற்")[0]
U = T.encode("உ")[0]

def _is_nom(feat):
    core = feat.replace("noun", "")
    for x in ("+foc", "+cmpr", "+sandhic", "+sandhik", "+sandhip", "+sandhit"):
        core = core.replace(x, "")
    return core.strip("+") in ("nom", "")

def two_short_open(b):
    """Arden 134: C V C உ, both vowels kuril -- naTu, maRu."""
    return (b is not None and len(b) == 4
            and T.is_mey(b[0]) and T.is_kuril(b[1])
            and T.is_mey(b[2]) and T.is_kuril(b[3]))

def main():
    log = []; n145 = n110 = n134 = n129 = n_del = n110d = 0
    out = []
    for line in GRID.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) != 4: continue
        stem, cls, feat, surfs = p[0], p[1], p[2], p[3].split("|")
        sb = enc(stem); add = set(); drop110 = set()

        # --- Arden 145: in-insertion is optional -------------------------------
        # MUST be matched in TLP1, not Unicode: viRkaLinai does not string-end with
        # "inai" because the i is written as the dependent sign after L. Same trap
        # that made the verb concatenation test score 0/2067 in DERIVABILITY.md.
        for insuf, plain in IN_PAIRS.get(feat, []):
            ib, pb = enc(insuf), enc(plain)
            for s in surfs:
                sbf = enc(s)
                if sbf and ib and sbf[-len(ib):] == ib:
                    cand = T.decode(sbf[:len(sbf)-len(ib)] + pb)
                    if cand not in surfs:
                        add.add(cand); n145 += 1
                        if len(log) < 20000: log.append(f"145\t{stem}\t{feat}\t+{cand}\t(from {s})")

        # --- Arden 110: dative ku after i/ii/ai --------------------------------
        if "dat" in feat and "pl" not in feat and sb and sb[-1] in FRONT:
            for s in surfs:
                # யுக்கு is the plain dative; யுக்காக is the same உ சாரியை before the benefactive ஆக
                if "யிற்கு" in s or "யிற்காக" in s:
                    # the இன் route does not exist after இ ஈ ஐ either: குழந்தையிற்கு, தந்தையிற்கு are not forms
                    drop110.add(s); n110d += 1
                    if len(log) < 20000: log.append(f"110d\t{stem}\t{feat}\t-{s}")
                for wrong, right in (("யுக்கு", "க்கு"), ("யுக்காக", "க்காக")):
                    if wrong in s:
                        cand = s.replace(wrong, right)
                        if cand not in surfs:
                            add.add(cand); n110 += 1
                            if len(log) < 20000: log.append(f"110\t{stem}\t{feat}\t+{cand}\t(was {s})")
                        # Arden (rank 2) outranks ThamizhiMorph (rank 3), and he says the உக்கு form is for bases
                        # ending in any OTHER letter, so after இ ஈ ஐ it is wrong, not a second licensed form.
                        # The correct form is in the cell (just added, or already there), so no cell empties.
                        drop110.add(s); n110d += 1
                        if len(log) < 20000: log.append(f"110d\t{stem}\t{feat}\t-{s}")

        # --- Arden 134: two short open syllables do not double -----------------
        # The base equals the nominative (Arden 136), so the marker attaches directly.
        # It must NOT be rebuilt from the gold's tail: the gold's tail belongs to a
        # DOUBLED base, and splicing it onto the undoubled one yields naTu+Tai = naTuTai
        # instead of naTuvai. A patch that injects a wrong form into the gold is worse
        # than one that injects nothing, so the marker is attached with the glide rule.
        if two_short_open(sb) and feat in MARKERS and '+pl' not in feat:
            for mh in MARKERS[feat]:
                mb = bytes.fromhex(mh)
                # Only VOWEL-INITIAL markers. A consonant-initial marker such as னை or
                # யை already carries another class's glide; splicing those on would
                # licence naTunai and naTuyai, which are not Tamil. The glide for a
                # u-final base is வ் and is supplied here, once.
                if not mb or not T.is_uyir(mb[0]): continue
                glide = GLIDE_V
                cand = T.decode(sb + glide + mb)
                if cand not in surfs and cand not in add:
                    add.add(cand); n134 += 1
                    if len(log) < 20000: log.append(f"134\t{stem}\t{feat}\t+{cand}\t(gold {'/'.join(surfs)})")
        # --- Arden 129-130: third-declension டு/று DOUBLE in the oblique ---------
        # "The inflectional base is formed by doubling the consonant of the final
        # syllable; as வீடு, inf. base வீட்டு; ஆறு, inf. base ஆற்று." (130)
        # Measured: C6 (டு-final) already doubles 225/225. C7 and C8 (ற்-final) NEVER
        # do -- 348 oblique cells over 116 stems, all ஏறு/ஞாயிறு type. Excluded by
        # 134: two-short-open stems, and stems already doubled (பட்டு, காற்று).
        # Naṉṉūl 181 REFINES Arden here. Arden 129-130 says all டு/று stems double;
        # Naṉṉūl 181-182 says only the நெடில்தொடர் and உயிர்த்தொடர் kinds do, and the
        # cluster kinds (வன்/மென்/இடை/ஆய்தத் தொடர்) do NOT. Without this guard the patch
        # licensed தொண்ட்டை, குண்ட்டை, வண்ட்டை -- not Tamil.
        if (sb and len(sb) >= 3 and sb[-1] == U and sb[-2] in (TU_, RU_)
                and not two_short_open(sb) and not (len(sb) >= 4 and sb[-3] == sb[-2])
                and not T.is_mey(sb[-3])                      # Naṉṉūl 181
                and "+pl" not in feat and not _is_nom(feat) and feat in MARKERS):
            dbl = sb[:-1] + bytes([sb[-2]])
            already = any((lambda x: x is not None and x[:len(dbl)] == dbl)(enc(x2))
                          for x2 in surfs)
            if not already:
                for mh in MARKERS[feat]:
                    mb = bytes.fromhex(mh)
                    if not mb or not T.is_uyir(mb[0]): continue   # same guard as 134
                    cand = T.decode(dbl + mb)
                    if cand not in surfs and cand not in add:
                        add.add(cand); n129 += 1
                        if len(log) < 20000:
                            log.append(f"129\t{stem}\t{feat}\t+{cand}\t(gold {'/'.join(surfs)})")

        # --- REMOVAL: two-short-open stems must not double -----------------------
        # Most patches only ADD, which is the safe direction. This one (and the Arden 110 one above) removes,
        # because leaving மட்டை licensed means the verifier accepts non-Tamil -- the
        # exact failure mode this gold exists to prevent. Gated to the one case two
        # authorities agree on: Arden 134 (fourth declension, base = nominative) and
        # Naṉṉūl's முற்றியலுகரம் (a full உ, so 182's doubling does not apply).
        drop = set()
        if two_short_open(sb):
            dbl = sb[:-1] + bytes([sb[-2]])
            for s2 in surfs:
                u2 = enc(s2)
                if u2 and u2[:len(dbl)] == dbl:
                    drop.add(s2); n_del += 1
                    if len(log) < 20000: log.append(f"134d\t{stem}\t{feat}\t-{s2}")

        final = (set(surfs) | add) - drop - drop110
        if not final: final = set(surfs)            # never empty a cell
        out.append("\t".join([stem, cls, feat, "|".join(sorted(final))]))

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"cells written       : {len(out):,} -> {OUT.relative_to(ROOT)}")
    print(f"  Arden 145 additions: {n145:,}")
    print(f"  Arden 110 additions: {n110:,}")
    print(f"  Arden 110 REMOVED  : {n110d:,}   (the உக்கு form after இ ஈ ஐ)")
    print(f"  Arden 134 additions: {n134:,}")
    print(f"  Arden 129 additions: {n129:,}   (Naṉṉūl 181 guard applied)")
    print(f"  REMOVED (134+Naṉṉūl): {n_del:,}")
    print(f"  TOTAL new surfaces : {n145+n110+n134+n129:,}")

if __name__ == "__main__":
    main()
