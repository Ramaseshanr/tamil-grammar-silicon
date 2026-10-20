#!/usr/bin/env python3
"""
Re-tag the register on corpus evidence instead of provenance.

build_tagged_gold.py assigned B/C by where a surface came from: in ThamizhiMorph = B
(modern), added by Naṉṉūl 226 = C (classical only). audit/REGISTER.md flagged that as
imprecise. The corpus shows it is not merely imprecise but sometimes BACKWARDS:

    தோட்கள்  tagged B, occurs    0 times in 39M tokens
    தோள்கள்  tagged C, occurs   64 times
    கடற்கள்  tagged B-absent, 0;  கடல்கள் 213

So the tag is decided by attestation where attestation exists:

    either alternant attested  ->  attested one(s) B, unattested one C
    neither attested           ->  keep the provenance tag (no evidence either way)

Most gold stems are rare compounds that will never appear in an encyclopaedia, so the
"neither attested" case is the common one and must not be read as evidence of absence.

Corpus: Tamil Wikipedia (CC BY-SA 4.0), 39,061,503 tokens. Counts only, never text.
"""
import sys, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

GRID = ROOT / "data/derived/nouns_grid_tagged.tsv"
FREQ = ROOT / "data/gold/freq/tawiki_freq.tsv"
OUT  = ROOT / "data/derived/nouns_grid_tagged2.tsv"
LOG  = ROOT / "data/derived/retag.log"
# Evidence thresholds. A first version used MIN=2 and promoted அருள்கள் (n=3) over
# அருட்கள் (n=0) -- overturning Naṉṉūl 226 on three Wikipedia hits. It is wrong twice:
#
#   1. n=2..3 is noise. 62 of 120 promotions sat below n=10.
#   2. More importantly, ABSENCE IS NOT EVIDENCE. A nūṟpā licenses அருட்கள்; that the
#      plural of "grace" is missing from an encyclopaedia says nothing about grammar.
#      And அருள் demonstrably still mutates -- 994 tokens of அருட்- compounds
#      (அருட்பணி, அருட்தந்தை, அருட்சகோதரி).
#
# So the corpus may only act where one alternant is STRONGLY attested, and it may never
# unlicense a rule-derived form on absence alone.
MIN      = 5      # counts as attested -> B
MIN_ACT  = 20     # a cell is only re-tagged if some alternant reaches this

def main():
    freq = {}
    for line in FREQ.read_text(encoding="utf-8").splitlines():
        w, c = line.split("\t"); freq[w] = int(c)
    print(f"corpus forms: {len(freq):,}")

    flips = collections.Counter(); log = []; out = []
    for line in GRID.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) != 5: continue
        stem, cls, feat, surfs, tags = p[0], p[1], p[2], p[3].split("|"), p[4].split("|")
        if len(tags) != len(surfs): out.append(line); continue
        # ONLY the உறழ்வு alternant cells -- those carrying both a B and a C tag.
        # Elsewhere the comparison is meaningless: அகத்தியில் is ordinary modern Tamil
        # and absent from an encyclopaedia only because the word is rare, so treating
        # its absence as evidence would demote thousands of correct modern forms. A
        # first version of this script did exactly that: 14,777 wrong B->C flips.
        # PROMOTION ONLY. The register tag records GRAMMATICAL LICENSING per register;
        # corpus frequency is a different fact and belongs in its own column. Conflating
        # them is what produced the அருள்கள்/அருட்கள் error: n=3 in an encyclopaedia was
        # allowed to overturn Naṉṉūl 226 and unlicense a form the grammar derives.
        # The corpus can show that a classically-licensed form is ALSO in modern use
        # (C -> B). It cannot show that anything is ungrammatical.
        seen = [freq.get(s, 0) for s in surfs]
        new = [("B" if (t == "C" and c >= MIN_ACT) else t) for t, c in zip(tags, seen)]
        for s, o, n, c in zip(surfs, tags, new, seen):
            if o != n:
                flips[f"{o}->{n}"] += 1
                if len(log) < 4000: log.append(f"{o}->{n}\t{stem}\t{feat}\t{s}\tn={c}")
        tags = new
        out.append("\t".join([stem, cls, feat, "|".join(surfs), "|".join(tags),
                               "|".join(str(c) for c in seen)]))

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("  (6th column added: corpus count per surface)")
    LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    print(f"cells written: {len(out):,} -> {OUT.relative_to(ROOT)}")
    print("tag flips:")
    for k, v in flips.most_common(): print(f"  {k:<8}{v:>8,}")
    print(f"\nsamples:")
    for l in log[:8]: print("  " + l)

if __name__ == "__main__":
    main()
