#!/usr/bin/env python3
"""
Derive the Tamil noun declension, and check it against the gold.

The claim in audit/DERIVABILITY.md is that ThamizhiMorph's declension table is a
THEOREM, not data. This program tries to prove it: it states the derivation as a
small parameter set, runs it over every stem, and diffs against the 1,554,418
round-trip-verified cells in data/derived/nouns_grid.tsv.

The derivation has three stages, all operating on TLP1 phonemes:

    1. CLASSIFY   stem              -> class        (from the final phoneme)
    2. STEM-FORM  stem + class      -> nom/obl/pl stem   (truncate k, add increment)
    3. MARKER     bundle            -> case marker (invariant across classes)

    surface = stemform(stem, class, form(bundle)) + marker(bundle)

Parameters are LEARNED once from the gold and written to data/derived/noun_rules.json,
then the derivation runs from that file alone. Learning them is legitimate -- it is what
reading the grammar does -- but the count is the claim, so it is reported.

Usage:
    python3 tools/derive_nouns.py learn      # fit parameters, write noun_rules.json
    python3 tools/derive_nouns.py eval       # derive all cells, diff against gold
"""
import sys, json, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

import os
GRID  = ROOT / os.environ.get("TAMILOS_GRID", "data/derived/nouns_grid_final.tsv")
PAIRED = os.environ.get("TAMILOS_PAIRED", "") == "1"
RULES = ROOT / ("data/derived/noun_rules_paired.json" if PAIRED
                else "data/derived/noun_rules.json")
U = T.encode("உ")[0]

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

def hx(b):  return b.hex()
def unhx(s): return bytes.fromhex(s)

# ------------------------------------------------------------------ bundle -> stem form
SANDHI = ("+sandhic", "+sandhik", "+sandhip", "+sandhit")

def form(feat):
    """Which stem-form a feature bundle selects.

    nomsandhi is separate from nom because a sandhi-marked nominative DELETES the
    stem-final nasal -- akakkaNNan + sandhic -> akakkaNNac, not akakkaNNanc.
    That is foma R18/R17: {n}/{m} -> 0 || _ "^" [t|c|T|p]. Folding it into nom
    accounted for 85% of all derivation misses."""
    if "+pl" in feat: return "pl"
    core = feat.replace("noun", "")
    for x in ("+foc", "+cmpr") + SANDHI: core = core.replace(x, "")
    if core.strip("+") in ("nom", ""):
        return "nomsandhi" if any(x in feat for x in SANDHI) else "nom"
    return "obl"

# ------------------------------------------------------------------ classifier context
TU_, RU_ = T.encode("ட்")[0], T.encode("ற்")[0]
N_, A_ = T.encode("ன்")[0], T.encode("அ")[0]

def context(stem):
    """The phonological context that selects the declension class.

    The final phoneme; and when the final is உ, the two before it.

    For ṭu/ṟu-final stems this implements Naṉṉūl 181-182's kuṟṟiyalukaram taxonomy
    instead, because the coarse V/C distinction cannot express it -- it misses both
    the நெடில்/குறில் contrast and the two-syllable முற்றியலுகரம் exclusion, which
    are exactly what carry the rule (see audit/NANNUL.md)."""
    b = enc(stem)
    if not b: return None
    if (len(b) > 2 and b[-1] == U and b[-2] in (TU_, RU_)
            and not (len(b) >= 4 and b[-3] == b[-2])):
        c = "T" if b[-2] == TU_ else "R"
        prev = b[-3]
        if T.is_mey(prev):      kind = "clust"    # Naṉṉūl 181
        elif T.is_nedil(prev):  kind = "nedil"    # நெடில்தொடர்
        elif sum(1 for x in b if T.is_uyir(x)) > 2: kind = "uyir"   # உயிர்த்தொடர்
        else:                   kind = "murri"    # முற்றியலுகரம்
        return f"nannul/{c}/{kind}"
    # ன்-final: the ன் → ர் plural is SUFFIX SUBSTITUTION, not sandhi -- the masculine
    # singular -அன் being replaced by the rational plural -அர். So it applies only where
    # the ன் IS that suffix. A monosyllable's ன் is part of the root (மன், கன், அன்), so
    # nothing is substituted and the plural is plain கள். Measured: 99.95% over 12,929
    # ன்-final stems. See audit/NSTEM.md.
    if b[-1] == N_ and len(b) > 1:
        a = "a" if b[-2] == A_ else "x"
        return f"n/{a}/{'1' if sum(1 for x in b if T.is_uyir(x)) == 1 else 'n'}"
    if b[-1] == U and len(b) > 2:
        return f"u/{b[-2]:02X}/{'V' if T.is_uyir(b[-3]) else 'C'}"
    if b[-1] == U and len(b) > 1:
        return f"u/{b[-2]:02X}"
    return f"{b[-1]:02X}"

