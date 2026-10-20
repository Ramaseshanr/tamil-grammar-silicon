#!/usr/bin/env python3
"""
Stem alternation: வரு in the past, ஆகு in the present.

audit/ADD_ROOTS.md measured that the added roots reach only 84.2% of their own attested
forms, because a conjugation class models the SUFFIX series and not stem alternation.
Two patterns carry most of that loss, and they turn out to be the same operation --
delete the root's final consonant + உ:

    வரு + past    வருந்தது  ->  வந்தது      [வ்,அ,ர்,உ] -> [வ்,அ]     + ந்தது
    ஆகு + present ஆகுகிறது ->  ஆகிறது      [ஆ,க்,உ]   -> [ஆ]        + கிறது
    ஆகு + past    ஆகினது    ->  ஆனது        [ஆ,க்,உ]   -> [ஆ]        + னது

Corpus is unambiguous on both:
    வந்தது     9,537  /  வருந்தது      0
    வந்தார்    7,371  /  வருந்தார்      2
    ஆகிறது       386  /  ஆகுகிறது      0
    ஆகிறார்       98  /  ஆகுகிறார்     0

Note ஆகு is an ORIGINAL ThamizhiMorph root, not one of the 159 added here -- so
ஆகுகிறது is a pre-existing defect, not something these additions introduced.

The corrected surface is added and the contradicted one removed, since the counts
leave no doubt. Never empties a cell.

  data/derived/verbs_grid_alt.tsv  +  data/derived/stem_alt.log
"""
import re, os, sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import buildcheck as B

SRC = ROOT / os.environ.get("TAMILOS_VGRID", "data/derived/verbs_grid_v3_fixed.tsv")
OUT = ROOT / os.environ.get("TAMILOS_VOUT", "data/derived/verbs_grid_alt.tsv")
LOG = ROOT / "data/derived/stem_alt.log"

# (root suffix, which tense the alternation applies in)
RULES = [("வரு", "past"),     # வருந்தது  -> வந்தது    (suppletive with வா)
         ("ஆகு", "pres"),     # ஆகுகிறது -> ஆகிறது
         ("ஆகு", "past")]     # ஆகினது   -> ஆனது      (past stem ஆன், corpus 4,814 vs 0)

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

def main():
    rules = [(enc(r), t) for r, t in RULES]
    n_add = n_del = 0; log = []; touched = collections.Counter()
    with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as o:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 4: continue
            root, cls, feat, surfs = p[0], p[1], p[2], p[3].split("|")
            # the register column, if present. Kept aligned to the surfaces by name, not
            # by position, because this script adds and removes surfaces.
            tags = p[4].split("|") if len(p) >= 5 else []
            tagof = dict(zip(surfs, tags)) if len(tags) == len(surfs) else {}
            default_tag = tags[0] if tags else "B"
            rb = enc(root)
            if rb:
                for pat, tense in rules:
                    # rb may EQUAL pat -- வரு and ஆகு are themselves the pattern, and
                    # an earlier guard of len(rb) > len(pat)+1 excluded exactly the two
                    # base roots this fix exists for. Only require that deleting two
                    # phonemes leaves something.
                    if not pat or len(rb) < len(pat) or len(rb) < 3: continue
                    if rb[-len(pat):] != pat: continue
                    if f"+{tense}=" not in feat: continue
                    new = []
                    cut = len(rb) - 2          # delete the two phonemes at cut, cut+1
                    for s in surfs:
                        sb = enc(s)
                        # Delete by POSITION, not by stripping a root prefix. ஆகினது
                        # does not start with ஆகு -- the உ has already been replaced by
                        # the இ of இன் -- so a prefix test silently skipped every past
                        # form and only the present got fixed. What is constant is the
                        # position: the root's final consonant and the phoneme after it.
                        #   ஆகு  pres  ஆகுகிறது [ஆ,க்,உ,க்,இ,ற்,அ,த்,உ] -> cut 1,2 -> ஆகிறது
                        #   ஆகு  past  ஆகினது   [ஆ,க்,இ,ன்,அ,த்,உ]      -> cut 1,2 -> ஆனது
                        #   வரு  past  வருந்தது [வ்,அ,ர்,உ,ன்,த்,அ,த்,உ] -> cut 2,3 -> வந்தது
                        if sb and len(sb) > len(rb) and sb[:cut] == rb[:cut]:
                            cand = T.decode(sb[:cut] + sb[cut+2:])
                            if cand not in new:
                                new.append(cand); n_add += 1
                                if len(log) < 3000: log.append(f"+\t{root}\t{feat}\t{s} -> {cand}")
                            n_del += 1
                            touched[root] += 1
                        else:
                            new.append(s)
                    if new: surfs = new
                    break
            uniq = sorted(set(surfs))
            o.write(f"{root}\t{cls}\t{feat}\t{'|'.join(uniq)}\t"
                    f"{'|'.join(tagof.get(x, default_tag) for x in uniq)}\n")
    LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"  surfaces rewritten : {n_add:,}")
    print(f"  roots touched      : {len(touched)}")
    print(f"  top: {dict(touched.most_common(6))}")
    print(f"  -> {B.rel(OUT)}")

if __name__ == "__main__":
    main()
