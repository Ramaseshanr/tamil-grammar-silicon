#!/usr/bin/env python3
"""
Attach nūṟpā citations to the verb grid's person-number-gender suffixes.

`docs/METHOD.md` recorded the verb side as the project's largest piece of open debt:
**zero citations**, every decision settled by corpus frequency, which the precedence order
does not permit the corpus to do. This is the first instalment.

The nūṟpā below were located in Naṉṉūl Collatikāram via `tools/bamini.py` and the MS
University DJL12 volume, where each verse is printed immediately before its number. They
are cited by NUMBER against the Saiva Siddhanta Kazhagam edition, as AUTHORITY.md requires.

⚠️ The `gist` strings are NOT canonical wording. They come through the Bamini pipeline,
which `audit/BAMINI.md` measures at 99.6% well-formed but with visible residue inside
quoted verse (பவ்வ+ர், மரர்). They record WHICH nūṟpā and WHAT it governs, enough to cite
and to check against the print edition. Do not quote them as the text.

  python3 tools/cite_verbs.py            report coverage, write the json
  python3 tools/cite_verbs.py --uncited  list the uncited features by corpus weight
"""
import os, re, sys, json, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

GRID = ROOT / os.environ.get("TAMILOS_VGRID", "data/derived/verbs_grid_final.tsv")
OUT  = ROOT / "data/derived/verb_rules_cited.json"

ED = "Naṉṉūl (Saiva Siddhanta Kazhagam ed.; verse text from data/gold/nannul/nurpa.json)"
NURPA_JSON = ROOT / "data/gold/nannul/nurpa.json"

def canon():
    """Canonical verse text, by nūṟpā number. Supersedes the Bamini `gist` strings."""
    if not NURPA_JSON.exists(): return {}
    d = json.loads(NURPA_JSON.read_text(encoding="utf-8"))
    return {int(k): v for k, v in d["nurpa"].items()}