# REGISTER: "modern" accepts only B-tagged surfaces; "classical" accepts B and C.
# B = valid in both, C = classical only (Naṉṉūl 226 உறழ்வு). See tools/build_tagged_gold.py.
REGISTER = os.environ.get("TAMILOS_REGISTER", "classical")

def load_rows():
    rows = []
    with open(GRID, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4: continue
            surfs = p[3].split("|")
            if len(p) >= 5:
                tags = p[4].split("|")
                if len(tags) == len(surfs):
                    allowed = {"B"} if REGISTER == "modern" else {"B", "C"}
                    surfs = [x for x, t in zip(surfs, tags) if t in allowed]
            if not surfs: continue
            rows.append((p[0], p[1].replace("SgRoot", "").replace("plRoot", "pl"),
                         p[2], surfs))
    return rows

# ------------------------------------------------------------------ learn
def _alt_threshold():
    # only meaningful when this module is run as a script; importing it must not
    # try to parse the importer's argv
    if __name__ == "__main__" and len(sys.argv) > 2:
        try: return float(sys.argv[2])
        except ValueError: pass
    return 0.35
ALT_THRESHOLD = _alt_threshold()

def learn():
    rows = load_rows()
    print(f"gold cells: {len(rows):,}")

    # 1. classifier
    ctx = collections.defaultdict(collections.Counter)
    for stem, cls, _, _ in rows:
        c = context(stem)
        if c: ctx[c][cls] += 1
    classifier = {c: cnt.most_common(1)[0][0] for c, cnt in ctx.items()}
    print(f"  classifier contexts : {len(classifier)}")

    # 2. stem forms: (class, form) -> (k, increment)
    obs = collections.defaultdict(list)
    for stem, cls, feat, surfs in rows:
        sb = enc(stem)
        if not sb: continue
        for su in surfs:
            ub = enc(su)
            if not ub: continue
            i = 0
            while i < len(sb) and i < len(ub) and sb[i] == ub[i]: i += 1
            obs[(cls, form(feat))].append((len(sb) - i, bytes(ub[i:])))
    # A class may licence more than one stem-form (C1 plural is both -kkaL and bare).
    # Keep every (k, increment) alternant covering >=5% of that cell's observations.
    stemforms = {}; n_sf = 0
    for key, lst in obs.items():
        tot = len(lst); alts = []
        for k in sorted({kk for kk, _ in lst}):
            pool = [s for kk, s in lst if kk == k]
            if len(pool) / tot < ALT_THRESHOLD: continue
            m = min(pool, key=len); inc = b""
            for i in range(len(m), 0, -1):
                if all(x[:i] == m[:i] for x in pool): inc = m[:i]; break
            alts.append([k, hx(inc)])
            # the residual pool at this k may itself split; take a second branch
            rest = [s for s in pool if not s.startswith(inc)] if inc else []
            if len(rest) / tot >= ALT_THRESHOLD:
                m2 = min(rest, key=len); inc2 = b""
                for i in range(len(m2), 0, -1):
                    if all(x[:i] == m2[:i] for x in rest): inc2 = m2[:i]; break
                alts.append([k, hx(inc2)])
        if not alts: alts = [[0, ""]]
        stemforms[f"{key[0]}|{key[1]}"] = alts; n_sf += len(alts)
    print(f"  stem-form params    : {n_sf}  ({len(stemforms)} cells)")

    # 3. markers
    #
    # UNPAIRED (the original): markers are keyed by bundle alone, so derivation takes
    # the CROSS-PRODUCT of stem-form alternants with markers. That is where the
    # over-generation comes from: a class whose plural increment is கள் also has a
    # zero-increment alternant, and the marker table holds both இல் and க்களில்,
    # so கள் + க்களில் = கள்க்களில் -- plural marked twice, not Tamil.
    #
    # PAIRED: attribute each observed marker to the ALTERNANT that actually explained
    # it, and key markers by (class, form, alternant, bundle). Only attested pairs are
    # emitted. When several alternants match a surface the longest base wins, since it
    # is the most specific decomposition.
    mk = collections.defaultdict(collections.Counter)
    for stem, cls, feat, surfs in rows:
        sb = enc(stem); key = f"{cls}|{form(feat)}"
        if not sb or key not in stemforms: continue
        for su in surfs:
            ub = enc(su)
            if not ub: continue
            best = None
            for idx, (k, inch) in enumerate(stemforms[key]):
                base = sb[:len(sb) - k] + unhx(inch)
                if ub[:len(base)] == base and (best is None or len(base) > best[1]):
                    best = (idx, len(base))
            if best is None: continue
            idx, blen = best
            mkey = f"{key}|{idx}|{feat}" if PAIRED else feat
            mk[mkey][bytes(ub[blen:])] += 1
    markers = {}
    n_m = 0
    for mkey, cnt in mk.items():
        tot = sum(cnt.values())
        _mt = float(os.environ.get('TAMILOS_MT', '0.05'))
        keep = [hx(m) for m, c in cnt.most_common() if c / tot >= _mt]
        markers[mkey] = keep; n_m += len(keep)
    print(f"  marker strings      : {n_m}" + ("   (paired)" if PAIRED else "   (per bundle)"))
    print(f"  TOTAL PARAMETERS    : {len(classifier)+n_sf+n_m}")

    RULES.write_text(json.dumps(
        {"classifier": classifier, "stemforms": stemforms, "markers": markers},
        ensure_ascii=False), encoding="utf-8")
    print(f"  written -> {RULES.relative_to(ROOT)}")

# ------------------------------------------------------------------ derive
class Deriver:
    def __init__(self):
        r = json.loads(RULES.read_text(encoding="utf-8"))
        self.cls = r["classifier"]; self.sf = r["stemforms"]; self.mk = r["markers"]
    def classify(self, stem):
        return self.cls.get(context(stem))
    def derive(self, stem, feat):
        b = enc(stem); c = self.classify(stem)
        if not b or not c: return set()
        key = f"{c}|{form(feat)}"
        if key not in self.sf: return set()
        out = set()
        for idx, (k, inch) in enumerate(self.sf[key]):
            base = b[:len(b) - k] + unhx(inch)
            mlist = self.mk.get(f"{key}|{idx}|{feat}", []) if PAIRED else self.mk.get(feat, [])
            for mh in mlist:
                try: out.add(T.decode(base + unhx(mh)))
                except T.TLP1Error: pass
        return out

# ------------------------------------------------------------------ evaluate
def evaluate():
    d = Deriver(); rows = load_rows()
    exact = superset = partial = miss = nocls = 0
    cellhit = celltot = 0
    badclass = collections.Counter()
    for stem, cls, feat, surfs in rows:
        gold = set(surfs)
        pred = d.derive(stem, feat)
        if d.classify(stem) is None: nocls += 1; continue
        if d.classify(stem) != cls: badclass[cls] += 1
        celltot += len(gold); cellhit += len(gold & pred)
        if pred == gold: exact += 1
        elif gold and gold <= pred: superset += 1
        elif gold & pred: partial += 1
        else: miss += 1
    n = exact + superset + partial + miss
    tp=fp=fn=0
    for stem, cls, feat, surfs in rows:
        if d.classify(stem) is None: continue
        g=set(surfs); pr=d.derive(stem,feat)
        tp+=len(g&pr); fp+=len(pr-g); fn+=len(g-pr)
    P=tp/max(tp+fp,1); R=tp/max(tp+fn,1)
    print(f"cells evaluated            : {n:,}")
    print(f"  EXACT set match          : {exact:,}  ({100*exact/n:.2f}%)")
    print(f"  derived ⊇ gold           : {superset:,}  ({100*superset/n:.2f}%)")
    print(f"  partial overlap          : {partial:,}  ({100*partial/n:.2f}%)")
    print(f"  complete miss            : {miss:,}  ({100*miss/n:.2f}%)")
    print(f"  unclassifiable stems     : {nocls:,}")
    print()
    print(f"  at least one correct form: {exact+superset+partial:,}  "
          f"({100*(exact+superset+partial)/n:.2f}%)")
    print(f"  individual gold surfaces reproduced: {cellhit:,}/{celltot:,} "
          f"({100*cellhit/celltot:.2f}%)")
    print(f"  PRECISION {100*P:.2f}%   RECALL {100*R:.2f}%   F1 {100*2*P*R/max(P+R,1e-9):.2f}%")
    if badclass:
        print(f"\n  misclassified stems by class: {dict(badclass.most_common(5))}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "eval"
    if cmd == "learn": learn()
    else: evaluate()
