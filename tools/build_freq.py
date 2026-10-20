#!/usr/bin/env python3
"""
Build a modern-Tamil word-frequency table from the Tamil Wikipedia dump.

audit/REGISTER.md flagged the one soft spot in the register split: the உறழ்வு
alternants in the ள் direction (தோள்கள் beside தோட்கள்) are tagged C — "classical
only" — although modern Tamil uses them freely. C currently means "not attested in
our modern source", and the only reason it means that is that the project had no
modern source. This supplies one.

Source : Tamil Wikipedia, tawiki-latest-pages-articles.xml.bz2
Licence: CC BY-SA 4.0 (Wikimedia). Attribution recorded in data/gold/freq/README.md.
         Only counts are kept, never the text.

Streams the bz2 so the dump is never fully decompressed to disk.

    python3 tools/build_freq.py <dump.xml.bz2>
"""
import bz2, re, sys, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT  = ROOT / "data/gold/freq"

TEXT   = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
STRIP  = [
    (re.compile(r"<ref[^>]*>.*?</ref>", re.S), " "),
    (re.compile(r"<[^>]+>"), " "),
    (re.compile(r"\{\{[^{}]*\}\}"), " "),
    (re.compile(r"\{\|.*?\|\}", re.S), " "),
    (re.compile(r"\[\[(?:[^\[\]|]*\|)?([^\[\]|]*)\]\]"), r"\1"),
    (re.compile(r"\[\[|\]\]|'''|''"), " "),
    (re.compile(r"https?://\S+"), " "),
]
TAMIL = re.compile(r"[஀-௿]+")

def clean(s):
    for pat, rep in STRIP:
        for _ in range(2):
            s2 = pat.sub(rep, s)
            if s2 == s: break
            s = s2
    return s

def main():
    dump = pathlib.Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    freq = collections.Counter()
    buf = ""; pages = 0; toks = 0
    with bz2.open(dump, "rt", encoding="utf-8", errors="replace") as f:
        for chunk in iter(lambda: f.read(4 << 20), ""):
            buf += chunk
            last = 0
            for m in TEXT.finditer(buf):
                body = clean(m.group(1))
                for w in TAMIL.findall(body):
                    freq[w] += 1; toks += 1
                pages += 1; last = m.end()
            buf = buf[last:]
            if len(buf) > (32 << 20): buf = buf[-(8 << 20):]
            if pages and pages % 20000 < 1:
                print(f"  pages {pages:,}  tokens {toks:,}  unique {len(freq):,}", flush=True)
    print(f"\npages {pages:,}   tokens {toks:,}   unique forms {len(freq):,}")

    # keep forms seen at least twice -- hapaxes are mostly OCR noise and proper nouns
    kept = {w: c for w, c in freq.items() if c >= 2}
    p = OUT / "tawiki_freq.tsv"
    with open(p, "w", encoding="utf-8") as fh:
        for w, c in sorted(kept.items(), key=lambda x: (-x[1], x[0])):
            fh.write(f"{w}\t{c}\n")
    print(f"kept (count>=2): {len(kept):,} -> {p.relative_to(ROOT)}")
    print(f"size: {p.stat().st_size/1048576:.1f} MB")

if __name__ == "__main__":
    main()
