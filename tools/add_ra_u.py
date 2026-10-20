#!/usr/bin/env python3
"""
The ர்-final உ alternant — Naṉṉūl Eḻuttatikāram 149.

> இணைந்தியல் காலை யரலக் கிகரமும் / மவ்வக் குகரமு நகரக் ககரமும் /
> மிசைவரும் **ரவ்வழி யுவ்வு மாம்** பிற

"in the environment of ர், உ also occurs." `ஆம்` is permissive, so a ர்-final root may take
a உ before the இடைநிலை and both forms are licensed — the same உறழ்வு shape as 226.

Raised by Arden 1910 (அமருகிறேன் / அமருவேன் against ThamizhiMorph's அமர்கிறேன் /
அமர்வேன், both agreeing on அமர்ந்தேன்) and adjudicated in `audit/ADJUDICATION.md`.

PRESENT AND FUTURE ONLY. Every one of the 81 attested variants is a pres or fut form —
கோருவது, சேருகிறது, வளருகின்றன, சேருகிறார், நகருகிறது, தொடருகின்றன. The past is not
affected: அமர்ந்தேன் is agreed by both sources, because before ந்த் the ர் assimilates
rather than taking a linking vowel.

TAGGED C, THEN PROMOTED. A nūṟpā licenses the form, so it is generated for every ர்-final
root — but the corpus decides which are modern standard. Default C (classical), promoted to
B at the established MIN_ACT=20 threshold. The corpus may promote and never demote, per
`docs/METHOD.md`; this is the same discipline as `tools/retag_by_corpus.py`.

  TAMILOS_VGRID=in.tsv TAMILOS_VOUT=out.tsv python3 tools/add_ra_u.py
"""
import os, re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import buildcheck as B

SRC = ROOT / os.environ.get("TAMILOS_VGRID", "data/derived/verbs_grid_final.tsv")
OUT = ROOT / os.environ.get("TAMILOS_VOUT", "data/derived/verbs_grid_rau.tsv")
FREQ = ROOT / "data/gold/freq/tawiki_freq.tsv"
MIN_ACT = int(os.environ.get("TAMILOS_MIN_ACT", "20"))   # same threshold as retag_by_corpus

RA = T.encode("ர்")[0]
U  = T.encode("உ")[0]
TENSE = re.compile(r'\+(pres|fut)=')

def ok(s):
    try: T.encode(s); return True
    except T.TLP1Error: return False

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
    added = promoted = rows_touched = 0
    skipped_prefix = 0
    roots_seen = set()
    with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as o:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                o.write(line); continue
            root, cls, feat, surfs = p[0], p[1], p[2], p[3].split("|")
            tags = p[4].split("|") if len(p) >= 5 else ["B"] * len(surfs)
            if len(tags) != len(surfs): tags = ["B"] * len(surfs)
            pairs = list(zip(surfs, tags))

            rb = T.encode(root) if ok(root) else None
            if rb and rb[-1] == RA and TENSE.search(feat):
                roots_seen.add(root)
                new = []
                for s, tg in pairs:
                    if not ok(s): continue
                    sb = T.encode(s)
                    # Operate on byte POSITIONS behind a verified prefix. The variant is
                    # the root's bytes, then உ, then the rest -- never a string slice:
                    # root[:-1] + "ரு" strips the pulli and yields உணரரு. See
                    # audit/ADJUDICATION.md on the seventh Unicode trap.
                    if sb[:len(rb)] != rb:
                        skipped_prefix += 1; continue
                    cand = T.decode(rb + bytes([U]) + sb[len(rb):])
                    if cand in surfs: continue
                    tag = "C"
                    if V.get(cand, 0) >= MIN_ACT:
                        tag = "B"; promoted += 1
                    new.append((cand, tag))
                if new:
                    rows_touched += 1
                    added += len(new)
                    pairs += new
            seen, uniq = set(), []
            for s, tg in sorted(pairs):
                if s in seen: continue
                seen.add(s); uniq.append((s, tg))
            o.write(f"{root}\t{cls}\t{feat}\t{'|'.join(s for s, _ in uniq)}\t"
                    f"{'|'.join(t for _, t in uniq)}\n")
    print(f"  ர்-final roots touched : {len(roots_seen):,}")
    print(f"  rows gaining a variant : {rows_touched:,}")
    print(f"  surfaces added         : {added:,}")
    print(f"    tagged C (licensed)  : {added - promoted:,}")
    print(f"    promoted B (n>={MIN_ACT})  : {promoted:,}")
    if skipped_prefix:
        print(f"  surfaces skipped (do not begin with the root): {skipped_prefix:,}")
    print(f"  -> {B.rel(OUT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