# nūṟpā -> what it licenses. `tags` are the project's own feature tags.
NURPA = {
    324: dict(gist="மூவைந்து இருமூன்று ஆறாய் முற்று வினைப்பதம்",
              governs="the enumeration of the 27 finite வினைமுற்று slots: three persons × "
                      "five pāl × three tenses. The paradigm skeleton itself.",
              tags=[]),
    325: dict(gist="அன் ஆன் இறுமொழி ஆண்பால் படர்க்கை",
              governs="3sg masculine படர்க்கை விகுதி: அன், ஆன்",
              tags=["3sgm=அன்", "3sgm=ஆன்", "euph=அன்"]),
    326: dict(gist="அள் ஆள் இறுதிமொழி பெண்பால் படர்க்கை",
              governs="3sg feminine படர்க்கை விகுதி: அள், ஆள்",
              tags=["3sgf=அள்", "3sgf=ஆள்"]),
    327: dict(gist="அர் ஆர் ப ஊர் அகரம் மார் ஈற்ற / பல்லோர் படர்க்கை மார் வினையொடு முடிமே",
              governs="plural epicene படர்க்கை விகுதி: அர், ஆர், ப, ஊர், அகரம், மார் — SIX, "
                      "not four. Licenses BOTH அர் and ஆர், which authorises the -ஆர் "
                      "honorific cell. (A Bamini reading gave only 'அர், ஆர், ப, மரர்'; "
                      "மரர் was residue for மார், and ஊர் and அகரம் were missed entirely. "
                      "The Project Madurai split text corrects it.) Of the six, only "
                      "அர் and ஆர் are generated: ப, ஊர் and மார் are classical with zero "
                      "genuine attestation, and ஊர்/மார் would collide with place names "
                      "and noun plurals -- see audit/ADJUDICATION.md.",
              tags=["3sge=அர்", "3sge=அனர்", "3ple=ஆர்", "3ple=ஆர்கள்",
                    "3sghe=ஆர்", "3sghe=ஆர்கள்", "3ple=ப", "3ple=மார்"]),
    328: dict(gist="து று டுக் குற்றியலுகர ஈற்ற ஒன்றன் படர்க்கை டுக் குறிப்பின் ஆகும்",
              governs="3sg neuter படர்க்கை விகுதி: து, று, டு — டு only in the குறிப்பு வினை",
              tags=["3sgn=அது", "3sgn=∅"]),
    329: dict(gist="அ ஆ ஈற்ற பலவின்பால் படர்க்கை ஆவே எதிர்மறைக் கண்ணதாகும்",
              governs="3pl neuter படர்க்கை விகுதி: அ, ஆ — ஆ only in the negative",
              tags=["3pln=அன", "3pln=∅"]),
    332: dict(gist="அம் ஆம் … எம் ஏம் ஒம் … தன்னொடு படுக்கும் தன்மைப் பன்மை",
              governs="1pl தன்மை விகுதி: அம், ஆம், எம், ஏம், ஓம்",
              tags=["1pl=ஓம்"]),
    333: dict(gist="செய்கு என் ஒருமையும் செய்கும் என் பன்மையும் வினையொடு முடியினும்",
              governs="1sg தன்மை விகுதி கு and 1pl கும்",
              tags=[]),
    335: dict(gist="ஐ ஆய் இகர ஈற்ற மூன்றும் ஏவலின் வருஉம் … ஒருமை முன்னிலை",
              governs="2sg முன்னிலை விகுதி: ஐ, ஆய், இ — and these serve the ஏவல் "
                      "(imperative) singular too",
              tags=["2sg=ஆய்", "2sg=∅", "imp=∅"]),
    337: dict(gist="இர் ஈர் ஈற்ற இரண்டும் இருதிணைப் பன்மை முன்னிலை மின் அவற்று ஏவல்",
              governs="2pl முன்னிலை விகுதி: இர், ஈர்; மின் in the ஏவல்",
              tags=["2sgh=ஈர்", "2pl=ஈர்கள்"]),
    338: dict(gist="க ய வ … த் ஒற்று ஈற்ற வியங்கோள் இயலும் இடம் பால் எங்கும்",
              governs="வியங்கோள் (optative) விகுதி க, ய, வ, த் — in every person and pāl",
              tags=["opt=க", "opt=க்க"]),
    # --- tense. These are in EḺUTTATIKĀRAM பதவியல், not Collatikāram, because the
    # --- இடைநிலை is morphophonemic. Found via the Wikisource canonical text.
    142: dict(gist="தடறவொற்று இன்னே ஐம்பால் மூவிடத்து இறந்த காலம் தரும் தொழில் இடைநிலை",
              governs="PAST tense இடைநிலை: the ஒற்று த், ட், ற் and இன் — in five pāl and "
                      "three persons. Exactly the project's past set ந்த்/ட்ட்/த்த்/ற்ற்/இன்.",
              tags=["past=த்", "past=ட்", "past=ற்", "past=இன்", "past=ந்த்",
                    "past=ட்ட்", "past=த்த்", "past=ற்ற்"]),
    143: dict(gist="ஆநின்று கின்று கிறு மூவிடத்தின் ஐம்பால் நிகழ்பொழுது அறை வினை இடைநிலை",
              governs="PRESENT tense இடைநிலை: ஆநின்று, கின்று, கிறு. The project has "
                      "கிற்/கின்ற்/க்கிற்/க்கின்ற்; ஆநின்று it does not generate.",
              tags=["pres=கிற்", "pres=கின்ற்", "pres=க்கிற்", "pres=க்கின்ற்"]),
    144: dict(gist="பவ்வ மூவிடத்து ஐம்பால் எதிர்பொழுது இசை வினை இடைநிலை ஆம் இவை சிலவில",
              governs="FUTURE tense இடைநிலை: ப், வ் — in five pāl and three persons, and "
                      "'these are sometimes absent', which is the ∅-future.",
              tags=["fut=ப்", "fut=வ்", "fut=ப்ப்", "fut=உம்"]),
    382: dict(gist="இறப்பு எதிர்வு நிகழ்வு எனக் காலம் மூன்றே",
              governs="there are exactly three tenses: past, future, present",
              tags=[]),
    # --- 331 licenses the 1sg endings I had wrongly recorded as uncited
    331: dict(gist="குடுதுறுவு என்னும் குன்றியலுகரமோடு அல் அன் என் ஏன் ஆகும் ஈற்ற "
                   "இருதிணை முக்கூற்று ஒருமைத் தன்மை",
              governs="1sg தன்மை விகுதி: the kuṟṟiyalukaram கு, டு, து, று, வு TOGETHER "
                      "WITH அல், அன், என், ஏன். So -ஏன் and -அன் are licensed.",
              tags=["1sg=ஏன்", "1sg=அன்"]),
    340: dict(gist="செய்த செய்கின்ற செய்யும் என் பாட்டில் காலமும் செயலும் தோன்றிப் "
                   "பாலொடு … எஞ்ச நிற்பது பெயரெச்சமே",
              governs="பெயரெச்சம் (adjectival participle) in the three tense வாய்பாடு "
                      "செய்த / செய்கின்ற / செய்யும்",
              tags=["adjpart=அ", "futANDadjpart=உம்", "futANDadjpart=ம்"]),
    343: dict(gist="செய்து செய்பு செய்யா செய்யூ செய்தென செய செயின் செய்யிய செய்யியர் … "
                   "வினையெச்சம்",
              governs="வினையெச்சம் (verbal participle) வாய்பாடுகள், and the infinitive "
                      "செய/செயின் among them",
              tags=["vpart=உ", "vpart=இ", "vpart=∅", "vpart=மல்", "inf=அ", "inf=க்க"]),
    339: dict(gist="வேறு இல்லை உண்டு ஐம்பால் மூவிடத்தன",
              governs="the invariant குறிப்பு forms இல்லை, உண்டு, வேறு — all five pāl, "
                      "all three persons",
              tags=["negpart=இல்லை"]),
}

