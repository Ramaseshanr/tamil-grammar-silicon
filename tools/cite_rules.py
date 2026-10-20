#!/usr/bin/env python3
"""
Attach nūṟpā citations to the fitted rule parameters.

audit/ADD_ROOTS.md's accounting made the gap explicit: the noun model derives 1.52M
cells from 1,265 parameters, but those parameters were FITTED against the FST, not read
out of a grammar. SanskritOS's vyutpatti cites a sūtra per step; this did not.

This attaches what can honestly be attached. Each citation below was read from the
UHH-Tamilex TEI edition of Naṉṉūl and is recorded with its nūṟpā id, so a derivation
step can name its authority instead of saying "fitted".

  Naṉṉūl Collatikāram
    C034   the cases are EIGHT
    C035   the master list: peyar / ai / āl / ku / iṉ / atu / kaṇ / viḷi
    C039   2nd case urupu = ஐ                    (accusative)
    C040   3rd case urupu = ஆல், ஆன், ஓடு, ஒடு   (instrumental, sociative)
    C041   4th case urupu = கு                   (dative)
    C0042  5th case urupu = இன், இல்             (ablative)
    C0043  6th case urupu = அது, ஆது sg; அ pl    (genitive)
    C0044  7th case urupu = கண் and others       (locative)
    C0045  the locative markers enumerated, including இல் and இடம்
  Naṉṉūl Eḻuttatikāram
    E0242  a cāriyai may come, may be absent, or may VARY -- the authority for
           why the model needs alternants at all
    E0243  the general cāriyai list: அன் ஆன் இன் அல் அற்று இற்று அத்து அம் ...
    E0181-2  ṭa/ṟa double before a case ending (already applied, audit/NANNUL.md)
    E0226  la/ḷa -> ṟa/ṭa in a case relation, uṟaḻvu in alvaḻi

Output: data/derived/noun_rules_cited.json, and a coverage report.
"""
import sys, json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

RULES = ROOT / "data/derived/noun_rules_paired.json"
OUT   = ROOT / "data/derived/noun_rules_cited.json"

