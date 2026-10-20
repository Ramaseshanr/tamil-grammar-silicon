#!/usr/bin/env python3
"""
Add the top missing verb roots, assigning each a conjugation class FROM CORPUS EVIDENCE.

audit/LEXICON_GAP.md: 159 roots recover 80% of the 46% verb-token gap. The hard part is
not finding them, it is the class. DERIVABILITY.md §F showed conjugation class is only
81.3% predictable from phonology, because the residue is transitivity — so guessing from
the root's shape is the wrong instrument.

The corpus supplies the right one. A class IS its (past, present, future) marker triple,
and the corpus shows which markers a root actually takes:

    class    past        present          future
    C11/C12  த்          க்கின்ற்/க்கிற்  ப்ப்     strong
    C5       இன்         கின்ற்/கிற்      வ்       weak, இன்-past
    C4/C1    த்          கின்ற்/கிற்      வ்
    C2       ட்          கின்ற்/கிற்      வ்
    C3       ற்          கின்ற்/கிற்      வ்
    C7/C9    ட்          கின்ற்/கிற்      ப்
    C8/C10   ற்          கின்ற்/கிற்      ப்

Each candidate root is probed for these markers. A root is assigned only where the
evidence is unambiguous; anything else is left OUT and reported, because a wrongly
classed root generates a whole wrong paradigm and is worse than an absent one.

  data/derived/new_roots.tsv        root, class, evidence
  data/derived/new_roots_skipped.tsv
"""
import re, sys, glob, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

def wellformed(w):
    """A root must be encodable and must not end in a bare consonant-less vowel sign.
    String-slicing Tamil produced உருவாு in a first pass -- a vowel sign with no base."""
    try:
        b = T.encode(w)
    except T.TLP1Error:
        return False
    return len(b) >= 2 and (T.is_uyir(b[-1]) or T.is_mey(b[-1]))

# A compound verb conjugates like its HEAD, so the head's class is the evidence.
# padu is C6 (kaaNappaTTathu is a T-past), not the C5 that a bare "weak, past
# unattested" default would give it. Ordered longest-first.
HEADS = ["ப்படுத்து","படுத்து","ப்படு","படு","ப்பெறு","பெறு","விடு","கொள்",
         "இரு","எடு","ஆக்கு","ஆகு","வை","செல்","இடு","ஆற்று","காட்டு","அளி","செய்","கூறு"]

FREQ = ROOT / "data/gold/freq/tawiki_freq.tsv"
GRID = ROOT / "data/derived/verbs_grid_fixed.tsv"
SRC  = ROOT / "data/gold/thamizhi-morph/foma/src"
N    = int(sys.argv[1]) if len(sys.argv) > 1 else 159

PNG_ALL  = ["ேன்","ோம்","ாய்","ீர்கள்","ீர்","ான்","ாள்","து","ார்கள்","ார்","னர்","ன","அர்"]
PNG_SAFE = ["ேன்","ோம்","ாய்","ீர்கள்","ான்","ாள்","ார்கள்"]
ENDINGS = sorted({t+p for t in ["க்கின்ற","க்கிற","கின்ற","கிற"] for p in PNG_ALL}
                 | {t+p for t in ["ப்ப","வ"] for p in PNG_SAFE}, key=len, reverse=True)