def tag_to_nurpa():
    m = {}
    for n, d in NURPA.items():
        for t in d["tags"]:
            m[t] = n
    return m

def main():
    want_uncited = "--uncited" in sys.argv
    T2N = tag_to_nurpa()
    if not GRID.exists():
        sys.exit(f"grid missing: {GRID}")

    cells = collections.Counter()      # feature string -> row count
    with open(GRID, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3: cells[p[2]] += 1

    # A cell has TWO citable dimensions and they are cited independently: the PNG suffix
    # (the last +k=v group) and the tense இடைநிலை (a +past=/+pres=/+fut= group). Reporting
    # one number for both would hide that tense was uncited while PNG was at 90.9%.
    cited = collections.defaultdict(dict)
    uncited_tag = collections.Counter()
    uncited_tense = collections.Counter()
    rows_total = png_rows = tense_rows = both_rows = 0
    tense_total = 0
    per_nurpa = collections.Counter()
    for feat, n in cells.items():
        rows_total += n
        tail = feat.rsplit("+", 1)[-1]
        nur = T2N.get(tail)
        if nur:
            png_rows += n; cited[feat]["png"] = nur; per_nurpa[nur] += n
        else:
            uncited_tag[tail] += n
        tm = re.search(r'\+(past|pres|fut)=([^+]+)', feat)
        if tm:
            tense_total += n
            key = f"{tm.group(1)}={tm.group(2)}"
            tn = T2N.get(key)
            if tn:
                tense_rows += n; cited[feat]["tense"] = tn; per_nurpa[tn] += n
                if nur: both_rows += n
            else:
                uncited_tense[key] += n

    print(f"  grid cells            : {rows_total:,} rows, {len(cells):,} distinct features")
    print(f"  PNG cited             : {png_rows:,}  ({100*png_rows/max(rows_total,1):.1f}%)"
          f"   {len(set(T2N) & {f.rsplit('+',1)[-1] for f in cells})}"
          f"/{len({f.rsplit('+',1)[-1] for f in cells})} distinct tags")
    print(f"  tense இடைநிலை cited   : {tense_rows:,} of {tense_total:,} finite-tense rows "
          f"({100*tense_rows/max(tense_total,1):.1f}%)")
    print(f"  BOTH cited            : {both_rows:,}  "
          f"({100*both_rows/max(rows_total,1):.1f}% of all rows)")
    print(f"\n  by nūṟpā:")
    for nur, c in sorted(per_nurpa.items()):
        print(f"    {ED.split('(')[0].strip()} {nur}: {c:>9,} rows   {NURPA[nur]['governs'][:58]}")
    if want_uncited:
        print(f"\n  uncited PNG tags, by rows:")
        for t, c in uncited_tag.most_common(14):
            print(f"    {t:<22} {c:>9,}")
        if uncited_tense:
            print(f"  uncited tense markers:")
            for t, c in uncited_tense.most_common(10):
                print(f"    {t:<22} {c:>9,}")

    C = canon()
    enriched = {}
    for k, v in NURPA.items():
        e = dict(v)
        if k in C:
            e["verse"] = C[k]["verse"]
            e["iyal"] = C[k]["iyal"]
            e["atikaram"] = C[k]["atikaram"]
        enriched[str(k)] = e
    have = sum(1 for k in NURPA if k in C)
    print(f"  canonical verse text available for {have}/{len(NURPA)} cited nūṟpā")
    doc = {
        "edition": ED,
        "warning": ("`verse` is canonical, from data/gold/nannul/nurpa.json (Wikisource). "
                    "`gist` is a reading aid via tools/bamini.py and is NOT canonical. "
                    "Cite by number."),
        "nurpa": enriched,
        "feature_to_nurpa": {f: v for f, v in cited.items()},
        "coverage": {"rows_total": rows_total, "png_rows": png_rows,
                     "tense_rows": tense_rows, "tense_total": tense_total,
                     "both_rows": both_rows,
                     "uncited_png": dict(uncited_tag.most_common()),
                     "uncited_tense": dict(uncited_tense.most_common())},
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  written: {OUT.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
