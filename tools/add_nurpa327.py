#!/usr/bin/env python3
"""
The ப and மார் plural-rational விகுதி — Naṉṉūl Collatikāram 327.

> அர்ஆர் பவ்வூ ரகரமா ரீற்ற / பல்லோர் படர்க்கை மார் வினையொடு முடிமே

Vellaivaranar glosses it as **four** விகுதி — "அர், ஆர், ப, மார் என்னும் நான்கு விகுதி" —
and his twenty-three-ending உயர்திணை inventory confirms it: ... அர், ஆர், **ப, மார்**. The
project already generates அர் and ஆர். These are the other two.

Both are **future**, which is why neither takes a separate tense marker:

  ப     Vellaivaranar: உண்ப · உண்குப (குகரச் சாரியை) · உணுப (உகரச் சாரியை) · உண்பர்
  மார்  Vellaivaranar: உண்மார் · வருமார் · சென்மார் · எள்ளுமார் · கொண்மார் · காணன்மார்
        "மார்விகுதி … எதிர்காலம் உணர்த்தும்" — the விகுதி itself marks the future, and
        `மார் வினையொடு முடிமே` distinguishes it from the noun plural (தந்தைமார்).

TAGGED C. Both have ~0 modern corpus attestation, so they are classical-register only, by
the same rule as அமருகிறேன் in `audit/ADJUDICATION.md`. The corpus may promote, never
demote.

⚠️ ஊர் and அகரம் are NOT generated. They appear only in the Project Madurai *split* of
`பவ்வூ ரகரமா`, which no commentator supports — a split is an editorial act, not data.

  TAMILOS_VGRID=in.tsv TAMILOS_VOUT=out.tsv python3 tools/add_nurpa327.py
"""
import os, re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import buildcheck as B

SRC = ROOT / os.environ.get("TAMILOS_VGRID", "data/derived/verbs_grid_final.tsv")
OUT = ROOT / os.environ.get("TAMILOS_VOUT", "data/derived/verbs_grid_327.tsv")
FREQ = ROOT / "data/gold/freq/tawiki_freq.tsv"
MIN_ACT = int(os.environ.get("TAMILOS_MIN_ACT", "20"))

A  = T.encode("அ")[0]
MAAR = T.encode("மார்")
# ல்/ள் nasalise before ம் -- மெய்யீற்றுப் புணரியல். செல் -> சென்மார், கொள் -> கொண்மார்,
# exactly Vellaivaranar's examples.
#
# NOT a mask-and-OR. tlp1.nasalize() maps வல்லினம் -> மெல்லினம், which TLP1 aligns on the
# place field so that க்->ங் etc. is one OR. ல் and ள் are இடையினம், numbered on their own
# scale: ல் is place 2 and ன் is place 5. Applying nasalize() to ல் sets both இனம் bits and
# yields 0x72, which is not a phoneme at all -- decode raised KeyError 114. An explicit
# pair map is the honest encoding of this rule.
# Draft 2 of the layout makes this T.nasalize() -- one AND, one OR. The set is which
# consonants the rule applies to, not a translation table.
_NASALISES = {T.encode("ல்")[0], T.encode("ள்")[0]}

# ப replaces the PNG on an existing FUTURE plural-rational cell
SRC_PNG = ("3ple=ஆர்", "3sge=அர்")
FUT = re.compile(r'\+fut=')

def ok(s):
    try: T.encode(s); return True
    except T.TLP1Error: return False

def nasalize_final(b):
    """ல் -> ன், ள் -> ண் before ம்."""
    if b and b[-1] in _NASALISES:
        return b[:-1] + bytes([T.nasalize(b[-1])])
    return b

def freq():
    f = {}
    if FREQ.exists():
        with open(FREQ, encoding="utf-8") as fh:
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) == 2: f[p[0]] = int(p[1])
    return f

def main():
    V = freq()
    rows = []
    # pass 1: read, and remember one simple-frame feature string per root for மார்
    frame = {}
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            rows.append(p)
            if len(p) < 4: continue
            if "+sim+" in p[2] and FUT.search(p[2]) and p[2].rsplit("+", 1)[-1] in SRC_PNG:
                frame.setdefault(p[0], (p[1], p[2]))

    n_pa = n_maar = promoted = 0
    extra = collections.defaultdict(list)     # (root, cls, feat) -> [(surface, tag)]

    # --- ப : the same future stem, PNG replaced by அ
    for p in rows:
        if len(p) < 4: continue
        feat = p[2]
        tail = feat.rsplit("+", 1)[-1]
        if not (FUT.search(feat) and tail in SRC_PNG): continue
        png = T.encode(tail.split("=", 1)[1])
        new_feat = feat[: feat.rfind("+")] + "+3ple=ப"
        for s in p[3].split("|"):
            if not ok(s): continue
            sb = T.encode(s)
            if sb[-len(png):] != png: continue
            cand = T.decode(sb[: -len(png)] + bytes([A]))
            tag = "B" if V.get(cand, 0) >= MIN_ACT else "C"
            if tag == "B": promoted += 1
            extra[(p[0], p[1], new_feat)].append((cand, tag))
            n_pa += 1

    # --- மார் : root + மார், with ல்/ள் nasalised. The விகுதி carries the future itself,
    # --- so the cell has no +fut= group.
    for root, (cls, feat) in frame.items():
        if not ok(root): continue
        rb = nasalize_final(T.encode(root))
        try: cand = T.decode(rb + MAAR)
        except T.TLP1Error: continue
        new_feat = re.sub(r'\+fut=[^+]+', '', feat)
        new_feat = new_feat[: new_feat.rfind("+")] + "+3ple=மார்"
        tag = "B" if V.get(cand, 0) >= MIN_ACT else "C"
        if tag == "B": promoted += 1
        extra[(root, cls, new_feat)].append((cand, tag))
        n_maar += 1

    with open(OUT, "w", encoding="utf-8") as o:
        for p in rows:
            o.write("\t".join(p) + "\n")
        for (root, cls, feat), pairs in sorted(extra.items()):
            seen, uniq = set(), []
            for s, tg in sorted(pairs):
                if s in seen: continue
                seen.add(s); uniq.append((s, tg))
            o.write(f"{root}\t{cls}\t{feat}\t{'|'.join(s for s, _ in uniq)}\t"
                    f"{'|'.join(t for _, t in uniq)}\n")
    print(f"  ப cells    : {len(set(k for k in extra if k[2].endswith('3ple=ப'))):,}"
          f"   surfaces {n_pa:,}")
    print(f"  மார் cells : {len(set(k for k in extra if k[2].endswith('3ple=மார்'))):,}"
          f"   surfaces {n_maar:,}")
    print(f"  promoted to B (n>={MIN_ACT}) : {promoted:,}")
    print(f"  -> {B.rel(OUT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
