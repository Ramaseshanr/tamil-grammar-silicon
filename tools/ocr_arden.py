#!/usr/bin/env python3
"""
Re-OCR Arden 1910's Tamil with a Tamil engine.

`data/gold/arden1910/README.md` records why this was needed: archive.org's own OCR
recovers Arden's English prose cleanly and DESTROYS the Tamil script -- மரம் comes out as
`tcTti`, மரத்தில் as `LDJpjsleo` -- because it was never run with a Tamil model. That left
Arden usable as a statement of the rules but useless as a source of FORMS, and forms are
what a second external gold would have to supply.

This fixes that. Full-resolution page images come from archive.org's IIIF endpoint (the
PDF's own images are 634x1020, far too low), and tesseract runs with `tam+eng`.

Scored with the project's two standing oracles, exactly as tools/bamini.py is:

  tlp1.encode()  rejects malformed Tamil -- does the output look like script at all
  tawiki_freq    807,232 real word types -- is it the RIGHT words

  python3 tools/ocr_arden.py --leaves 39-51      fetch, OCR and score those leaves
  python3 tools/ocr_arden.py --psm-sweep 43      pick --psm by the vocabulary oracle
"""
import os, re, sys, json, pathlib, subprocess, urllib.request, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

ITEM = "progressivegramm00ardeiala"
IIIF = "https://iiif.archive.org/iiif/{item}%24{leaf}/full/full/0/default.jpg"
CACHE = pathlib.Path(os.environ.get(
    "TAMILOS_OCR_CACHE",
    "/private/tmp/claude-501/-Users-ram-Documents-GitHub-TamilOS/"
    "ff6ace7a-15e7-42ff-84e7-5b1c02b90e9f/scratchpad/arden_leaves"))

def leaf_image(n):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"leaf{n}.jpg"
    if p.exists() and p.stat().st_size > 10000:
        return p
    url = IIIF.format(item=ITEM, leaf=n)
    req = urllib.request.Request(url, headers={"User-Agent": "TamilOS-research/1.0"})
    try:
        p.write_bytes(urllib.request.urlopen(req, timeout=180).read())
    except Exception as e:
        print(f"    leaf {n}: fetch failed ({e})"); return None
    return p

def ocr(img, psm=6, lang="tam+eng"):
    out = img.with_suffix("")
    r = subprocess.run(["tesseract", str(img), str(out), "-l", lang, "--psm", str(psm)],
                       capture_output=True, text=True, timeout=300)
    txt = out.with_suffix(".txt")
    return txt.read_text(encoding="utf-8", errors="replace") if txt.exists() else ""

_V = None
def vocab():
    global _V
    if _V is None:
        _V = set()
        f = ROOT / "data/gold/freq/tawiki_freq.tsv"
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    q = line.rstrip("\n").split("\t")
                    if q: _V.add(q[0])
    return _V

def wf(w):
    try: T.encode(w); return True
    except T.TLP1Error: return False

def score(text):
    toks = [w for w in re.findall(r'[஀-௿]+', text) if len(w) > 1]
    if not toks: return dict(tokens=0, wf=0.0, inv=0.0)
    V = vocab()
    return dict(tokens=len(toks),
                wf=100 * sum(1 for w in toks if wf(w)) / len(toks),
                inv=100 * sum(1 for w in toks if w in V) / len(toks) if V else 0.0)

def parse_range(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out

def main():
    a = sys.argv[1:]
    if not a: print(__doc__.strip()); return 2

    if a[0] == "--psm-sweep":
        n = int(a[1]); img = leaf_image(n)
        if not img: return 1
        print(f"  leaf {n}: picking --psm by the vocabulary oracle")
        best = None
        for psm in (3, 4, 6, 11, 12):
            s = score(ocr(img, psm))
            print(f"    psm {psm:>2}: {s['tokens']:>4} tokens   "
                  f"well-formed {s['wf']:5.1f}%   in vocab {s['inv']:5.1f}%")
            if best is None or s["inv"] > best[1]["inv"]: best = (psm, s)
        print(f"  best: psm {best[0]}")
        return 0

    if a[0] == "--leaves":
        leaves = parse_range(a[1])
        psm = int(os.environ.get("TAMILOS_PSM", "6"))
        agg = collections.Counter()
        texts = {}
        for n in leaves:
            img = leaf_image(n)
            if not img: continue
            t = ocr(img, psm)
            texts[n] = t
            s = score(t)
            agg["tokens"] += s["tokens"]
            agg["wf"] += s["wf"] * s["tokens"] / 100
            agg["inv"] += s["inv"] * s["tokens"] / 100
            print(f"    leaf {n:>3}: {s['tokens']:>4} Tamil tokens   "
                  f"well-formed {s['wf']:5.1f}%   in vocab {s['inv']:5.1f}%")
        tot = agg["tokens"] or 1
        print(f"\n  TOTAL {agg['tokens']:,} Tamil tokens   "
              f"well-formed {100*agg['wf']/tot:.1f}%   in vocab {100*agg['inv']/tot:.1f}%")
        out = ROOT / "data/gold/arden1910/ocr_tamil.json"
        out.write_text(json.dumps(
            {"item": ITEM, "engine": f"tesseract tam+eng --psm {psm}",
             "images": "archive.org IIIF, full resolution (~340 dpi)",
             "leaves": {str(k): v for k, v in sorted(texts.items())},
             "score": {"tokens": agg["tokens"],
                       "well_formed_pct": round(100*agg['wf']/tot, 1),
                       "in_vocab_pct": round(100*agg['inv']/tot, 1)}},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  written: {out.relative_to(ROOT)}")
        return 0
    print(__doc__.strip()); return 2

if __name__ == "__main__":
    sys.exit(main())
