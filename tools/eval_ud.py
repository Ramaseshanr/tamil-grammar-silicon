#!/usr/bin/env python3
"""
Independent evaluation: the phonemic noun derivation against UD Tamil.

Every other number for the derivation is measured against a gold we audited and corrected
ourselves. data/gold/UD_Tamil-{TTB,MWTT} is externally annotated and NO noun parameter was
ever fitted on it -- the only tools that read it are validate_tlp1.py (round-trip) and
morph_tokenizer.py (evaluation), both read-only. Two separate treebanks, so there is
internal replication.

UD gives (lemma, Case, Number, form). We map the case to our feature bundle, derive from
the lemma, and ask whether UD's form is among the surfaces the rules license.

A UD token in running text may carry pada sandhi -- நிலையத்துக்குக்க் -- so the base bundle
and its +sandhi{k,c,p,t} variants are all accepted. CC BY-NC-SA 3.0.

    python3 tools/eval_ud.py            # report
    python3 tools/eval_ud.py --misses   # also list what it got wrong
"""
import sys, re, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import phon_rules as P
import tlp1 as T

GOLD = ROOT / "data/gold"
GRID = ROOT / "data/derived/nouns_grid_final.tsv"

# UD Case -> our bundle.  Com is a judgement, not an identity: UD's comitative is nearest
# to our `soc` (ஓடு/உடன்) and is counted separately so it can be discounted.
CASE = {"Nom": "nom", "Acc": "acc", "Dat": "dat", "Gen": "gen", "Loc": "loc",
        "Ins": "inst", "Abl": "abl", "Ben": "dat+ben", "Com": "soc"}
JUDGED = {"Com"}
SANDHI = ("", "+sandhik", "+sandhic", "+sandhip", "+sandhit")

def stem_classes():
    """lemma -> every class the lexicon declares it in.

    A stem can be declared in more than one class (19 are -- கடல் is in both C4 and C15),
    and the reference grid is the union over them. Taking only the first, as this once
    did, scored கடலில் as a miss when it is simply the C4 form."""
    _, stems = P.load_lexc()
    m = {k: set(v) for k, v in stems.items()}
    with open(GRID, encoding="utf-8") as f:
        for line in f:
            p = line.split("\t", 3)
            if len(p) < 3: continue
            m.setdefault(p[0], set()).add(re.sub(r"(Sg|pl)Root$", "", p[1]))
    return m

def ud_items():
    out = set()
    for f in sorted(list((GOLD/"UD_Tamil-TTB").glob("*.conllu"))
                    + list((GOLD/"UD_Tamil-MWTT").glob("*.conllu"))):
        for line in f.read_text(encoding="utf-8").splitlines():
            p = line.split("\t")
            if len(p) < 6 or p[3] not in ("NOUN", "PROPN"): continue
            form, lemma, feats = p[1], p[2], p[5]
            d = dict(x.split("=", 1) for x in feats.split("|") if "=" in x)
            c = d.get("Case")
            if not c: continue
            out.add((lemma, c, d.get("Number", "Sing"), form, f.name))
    return out

def main():
    show = "--misses" in sys.argv
    cls = stem_classes()
    items = ud_items()
    print(f"  UD items: {len(items):,} unique (lemma, Case, Number, form)")

    by = collections.Counter(); hit = collections.Counter()
    nolemma = nocase = 0
    misses = []
    for lemma, case, num, form, src in sorted(items):
        if case not in CASE: nocase += 1; continue
        cs = [c for c in (cls.get(lemma) or ()) if c in P.STEMFORM]
        if not cs: nolemma += 1; continue
        base = "noun+" + ("pl+" if num == "Plur" else "") + CASE[case]
        got = set()
        for c in cs:
            for s in SANDHI:
                r = P.derive(lemma, c, base + s)
                if r: got |= r
        by[case] += 1
        if form in got: hit[case] += 1
        elif len(misses) < 4000: misses.append((lemma, case, num, form, sorted(got)[:3]))

    tot = sum(by.values()); ok = sum(hit.values())
    print(f"  testable: {tot:,}   (lemma not in our inventory: {nolemma:,}; "
          f"case unmapped: {nocase:,})")
    print(f"\n  AGREEMENT  {ok:,} / {tot:,} = {100*ok/max(tot,1):.2f}%\n")
    print(f"  {'case':8s} {'n':>6} {'hit':>6} {'%':>7}")
    for c, n in by.most_common():
        mark = "  (mapping is a judgement)" if c in JUDGED else ""
        print(f"  {c:8s} {n:6d} {hit[c]:6d} {100*hit[c]/n:6.1f}%{mark}")
    strict_t = sum(n for c, n in by.items() if c not in JUDGED)
    strict_h = sum(hit[c] for c in by if c not in JUDGED)
    print(f"\n  excluding the judged mapping: {strict_h:,} / {strict_t:,} = "
          f"{100*strict_h/max(strict_t,1):.2f}%")
    if show:
        print(f"\n  misses ({len(misses)} shown)")
        for lemma, case, num, form, got in misses[:40]:
            print(f"    {lemma:16s} {case:4s} {num:5s}  UD {form:24s} derived {got}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
