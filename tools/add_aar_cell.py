#!/usr/bin/env python3
"""
Add the missing 3sghe=ஆர் cell -- the singular honorific -- to the classes that lack it.

audit/STEM_ALTERNATION.md left வந்தார் (7,371 tokens) and வருகிறார் (7,338) unreachable.
Neither is a stem-alternation problem: வந்தது and வந்தனர் are both generated. The
singular honorific PNG cell is simply absent from most class lists.

    classes WITH 3sghe=ஆர்   C1 C2 C3 C5 C11                    5
    classes WITHOUT          C4 C6 C7 C8 C9 C10 C12 C13-C18    13

The cell is mechanical: every class already carries 3sghe=ஆர்கள், and the honorific
singular is that minus கள், in both the tag and the surface —

    +...+3sghe%=ஆர்கள்:^ந்தார்கள் #;      ->   +...+3sghe%=ஆர்:^ந்தார் #;

which is exactly how C5 (which has it) is written. Verified in TLP1 that the trailing
கள் is [க அ ள்] and strips cleanly.

  python3 tools/add_aar_cell.py <builddir>
"""
import re, sys, pathlib, collections

ROOT  = pathlib.Path(__file__).resolve().parent.parent
BUILD = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/tamilos-build")

def main():
    added = collections.Counter()
    for path in sorted(BUILD.glob("ThamizhiVerbs-*.lexc")):
        txt = path.read_text(encoding="utf-8")
        out = []; changed = False
        # walk block by block so a cell is only added to classes that lack it
        blocks = re.split(r'(^LEXICON \S+\s*$)', txt, flags=re.M)
        for i, part in enumerate(blocks):
            m = re.match(r'^LEXICON (C[0-9A-Za-z]+)Vinf\s*$', part.strip()) if part.strip().startswith("LEXICON") else None
            out.append(part)
            if not m: continue
            cls = m.group(1)
            body = blocks[i+1] if i+1 < len(blocks) else ""
            if re.search(r'\+3sghe%=ஆர்:', body):      # already has it
                continue
            lines = body.splitlines()
            have = {l.split(":",1)[1].strip() for l in lines if ":" in l}
            new = []
            for l in lines:
                g = re.match(r'^(\+verb\S*?\+3sghe%=ஆர்)கள்:\^(\S*?)கள்(\s*#\s*;)', l)
                if g:
                    cand = f"{g.group(1)}:^{g.group(2)}{g.group(3)}"
                    if cand.split(":",1)[1].strip() not in have:
                        new.append(cand); added[cls] += 1
            if new:
                blocks[i+1] = body.rstrip("\n") + "\n" + "\n".join(new) + "\n"
                changed = True
        if changed:
            path.write_text("".join(blocks[:1] + [x for pair in zip(blocks[1::2], blocks[2::2]) for x in pair]
                                    if len(blocks) > 1 else blocks), encoding="utf-8")
    for c, n in sorted(added.items(), key=lambda x: -x[1]):
        print(f"  {c:<8} +{n} cells")
    print(f"\n  total cells added: {sum(added.values())}  across {len(added)} classes")

if __name__ == "__main__":
    main()