# marker (as TLP1-decoded text) -> citation
MARKER_CITE = {
    "ஐ":    ("Naṉṉūl Collatikāram 39 (Tamilex ed.)", "2nd case urupu ai"),
    "ஆல்":  ("Naṉṉūl Collatikāram 40 (Tamilex ed.)", "3rd case urupu āl"),
    "ஆன்":  ("Naṉṉūl Collatikāram 40 (Tamilex ed.)", "3rd case urupu āṉ"),
    "ஓடு":  ("Naṉṉūl Collatikāram 40 (Tamilex ed.)", "3rd case urupu ōṭu"),
    "ஒடு":  ("Naṉṉūl Collatikāram 40 (Tamilex ed.)", "3rd case urupu oṭu"),
    "உடன்": ("Naṉṉūl Collatikāram 40 (Tamilex ed.)", "sociative, oṭu series"),
    "கு":   ("Naṉṉūl Collatikāram 41 (Tamilex ed.)", "4th case urupu ku"),
    "உக்கு":("Naṉṉūl Collatikāram 41 (Tamilex ed.)", "4th case urupu ku, with euphonic உ"),
    "க்கு": ("Naṉṉūl Collatikāram 41 (Tamilex ed.)", "4th case urupu ku"),
    "இன்":  ("Naṉṉūl Collatikāram 42 (Tamilex ed.)", "5th case urupu iṉ"),
    "இல்":  ("Naṉṉūl Collatikāram 42/45 (Tamilex ed.)", "5th case urupu il; also locative il"),
    "அது":  ("Naṉṉūl Collatikāram 43 (Tamilex ed.)", "6th case urupu atu, singular"),
    "ஆது":  ("Naṉṉūl Collatikāram 43 (Tamilex ed.)", "6th case urupu ātu, singular"),
    "இடம்": ("Naṉṉūl Collatikāram 45 (Tamilex ed.)", "locative urupu iṭam"),
    "கண்":  ("Naṉṉūl Collatikāram 44/45 (Tamilex ed.)", "7th case urupu kaṇ"),
    "இலிருந்து": ("Naṉṉūl Collatikāram 42 (Tamilex ed.)", "ablative il + irunthu"),
    "கள்":  ("Naṉṉūl Collatikāram 21 (Tamilex ed.)", "kaḷ, the plural suffix"),
    "∅":    ("Naṉṉūl Collatikāram 38 (Tamilex ed.)", "eḻuvāy urupu tiripil -- the nominative takes no urupu"),
    "ய்":   ("Naṉṉūl Eḻuttatikāram 161 (Tamilex ed.)", "uṭampaṭumey, the glide y"),
    "வ்":   ("Naṉṉūl Eḻuttatikāram 161 (Tamilex ed.)", "uṭampaṭumey, the glide v"),
    "உடன்": ("Naṉṉūl Collatikāram 40 (Tamilex ed.)", "sociative, oṭu series"),
    "டன்":  ("Naṉṉūl Collatikāram 40 (Tamilex ed.)", "sociative, oṭu series"),
    "ற்கள்":("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "la → ṟa before kaḷ"),
    "ட்கள்":("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "ḷa → ṭa before kaḷ"),
    "ங்கள்":("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "ma → ṅa before kaḷ"),
    "ர்கள்":("Arden §118", "ன் → ர், rational plural"),
    "ச்":   ("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "hard-consonant sandhi"),
    "ப்":   ("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "hard-consonant sandhi"),
    "த்":   ("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "hard-consonant sandhi"),
    "க்":   ("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "hard-consonant sandhi"),
}
# increment (decoded) -> citation
INC_CITE = {
    "∅":    ("Naṉṉūl Eḻuttatikāram 242 (Tamilex ed.)", "cāriyai tavirtal -- the increment may be absent"),
    "கள்":  ("Naṉṉūl Collatikāram 21 (Tamilex ed.)", "kaḷ, the plural suffix"),
    "க்கள்":("Naṉṉūl Collatikāram 21 (Tamilex ed.)", "kaḷ with hard-consonant sandhi, E0226"),
    "வ்":   ("Naṉṉūl Eḻuttatikāram 161 (Tamilex ed.)", "uṭampaṭumey, the glide v"),
    "ய்":   ("Naṉṉūl Eḻuttatikāram 161 (Tamilex ed.)", "uṭampaṭumey, the glide y"),
    "டு":   ("Naṉṉūl Eḻuttatikāram 181–182 (Tamilex ed.)", "ṭa before a case ending"),
    "த்த்": ("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai attu"),
    "அத்து":("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai attu"),
    "இன்":  ("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai iṉ"),
    "அன்":  ("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai aṉ"),
    "ஆன்":  ("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai āṉ"),
    "அற்று":("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai aṟṟu"),
    "இற்று":("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai iṟṟu"),
    "ற்ற்": ("Naṉṉūl Eḻuttatikāram 243 (Tamilex ed.)", "cāriyai aṟṟu"),
    "ண்":   ("Naṉṉūl Eḻuttatikāram 181–182 (Tamilex ed.)", "ṭa/ṟa gemination before a case ending"),
    "ட்":   ("Naṉṉūl Eḻuttatikāram 181–182 (Tamilex ed.)", "ṭa doubles before a case ending"),
    "ற்":   ("Naṉṉūl Eḻuttatikāram 181–182 (Tamilex ed.)", "ṟa doubles before a case ending"),
    "ங்கள்":("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "ம் before a hard consonant"),
    "ர்கள்":("Arden §118",   "ன் → ர், rational plural"),
    "ற்கள்":("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "la → ṟa before a hard consonant"),
    "ட்கள்":("Naṉṉūl Eḻuttatikāram 226 (Tamilex ed.)", "ḷa → ṭa before a hard consonant"),
}

def main():
    r = json.loads(RULES.read_text(encoding="utf-8"))
    def dec(h):
        try: return T.decode(bytes.fromhex(h)) if h else "∅"
        except Exception: return "?"

    cited = {"classifier": {}, "stemforms": {}, "markers": {}}
    stat = collections.Counter()

    for k, alts in r["stemforms"].items():
        entry = []
        for kk, h in alts:
            d = dec(h)
            c = INC_CITE.get(d)
            entry.append({"truncate": kk, "increment": d,
                          "cite": c[0] if c else None, "note": c[1] if c else "fitted"})
            stat["stemform cited" if c else "stemform fitted"] += 1
        cited["stemforms"][k] = entry

    for key, lst in r["markers"].items():
        out = []
        for h in lst:
            d = dec(h)
            c = MARKER_CITE.get(d)
            if not c:
                # Compound markers are built from cited parts, but the match MUST be
                # made in TLP1: இனை is இன் + ஐ, and does not string-start with இன்
                # because the ் becomes ை. Fifth occurrence of this trap.
                try: db = T.encode(d)
                except T.TLP1Error: db = None
                if db:
                    best = None
                    for m, cc in MARKER_CITE.items():
                        try: mb = T.encode(m)
                        except T.TLP1Error: continue
                        if len(db) > len(mb) and db[:len(mb)] == mb:
                            if best is None or len(mb) > best[0]: best = (len(mb), m, cc)
                    if best: c = (best[2][0], best[2][1] + f", extended ({best[1]} + …)")
            out.append({"marker": d, "cite": c[0] if c else None,
                        "note": c[1] if c else "fitted"})
            stat["marker cited" if c else "marker fitted"] += 1
        cited["markers"][key] = out

    cited["classifier_note"] = ("phonological contexts; the ṭu/ṟu ones implement "
                                "Naṉṉūl Eḻuttatikāram 181–182 (Tamilex ed.)'s kuṟṟiyalukaram taxonomy, the rest are fitted")
    OUT.write_text(json.dumps(cited, ensure_ascii=False), encoding="utf-8")

    sc, sf = stat["stemform cited"], stat["stemform fitted"]
    mc, mf = stat["marker cited"], stat["marker fitted"]
    print(f"  {'':<22}{'cited':>8}{'fitted':>8}{'% cited':>10}")
    print("  " + "-"*48)
    print(f"  {'stem-form increments':<22}{sc:>8}{sf:>8}{100*sc/max(sc+sf,1):>9.1f}%")
    print(f"  {'markers':<22}{mc:>8}{mf:>8}{100*mc/max(mc+mf,1):>9.1f}%")
    print("  " + "-"*48)
    print(f"  {'TOTAL':<22}{sc+mc:>8}{sf+mf:>8}{100*(sc+mc)/max(sc+mc+sf+mf,1):>9.1f}%")
    print(f"\n  written: {OUT.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