def main():
    freq = {}
    for line in FREQ.read_text(encoding="utf-8").splitlines():
        w, c = line.split("\t"); freq[w] = int(c)
    roots = set()
    for f in glob.glob(str(SRC / "ThamizhiVerbs-*.lexc")):
        for m in re.finditer(r'^(\S+)\s+C[0-9A-Za-z]+Vinf\s*;',
                             pathlib.Path(f).read_text(encoding="utf-8"), re.M):
            roots.add(m.group(1))
    surfaces = set()
    for line in GRID.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) == 4: surfaces.update(p[3].split("|"))

    miss = collections.Counter()
    for w, c in freq.items():
        e = next((x for x in ENDINGS if w.endswith(x) and len(w) > len(x) + 1), None)
        if not e or w in surfaces: continue
        stem = w[: -len(e)]
        cands = {stem, stem + "ு", stem + "்"}
        if stem.endswith("க்"): cands |= {stem[:-2], stem[:-2] + "ு"}
        if not any(x in roots for x in cands): miss[stem] += c

    def probe(r, suf):
        """total corpus support for root+suffix, allowing the உ-drop"""
        t = freq.get(r + suf, 0)
        if r.endswith("ு"): t += freq.get(r[:-1] + suf, 0)
        return t

    headcls = {}
    for f in glob.glob(str(SRC / "ThamizhiVerbs-*.lexc")):
        for m in re.finditer(r'^(\S+)\s+(C[0-9A-Za-z]+)Vinf\s*;',
                             pathlib.Path(f).read_text(encoding="utf-8"), re.M):
            headcls.setdefault(m.group(1), m.group(2))

    out, skip = [], []
    for stem, toks in miss.most_common(N * 4):
        if len(out) >= N: break
        # build a WELL-FORMED root; try the plain stem, +உ (consonant-final) and +கு
        # Candidate order matters. A stem ending in a LONG vowel usually lost a
        # consonant to the ending (உருவாகிறது -> உருவா, root உருவாகு), while one
        # ending in short உ is usually already complete (வருகிறது -> வரு, root வரு).
        # Picking the first well-formed candidate blindly gave உருவா as a "root".
        try:
            _b = T.encode(stem); _long = T.is_uyir(_b[-1]) and T.is_nedil(_b[-1])
        except T.TLP1Error:
            _long = False
        order = (stem + "கு", stem, stem + "ு") if _long else (stem, stem + "ு", stem + "கு")
        r = next((c for c in order if wellformed(c)), None)
        if r is None:
            skip.append((stem, toks, "no well-formed root")); continue

        # compound? inherit the head's class -- stronger evidence than any probe
        # the head must BE a lexicon root; ப்படு matches but is not one, படு is
        # Match the head in TLP1, NOT as a Unicode string. குறிப்பிடு does not
        # string-end with இடு, because that இ is the dependent sign ி on ப -- the
        # same trap that has now bitten this project four times. In phonemes the
        # suffix is exact.
        rb = T.encode(r)
        head = None
        for h in HEADS:
            if h not in headcls: continue
            hb = T.encode(h)
            if len(rb) > len(hb) and rb[-len(hb):] == hb: head = h; break
        if head:
            out.append((r, headcls[head], toks, f"compound, head {head} -> {headcls[head]}"))
            continue
        pres_w = probe(r, "கிறது") + probe(r, "கின்றது") + probe(r, "கிறார்")
        pres_s = probe(r, "க்கிறது") + probe(r, "க்கின்றது") + probe(r, "க்கிறார்")
        fut_w  = probe(r, "வது") + probe(r, "வார்")
        fut_s  = probe(r, "ப்பது") + probe(r, "ப்பார்")
        past = {"இன்": probe(r, "ியது") + probe(r, "ினார்") + probe(r, "ின"),
                "த்":  probe(r, "ந்தது") + probe(r, "த்தது") + probe(r, "ந்தார்") + probe(r, "த்தார்"),
                "ட்":  probe(r, "ட்டது") + probe(r, "ட்டார்"),
                "ற்":  probe(r, "ற்றது") + probe(r, "ற்றார்")}
        pm, pv = max(past.items(), key=lambda x: x[1])
        strong = pres_s > pres_w and fut_s >= fut_w
        weak   = pres_w > pres_s and fut_w >= fut_s
        ev = f"pres_w={pres_w} pres_s={pres_s} fut_w={fut_w} fut_s={fut_s} past={pm}:{pv}"
        if strong:
            out.append((r, "C11", toks, ev))
        elif weak and pv > 0:
            cls = {"இன்": "C5", "த்": "C4", "ட்": "C2", "ற்": "C3"}[pm]
            out.append((r, cls, toks, ev))
        elif weak and (pres_w + fut_w) >= 20 and not T.is_mey(T.encode(r)[-1]):
            # C5 is the உ-final இன்-past class, so a consonant-final root cannot
            # default into it. நிற், கேட், ஏற், பங்கேற் were being assigned C5.
            out.append((r, "C5", toks, ev + "  [past unattested, weak default C5]"))
        else:
            skip.append((r, toks, ev))

    (ROOT / "data/derived/new_roots.tsv").write_text(
        "".join(f"{r}\t{c}\t{t}\t{e}\n" for r, c, t, e in out), encoding="utf-8")
    (ROOT / "data/derived/new_roots_skipped.tsv").write_text(
        "".join(f"{r}\t{t}\t{e}\n" for r, t, e in skip), encoding="utf-8")
    byc = collections.Counter(c for _, c, _, _ in out)
    print(f"roots assigned : {len(out)}   covering {sum(t for _,_,t,_ in out):,} tokens")
    print(f"  by class     : {dict(byc.most_common())}")
    print(f"roots skipped  : {len(skip)}   (ambiguous evidence, left out deliberately)")
    print(f"\ntop assignments:")
    for r, c, t, e in out[:18]:
        print(f"  {r:<20} {c:<5} {t:>7,}   {e}")

if __name__ == "__main__":
    main()
