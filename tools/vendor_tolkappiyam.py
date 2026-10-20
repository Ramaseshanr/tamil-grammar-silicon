#!/usr/bin/env python3
"""
Vendor Tolkāppiyam Eḻuttatikāram, பிறப்பியல் — the chapter on how sounds are produced.

docs/METHOD.md ranks Tolkāppiyam with Naṉṉūl at rank 1, but only Naṉṉūl was vendored,
so Tolkāppiyam could be named and never quoted. This fixes that for the one chapter this
project actually reasons from: பிறப்பியல் is where the place of articulation is set out,
and Naṉṉūl 79 is its descendant.

Source: Project Madurai pmuni0100, "தொல்காப்பியர் அருளிய தொல்காப்பியம்", a plain numbered
text with no commentary. Its header states: "You are welcome to freely distribute this
file, provided this header page is kept intact." The header is preserved verbatim in the
output, and Tolkāppiyam itself is ancient and in the public domain.

    python3 tools/vendor_tolkappiyam.py <downloaded.html>
"""
import sys, re, html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

OUT = ROOT / "data/gold/tolkappiyam"
SRC_URL = "https://www.projectmadurai.org/pm_etexts/utf8/pmuni0100.html"

def strip_tags(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(p|div|h\d|tr|li)>", "\n", s, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", s))

def main(path):
    raw = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    text = strip_tags(raw)
    lines = [l.rstrip() for l in text.split("\n")]

    # Chapter headings appear twice: once in the table of contents near the top
    # ("1.3 --  பிறப்பியல்") and once in the body ("1.3. பிறப்பியல்"). Take the body one,
    # which is the last occurrence, and run to the next body heading.
    HEAD = re.compile(r"^\s*\d\.\d+\s*[-–.]*\s*\S")
    heads = [i for i, l in enumerate(lines) if HEAD.match(l)]
    toc_end = max((i for i in heads if i < 120), default=0)
    body_heads = [i for i in heads if i > toc_end]
    beg = next((i for i in body_heads if "பிறப்பியல்" in lines[i]), None)
    if beg is None:
        sys.exit("பிறப்பியல் body heading not found")
    end = next((i for i in body_heads if i > beg), len(lines))
    heading = lines[beg].strip()
    body = lines[beg + 1:end]
    print(f"  chapter heading   : {heading!r}   lines {beg}-{end}")

    # a nūṟpā ends at a line whose last token is its number
    nurpa, cur = [], []
    for l in body:
        s = l.strip()
        if not s: continue
        m = re.search(r"(\d{1,3})\s*$", s)
        if m and re.search(r"[஀-௿]", s):
            cur.append(re.sub(r"\s*\d{1,3}\s*$", "", s).strip())
            nurpa.append({"n": int(m.group(1)),
                          "lines": [x for x in cur if x]})
            cur = []
        else:
            cur.append(s)

    # every line must be well-formed Tamil under TLP1
    bad = []
    for v in nurpa:
        for ln in v["lines"]:
            for tok in ln.split():
                t = tok.strip(".,;:()[]‘’“”")
                if not t or not re.search(r"[஀-௿]", t): continue
                try: T.encode(t)
                except T.TLP1Error: bad.append((v["n"], t))

    hdr = "\n".join(l.strip() for l in lines[:60] if l.strip())[:1400]
    OUT.mkdir(parents=True, exist_ok=True)
    doc = {"work": "தொல்காப்பியம்", "atikaram": "எழுத்ததிகாரம்", "iyal": "பிறப்பியல்",
           "heading_verbatim": heading,
           "source": SRC_URL,
           "source_note": "Project Madurai etext pmuni0100, plain numbered nūṟpā, no "
                          "commentary. Freely distributable with the header kept intact; "
                          "the header is reproduced below. Tolkāppiyam is ancient and in "
                          "the public domain.",
           "header_verbatim": hdr,
           "count": len(nurpa), "nurpa": nurpa}
    (OUT / "pirappiyal.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  nūṟpā parsed      : {len(nurpa)}")
    print(f"  numbering         : {min(v['n'] for v in nurpa)}–{max(v['n'] for v in nurpa)}")
    print(f"  non-Tamil tokens  : {len(bad)}" + (f"  {bad[:4]}" if bad else "  (all clean)"))
    print(f"  written           : {OUT.relative_to(ROOT)}/pirappiyal.json")
    for v in nurpa[:2]:
        print(f"\n  {v['n']}. " + " / ".join(v["lines"]))

if __name__ == "__main__":
    main(sys.argv[1])
