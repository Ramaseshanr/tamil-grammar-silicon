#!/usr/bin/env python3
"""
Monosyllabic ன்-stems take plain கள் -- the last open item from ADJUDICATION.md.

The ன் → ர் plural is not sandhi. It is SUFFIX SUBSTITUTION: the masculine singular
-அன் replaced by the rational plural -அர் (மனித+அன் -> மனித+அர்+கள்). It therefore
applies only where the ன் IS that suffix. In a monosyllable the ன் belongs to the root
-- மன், கன், அன், மீன், பொன் -- so there is nothing to substitute and the plural is
plain கள்.

Measured over 12,929 ன்-final stems, class is 99.95% predictable from
(preceding vowel is அ) x (monosyllable?). ThamizhiMorph already has this right for
அ+ன் monosyllables (அன், கன், மன் -> C10, plain கள்); it is inconsistent only for the
18 non-அ monosyllables, where it emits பொர்கள், கோர்கள், மிர்கள், முர்கள்.

Corpus agrees where the evidence is clean: மீன்கள் 1968 / மீர்கள் 0, மான்கள் 570 /
மார்கள் 2, பொன்கள் 2 / பொர்கள் 0. (வார்கள், தேர்கள், கார்கள் are homographs of
strap/chariot/car, not plurals, so those counts are not evidence.)

Removes the ர்-substituted plural for monosyllabic ன்-stems. Never empties a cell.
"""
import sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

SRC = ROOT / "data/derived/nouns_grid_tagged2.tsv"
OUT = ROOT / "data/derived/nouns_grid_final.tsv"
LOG = ROOT / "data/derived/nstem_fix.log"
N = T.encode("ன்")[0]

def enc(s):
    try: return T.encode(s)
    except T.TLP1Error: return None

def main():
    out = []; removed = 0; log = []; stems = set()
    for line in SRC.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) < 4: continue
        stem, cls, feat = p[0], p[1], p[2]
        surfs = p[3].split("|")
        tags  = p[4].split("|") if len(p) > 4 else ["B"] * len(surfs)
        cnts  = p[5].split("|") if len(p) > 5 else ["0"] * len(surfs)
        b = enc(stem)
        if (b and b[-1] == N and sum(1 for x in b if T.is_uyir(x)) == 1
                and "+pl" in feat and len(tags) == len(surfs) == len(cnts)):
            rbase = b[:-1] + T.encode("ர்")        # the ர்-substituted stem
            bad = lambda x: (lambda u: u is not None and u[:len(rbase)] == rbase)(enc(x))
            keep = [i for i, s in enumerate(surfs) if not bad(s)]
            if not keep and surfs:
                # every licensed form was the wrong ர்-substituted one (கோன் -> கோர்கள்).
                # Removing them all would empty the cell, so REPLACE: rebuild each on the
                # plain stem before dropping the originals. Leaving கோர்கள் in place
                # because the cell would otherwise be empty is not an acceptable outcome.
                for i, s in enumerate(surfs):
                    u = enc(s)
                    if u is None: continue
                    cand = T.decode(b + u[len(rbase):])
                    if cand not in surfs:
                        surfs.append(cand); tags.append(tags[i]); cnts.append("0")
                keep = [i for i, s in enumerate(surfs) if not bad(s)]
            if keep and len(keep) < len(surfs):
                for i, s in enumerate(surfs):
                    if i not in keep:
                        removed += 1; stems.add(stem)
                        if len(log) < 2000: log.append(f"-\t{stem}\t{feat}\t{s}")
                surfs = [surfs[i] for i in keep]
                tags  = [tags[i]  for i in keep]
                cnts  = [cnts[i]  for i in keep]
        out.append("\t".join([stem, cls, feat, "|".join(surfs),
                              "|".join(tags), "|".join(cnts)]))
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"cells written    : {len(out):,} -> {OUT.relative_to(ROOT)}")
    print(f"surfaces removed : {removed:,}  across {len(stems)} stems")
    print(f"stems            : {', '.join(sorted(stems))}")

if __name__ == "__main__":
    main()
