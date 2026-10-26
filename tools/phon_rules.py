#!/usr/bin/env python3
"""
spec/TLP1.md §7 item 5 — re-express tamil-noun.foma's rules phonemically and diff.

The foma source declares 26 rewrite rules (R1–R19, R101, PR1–PR6, two cleanups) over
Tamil *orthography*, and a lexicon that pre-spells 415 suffix allomorphs so those rules
only ever have to delete. This program states the same declension over TLP1 phonemes and
diffs the result against data/derived/nouns_grid.tsv.

Three stages, and the parameter count of each is the claim:

    1. STEM-FORM   class -> (truncate, increment, geminates)        16 x 3
    2. MORPHEME    feature -> one உருபு, concatenated in order       ~20
    3. JUNCTURE    phonemic rules applied where two morphs meet       7

Usage:
    python3 tools/phon_rules.py orth      # validate the foma reimplementation
    python3 tools/phon_rules.py phon      # derive phonemically and diff
    python3 tools/phon_rules.py series    # spec §7 item 1: the assimilation series
"""
import sys, os, re, json, collections, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T

# VARIANTS=all  generate every alternative the phonology licenses (default)
# VARIANTS=min  generate one form per cell -- the precision/recall trade-off, measured
VARIANTS = os.environ.get("TAMILOS_PHON_VARIANTS", "all")
GRID = ROOT / os.environ.get("TAMILOS_GRID", "data/derived/nouns_grid_final.tsv")

B = lambda s: T.encode(s)
C0 = T.MORPH_BOUNDARY

# ------------------------------------------------------------------ phoneme predicates
# Read the phonemes from the encoding, never from an assumed ordering. Hardcoding
# `0x60 | i` for இடையினம் survived draft 1 only because the list order happened to match;
# the draft-2 re-layout turned RA into ய், which silently rewrote every உயர்திணை plural
# and cost 25 points of cell agreement before the "nothing may move" check caught it.
_c = lambda ch: T.encode(ch + T.PULLI)[0]
KA, CA, TTA, THA, PA, RRA = (_c(c) for c in "க ச ட த ப ற".split())
NGA, NYA, NNA, NTHA, MA, NA = (_c(c) for c in "ங ஞ ண ந ம ன".split())
YA, RA, LA, VA, ZHA, LLA = (_c(c) for c in "ய ர ல வ ழ ள".split())
U, A, I = B("உ")[0], B("அ")[0], B("இ")[0]

FRONT = {1, 3, 5}                       # i, e, ai  -> ய் ;  everything else -> வ்

# மெய்யீற்றுப் புணரியல் hardening [Naṉṉūl 227]. Under the draft-2 layout this is
# T.harden() -- one AND, one OR -- for every member. The set says which consonants the
# rule APPLIES to; ண் is deliberately absent, since கண் + கள் is கண்கள்.
HARDENS = {LA, LLA, NA}

def is_v(b):   return T.is_uyir(b)
def is_val(b): return T.is_vallinam(b)
def is_mel(b): return T.is_mellinam(b)

# ------------------------------------------------------------------ 3. juncture rules
FIRED = collections.Counter()

def join(left, right, pada=False, gem=False, clitic=False, kural=False,
         inc=False, dbl=False, mono=False, nohard=False):
    """Apply the phonemic juncture rules where two morphs meet.

    pada=True   a word boundary (the +sandhi* bundles): a stem-final nasal is lost.
    clitic=True a particle boundary (தான், போல்): no புணரியல் at all.
    kural=True  the left form ends in a குற்றியலுகரம் -- an enunciative உ that
                drops before a vowel.  A முற்றியலுகரம் (பசு) does not: it takes
                a உடம்படுமெய் instead [Naṉṉūl 162].  Naṉṉūl 94 says which உகரம் is a குற்றியலுகரம்; 164 drops it.
    """
    if not left:  return bytes(right)
    if not right: return bytes(left)
    if clitic:
        if dbl and left and right and is_val(right[0]) and is_v(left[-1]):
            FIRED["P10 clitic-doubling"] += 1
            return bytes(left) + bytes([right[0]]) + bytes(right)
        return bytes(left) + bytes(right)
    a, b = left[-1], right[0]

    # P9  coalescence: two identical vowels across a seam become one
    #     (மர + அத்து -> மரத்து: the அ of the சாரியை absorbs)
    #     [Naṉṉūl 252; Tolkāppiyam புணரியல் 23: அத்தின் அகரம் அகர முனை இல்லை]
    if inc and is_v(a) and a == b:
        FIRED["P9 coalesce"] += 1
        return bytes(left) + bytes(right[1:])

    # at a pada juncture only ச் ட் த் ப் trigger anything at all
    if pada and not (b in (CA, TTA, THA, PA)):
        return bytes(left) + bytes(right)

    # P5  hiatus: a குற்றியலுகரம் drops before a vowel
    if kural and a == U and is_v(b) and len(left) >= 2 and T.is_mey(left[-2]):
        FIRED["P5 hiatus"] += 1
        return join(left[:-1], right, pada, gem, clitic, False)

    # P6  உடம்படுமெய்: a glide fills a vowel-vowel juncture
    if is_v(a) and is_v(b):
        FIRED["P6 udampadumey"] += 1
        g = YA if (a & 7) in FRONT else VA
        return bytes(left) + bytes([g]) + bytes(right)

    # P3  nasal loss at a pada juncture before a வல்லினம்.
    #     க் and ற் are excluded -- ThamizhiMorph keeps the nasal there (foma R17/R18
    #     list only த் ச் ட் ப்), which is itself open to question against Naṉṉūl.
    if pada and is_mel(a):
        FIRED["P3 nasal-loss"] += 1
        return bytes(left[:-1]) + bytes(right)

    # P1  assimilation: a மெல்லினம் takes the place of a following வல்லினம்.
    #     Restricted to ம்: the encoding predicts the whole series (spec §3), but the
    #     gold licenses only ம் -- foma R12 names ம் and nothing else.  See run_series().
    if a == MA and is_val(b) and not pada:
        FIRED["P1 assimilate"] += 1
        return bytes(left[:-1]) + bytes([T.assimilate(a, b)]) + bytes(right)

    # P2  hardening: ல்/ள்/ன்/ண் before a வல்லினம்
    if a in HARDENS and is_val(b) and not pada and not nohard:
        FIRED["P2 harden"] += 1
        return bytes(left[:-1]) + bytes([T.harden(a)]) + bytes(right)

    # P11 ஒற்று இரட்டல்: the final ஒற்று doubles before a vowel உருபு.  Naṉṉūl restricts
    #     this to monosyllables (கண் -> கண்ணை); ThamizhiMorph makes it a class property
    #     and so extends it to polysyllabic C11 (மாணவன் -> *மாணவன்னை).
    if mono and T.is_mey(a) and is_v(b):
        FIRED["P11 ottru-irattal"] += 1
        return bytes(left) + bytes([a]) + bytes(right)

    # P4  வல்லினம் மிகல்: the suffix-initial வல்லினம் doubles after a vowel
    if is_v(a) and is_val(b) and gem and not pada:
        FIRED["P4 geminate"] += 1
        return bytes(left) + bytes([b]) + bytes(right)

    return bytes(left) + bytes(right)

# ------------------------------------------------------------------ the சாரியை authority
#   Naṉṉūl Eḻuttatikāram, உருபுபுணரியல் (nūṟpā 240-257) governs the உருபு juncture.
#   data/gold/nannul/nurpa.json; both the Wikisource joined and the Project Madurai
#   split readings agree on all six cited below.
NURPA = {
 240: ("ஒருவன் ஒருத்தி பலர் ஒன்று பல என / வருபெயர் ஐந்தொடு பெயர்முதல் இருநான்கு / "
       "உருபும் உறழ்தர நாற்பதாம் உருபே",
       "five persons/numbers x the eight வேற்றுமை, உறழ்தர -- alternating -- - 40 உருபு"),
 242: ("ஒற்று உயிர் முதல் ஈற்று உருபுகள் புணர்ச்சியின் / ஒக்கும் அப்பெயர் வேற்றுமைப் புணர்ப்பே",
       "consonant- and vowel-initial உருபு join exactly as nouns do: the licence for "
       "running the ordinary புணரியல் at the உருபு seam, which is what join() does"),
 243: ("பதம்முன் விகுதியும் பதமும் உருபும் / புணர்வழி ஒன்றும் பலவும் சாரியை / "
       "வருதலும் தவிர்தலும் விகற்பமும் ஆகும்",
       "GOVERNING: where a stem meets a விகுதி, a stem or an உருபு, one or many "
       "சாரியை may COME, be OMITTED, or be OPTIONAL (விகற்பம்)"),
 244: ("அன் ஆன் இன் அல் அற்று இற்று அத்து அம் / தம் நம் நும் ஏ அ உ ஐ கு ன / "
       "இன்ன பிறவும் பொதுச் சாரியையே",
       "the பொதுச்சாரியை inventory -- it contains இன் and அத்து, so MORPH['in'] and "
       "the C15 increment are both cited here, not fitted"),
 253: ("இதற்கு இது சாரியை எனின் அளவு இன்மையின் / விகுதியும் பதமும் உருபும் பகுத்து இடை / "
       "நின்ற எழுத்தும் பதமும் இயற்கையும் / ஒன்ற உணர்த்தல் உரவோர் நெறியே",
       "to say 'this சாரியை for this' is without limit; the wise way is to teach by "
       "analogy -- Naṉṉūl DECLINES to enumerate the selection"),
 255: ("இயல்பின் விகாரமும் விகாரத்து இயல்பும் / உயர்திணை இடத்து விரிந்தும் தொக்கும் / "
       "விரவுப் பெயரின் விரிந்தும் நின்றும் / அன்ன பிறவும் ஆகும் ஐ உருபே",
       "the ஐ உருபு stands விரிந்து (expanded) or தொக்கு (elided) in உயர்திணை -- "
       "the authority for ஐ beside இனை"),
 257: ("இதற்கு இது முடிபு என்று எஞ்சாது யாவும் / விதிப்ப அளவு இன்மையின் விதித்தவற்று இயலான் / "
       "வகுத்து உரையாதவும் வகுத்தனர் கொளலே",
       "the chapter's closing under-determination clause: not everything can be "
       "prescribed, so take the unprescribed by analogy with what is"),
}
CITE = {"in": 244, "acc": 255, "sar": 243, "var": 253, "odb": 243, "cdb": 243,
        "infInc": 244, "juncture": 242}

# ------------------------------------------------------------------ 2. the morphemes
#   One entry per feature.  These are Naṉṉūl's வேற்றுமை உருபு plus the particles;
#   where a case has genuine variants they are listed and all are generated.
MORPH = {
    "pl":    ["கள்"],
    "in":    ["இன்"],        # இன் சாரியை [Naṉṉūl 244] -- கள் + இன் + ஆல் -> களினால்
    "acc":   ["ஐ"],          # விரிந்தும் தொக்கும் [Naṉṉūl 255]; இனை = இன் + ஐ
    "inst":  ["ஆல்"],
    # கு with the உ சாரியை, and கு with the இன் சாரியை -- இன் + கு hardens to இற்கு by
    # மெய்யீற்றுப் புணரியல் [Naṉṉūl 227].  Both licensed; 243 says the சாரியை is விகற்பம்.
    "dat":   ["உக்கு", "இற்கு"],
    "ben":   ["ஆக"],
    # ``உக்கு`` is the உ சாரியை plus the ending க்கு. It comes from two sources, not from a nūṟpā: ThamizhiMorph's
    # lexicon spells the dative as ten class-specific allomorphs (வுக்கு, யுக்கு, ணுக்கு, ... ), nine of which are
    # உ + க்கு after the stem's own consonant or a glide, and Arden 110 gives உக்கு. Naṉṉūl 244 lists உ among the
    # சாரியை but does not say the dative takes it, so that pairing is this table's. ``கள்`` takes none.
    "loc":   ["இல்", "இடம்"],
    "abl":   ["இல்", "இன்", "இலிருந்து"],
    "gen":   ["இன்", "அது"],
    "soc":   ["ஓடு", "உடன்"],
    "foc":   ["தான்"],
    "cmpr":  ["போல்"],
    "sandhik": ["க்"], "sandhic": ["ச்"],
    "sandhip": ["ப்"], "sandhit": ["த்"],
    "infInc": [],            # realised by the stem-form stage, not a morpheme
    "nom":   [],
    "so":    ["உடன்"],
}
CLITIC = {"foc", "cmpr"}
CASES = ("acc", "inst", "dat", "loc", "abl", "gen", "soc", "nom", "so")
ORDER = ("pl", "case", "ben", "cmpr", "foc", "sandhi")

def morphemes(feat):
    """Decompose a feature bundle into an ordered list of morpheme alternative-sets."""
    tags = [t for t in feat.split("+") if t and t != "noun"]
    unknown = [t for t in tags if t not in MORPH and t not in CASES]
    if unknown: return None, unknown
    seq = []
    if "pl" in tags: seq.append((MORPH["pl"], "pl"))
    if any(c in tags for c in ("acc", "inst", "gen", "abl")):
        seq.append((MORPH["in"] + [""], "in") if VARIANTS == "all"
                   else ([""], "in"))               # சாரியை optional
    for c in CASES:
        if c in tags and MORPH.get(c):
            seq.append((MORPH[c] if VARIANTS == "all" else MORPH[c][:1], c)); break
    if "ben" in tags: seq.append((MORPH["ben"], "ben"))
    if "cmpr" in tags: seq.append((MORPH["cmpr"], "cmpr"))
    if "foc" in tags: seq.append((MORPH["foc"], "foc"))
    for s in ("sandhik", "sandhic", "sandhip", "sandhit"):
        if s in tags: seq.append((MORPH[s], s))
    return seq, []

# ------------------------------------------------------------------ 1. the stem-forms
#   (truncate, increment, geminates, doubles-final) -- one row per declension class.
#   `inc` is the சாரியை; `gem` is whether a வல்லினம் உருபு doubles after this stem.
# Classes where the UNINFLECTED stem is a licensed oblique beside the சாரியை-bearing one. Empty now: it was C16
# (ஊர், சுவர்), whose சாரியை ற்று (சுவற்றை, ஊற்றுக்கு) has no verse behind it. Naṉṉūl 204 (உடல்மேல் உயிர்வந்து
# ஒன்றுவது இயல்பே) derives சுவரை and சுவரில் from the plain stem, and that is all the model derives.
PLAIN_OK = set()
UYAR = {"C11"}                  # ன் -> ர் before கள்  (foma R6)

STEMFORM = {
    "C1":  (0, "",      True,  False),    # பசு     vowel-final
    "C2":  (0, "",      False, False),   # எலி, நெய்
    "C3":  (0, "",      True,  False),    # ஈ
    "C4":  (0, "",      False, False),   # நாய், கால்
    "C5":  (0, "",      False, False),   # பலர்
    "C6":  (1, "டு",    False, False),   # காடு -> காட்டு
    "C7":  (1, "",      False, False),   # வண்டு -> வண்ட்
    "C8":  (1, "று",    False, False),   # ஆறு -> ஆற்று
    "C9":  (0, "",      False, True ),   # கண்
    "C10": (0, "",      False, True ),   # பொன்
    "C11": (0, "",      False, True ),   # மாணவன்
    "C12": (0, "",      False, True ),   # புல்
    "C13": (0, "",      False, True ),   # முள்
    "C14": (0, "",      False, False),   # நாள்
    "C15": (1, "அத்து", False, False),   # மரம் -> மர + அத்து சாரியை -> மரத்து
    "C16": (0, "",      False, False),   # சுவர் -> சுவரில் [Naṉṉūl 204]; ThamizhiMorph's சுவற்று has no verse
    # Naṉṉūl 181-182 relabels (tools/relabel_nannul.py): the குற்றியலுகரம் taxonomy
    # that replaced the coarse C6/C7/C8 split.
    "NDBLT":  (1, "டு",    False, False),   # காடு  -> காட்டு   (ட் doubles)
    "NDBLR":  (1, "று",    False, False),   # ஆறு   -> ஆற்று    (ற் doubles)
    "NCLUST": (1, "",      False, False),   # வண்டு -> வண்ட்     (cluster, no doubling)
    "NMURRI": (0, "",      True,  False),    # முற்றியலுகரம் -- the உ is lexical
}

def stemform(stem_b, cls, feat):
    """nom / obl / pl stem — every variant the grammar licenses.

    Yields (bytes, geminates, ends-in-a-குற்றியலுகரம், doubles-final, plain?).
    Where a class carries a சாரியை increment, the plain stem is yielded too: nūṟpā 243
    makes the சாரியை விகற்பம், so உலகின் stands beside உலகத்தின் and ஊருக்கு beside
    ஊற்றுக்கு."""
    trunc, inc, gem, dblfin = STEMFORM[cls]
    kural = False
    orig = bytes(stem_b)
    if "+infInc" in feat or needs_obl(feat):
        if trunc: stem_b = stem_b[:-trunc]
        cut = bytes(stem_b)
        if inc:
            # Naṉṉūl 181's exclusion: a stem whose final ஒற்று is already doubled does
            # not double again.  ThamizhiMorph's C6 lacks this, so it derives
            # *சிட்ட்ட for சிட்டு; the Naṉṉūl relabel moved most such stems to NCLUST.
            ib = B(inc)
            if not (len(stem_b) >= 2 and T.is_mey(stem_b[-1])
                    and stem_b[-1] == stem_b[-2] and ib[0] == stem_b[-1]):
                stem_b = join(stem_b, ib, inc=True)
                kural = ib[-1] == U
                # The plain alternant is the UNTRUNCATED stem only. A `cut` variant -- the
                # stem with its final consonant removed and no increment to replace it --
                # was emitted here once and can never be right: it makes உலகம் + இல் ->
                # உலகவில், சுவர் + ஐ -> சுவவை. Measured before removal: it added no UD
                # agreement and only non-words.
                out = [(bytes(stem_b), gem, kural, dblfin, 0)]
                if cls in PLAIN_OK and VARIANTS == "all":   # `min` means one form per cell
                    out.append((bytes(orig), gem, False, dblfin, 1))
                return out
    elif "+pl" in feat and cls in UYAR and stem_b and stem_b[-1] == NA:
        FIRED["P8 uyar-plural"] += 1
        stem_b = bytes(stem_b[:-1]) + bytes([RA])
    return [(bytes(stem_b), gem, kural, dblfin, 0)]

def needs_obl(feat):
    if "+pl" in feat: return False
    core = feat.replace("noun", "")
    for x in ("+foc", "+cmpr", "+sandhic", "+sandhik", "+sandhip", "+sandhit"):
        core = core.replace(x, "")
    return core.strip("+") not in ("nom", "")

# ------------------------------------------------------------------ derive
def _arden110(cur):
    """True when the base ends in இ, ஈ or ஐ: quality 1 (i) or 5 (ai), short or long."""
    x = [b for b in cur if b != C0]
    return bool(x) and T.is_uyir(x[-1]) and (x[-1] & 7) in (1, 5)

def derive_labeled(stem, cls, feat):
    """Every licensed surface, each tagged with the optional choices that produced it.

    The tag is what tools/learn_variants.py learns to select:
        sar  the இன் சாரியை was taken
        var  which case-உருபு alternative, 1-based; 0 means the உருபு had no
             alternatives at all, so taking it was not a choice
        odb  the ஒற்று was doubled
        cdb  the clitic doubled its initial வல்லினம்
    """
    try: sb = B(stem)
    except T.TLP1Error: return None
    seq, unknown = morphemes(feat)
    if seq is None: return None
    bases = stemform(sb, cls, feat)
    pada = any(s in feat for s in ("sandhic", "sandhik", "sandhip", "sandhit"))
    # sar, var, odb, cdb, plain-stem, unhardened
    outs = {(bytes(b), ku, True, (0, 0, 0, 0, pl, 0))
            for b, _g, ku, _d, pl in bases}
    gem = bases[0][1]; dblfin = bases[0][3]
    for i, (alts, kind) in enumerate(seq):
        last = (i == len(seq) - 1)
        nxt = set()
        for cur, k, first, d in outs:
            for vi, a in enumerate(alts):
                # P12  The dative உருபு is கு itself [Tolkāppiyam, Collatikāram, வேற்றுமையியல் 14:
                # கு எனப் பெயரிய வேற்றுமைக் கிளவி]. The உ of உக்கு is a சாரியை [Naṉṉūl 244 lists
                # it], which may be left out [Naṉṉūl 243; and Tolkāppiyam, உருபியல் 30, says that for
                # words it has not listed a சாரியை is not obligatory]; Arden 110 says where: after a
                # base ending in இ, ஈ or ஐ -- குழந்தைக்கு, not குழந்தையுக்கு.
                g = gem                         # the class decides whether a வல்லினம் doubles ...
                if kind == "dat" and a != "உக்கு" and _arden110(cur):
                    continue                    # after இ ஈ ஐ the dative is கு only: no இற்கு (குழந்தையிற்கு, தந்தையிற்கு are not forms)
                if kind == "dat" and a == "உக்கு" and _arden110(cur):
                    # ... but this உருபு is a வேற்றுமை one, and it doubles after a vowel whatever the
                    # class (மொழிக்கு), where the plural கள் is not (மொழிகள்).
                    FIRED["P12 dative-ku"] += 1; a = "கு"; g = True
                if not a:                       # the slot may be empty (சாரியை)
                    nxt.add((cur, k, first, d)); continue
                dd = list(d)
                if kind == "in": dd[0] = 1
                elif kind in CASES and len(alts) > 1: dd[1] = vi + 1
                if kind in CASES and d[0] and a.startswith("இன்"):
                    continue                    # இன் + இன் -> இனின், not a word
                nk = B(a)[-1] == U
                nxt.add((join(cur, B(a), pada=pada and last, gem=g,
                              clitic=(kind in CLITIC), kural=k), nk, False, tuple(dd)))
                if dblfin and first and VARIANTS == "all":
                    e = list(dd); e[2] = 1
                    nxt.add((join(cur, B(a), pada=pada and last, gem=g,
                                  clitic=(kind in CLITIC), kural=k, mono=True),
                             nk, False, tuple(e)))
                if kind in CLITIC and VARIANTS == "all":
                    e = list(dd); e[3] = 1
                    nxt.add((join(cur, B(a), clitic=True, dbl=True), nk, False, tuple(e)))
                if first and VARIANTS == "all":
                    # உறழ்வு [Naṉṉūl Eḻuttatikāram 226]: ல்/ள் before கள் may harden or
                    # not -- கற்கள் beside கல்கள், நாட்கள் beside நாள்கள். Emitting only
                    # the hardened form was this project selecting where the nūṟpā
                    # licenses both, which is the error paper/tlp1-encoding.md argues
                    # against. Identical outputs dedup, so this is free where P2 is idle.
                    e = list(dd); e[5] = 1
                    nxt.add((join(cur, B(a), pada=pada and last, gem=g,
                                  clitic=(kind in CLITIC), kural=k, nohard=True),
                             nk, False, tuple(e)))
        outs = nxt
    # Several choices of optional mechanism can give the same surface. Which label it carries
    # must not depend on set iteration order (hash-randomised: two runs gave different
    # labels on ~440k rows), so keep the derivation that engages the FEWEST optional
    # mechanisms, then the smallest tuple. The surfaces themselves are unaffected.
    res = {}
    for o, _, _, d in outs:
        try: surf = T.decode(bytes(b for b in o if b != C0))
        except Exception: continue
        key = (sum(1 for v in d if v), d)
        if surf not in res or key < res[surf][0]: res[surf] = (key, d)
    return {surf: kd[1] for surf, kd in res.items()}

def derive(stem, cls, feat):
    r = derive_labeled(stem, cls, feat)
    return None if r is None else set(r)


# ==================================================================  the foma baseline
# A faithful Python reimplementation of tamil-noun.foma, so that "what the rules do" is
# measured rather than asserted.  Validated at 1,554,407 / 1,554,418 cells.
LEXC = ROOT / "data/gold/thamizhi-morph/foma/src/Nouns.lexc"
LONG, CS1, CS2, PU = "ாீூைோேௌஆ", "யர", "தகமவணளனலரழ", "்"

ORTH_RULES = [
 ("R1",   rf"(?<=[{LONG}][{CS1}]){PU}(?=\^(?:ி|ு|ோ|து|ை|ா))"),
 ("R101", rf"(?<=[{LONG}])ய{PU}(?=\^ோ)"),
 ("R2",   rf"(?<=[{CS2}]){PU}(?=\^(?:ி|ு|ோ|து|ை|ா))"),
 ("R3",   r"டு(?=\^ட்ட)"),           ("R4",  r"ு(?=\^ஆ)"),
 ("R5",   r"று(?=\^ற)"),             ("R6",  r"ன்(?=\^ர்க)"),
 ("R7",   r"ன்(?=\^(?:னி|னோ|னா|னு))"), ("R8", r"ல்(?=\^ற்க)"),
 ("R9",   r"ள்(?=\^ட்க)"),           ("R10", rf"(?<=[{LONG}])ள்(?=\^ட்க)"),
 ("R11",  rf"(?<=ருள){PU}(?=\^(?:ி|ு|ோ|ை|ா))"),
 ("R12",  r"ம்(?=\^ங்க)"),           ("R13", r"ம்(?=\^த்த)"),
 ("R14",  r"ர்(?=\^ற்ற)"),
 ("R15",  rf"(?<=ள){PU}(?=\^(?:ி|ு|ோ|ை|ா))"),
 ("R16",  r"ன்(?=\^ற்)"),            ("R17", r"ம்(?=\^(?:த்|ச்|ட்|ப்))"),
 ("R18",  r"ன்(?=\^(?:த்|ச்|ட்|ப்))"),
 ("R19",  r"ன்(?=\^(?:ற்த்|ற்ச்|ற்ட்|ற்ப்))"),
]
PRON = [("PR1", ["நம்"], "ந"), ("PR2", ["தாங்கள்"], "த"),
        ("PR3", ["எங்கள்", "எம்", "என்"], "எ"),
        ("PR4", ["அவன்", "அவள்", "அது", "அவை", "அவர்கள்", "அவர்"], "அ"),
        ("PR5", ["உவன்", "உவள்", "உது", "உவை", "உன்", "உம்", "உங்கள்",
                 "உவர்கள்", "உவர்"], "உ"),
        ("PR6", ["இவன்", "இவள்", "இது", "இவை", "இவர்கள்", "இவர்"], "இ")]
OFIRED = collections.Counter()

def orth_apply(s, count=True):
    for name, pat in ORTH_RULES:
        new = re.sub(pat, "", s)
        if count and new != s: OFIRED[name] += 1
        s = new
    for name, alts, follow in PRON:
        for a in alts:
            new = re.sub(a + r"(?=\^" + follow + ")", "", s)
            if count and new != s: OFIRED[name] += 1
            s = new
    new = re.sub(r"(?<=\^)ஆ", "", s)
    if count and new != s: OFIRED["Cleanup1"] += 1
    return new.replace("^", "")

def load_lexc():
    cur, suf, stems = None, collections.defaultdict(lambda: collections.defaultdict(set)), \
                      collections.defaultdict(set)
    for line in LEXC.read_text().splitlines():
        m = re.match(r"^LEXICON\s+(\S+)", line)
        if m: cur = m.group(1); continue
        if not cur: continue
        line = line.split("!")[0].strip()
        if not line: continue
        if cur.endswith("Inflections") and line.startswith("+"):
            c = cur[:-len("Inflections")]
            m = re.match(r"^(\+[^\s:]*):(\S*)\s*#\s*;", line)
            if m: suf[c][m.group(1)].add(m.group(2))
            elif re.match(r"^(\+[^\s:]*):\s*#\s*;", line):
                suf[c][re.match(r"^(\+[^\s:]*):", line).group(1)].add("")
        elif re.fullmatch(r"C\d+(Sg|pl)", cur):
            m = re.match(r"^(\S+)\s+(C\d+)(?:Sg|pl)Root\s*;", line)
            if m: stems[m.group(1)].add(m.group(2))
    return suf, stems

def suffixes_for(table, feat):
    for key in ("+" + feat, "+noun+infInc+" + feat[len("noun+"):]):
        if key in table: return table[key]
    return None

def rows():
    with open(GRID, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4: yield p[0], p[1], p[2], p[3]

# ==================================================================  drivers
def run_orth():
    suf, stems = load_lexc()
    ok = bad = miss = 0
    for stem, cl, feat, surf in rows():
        classes = stems.get(stem) or {re.sub(r"(Sg|pl)Root$", "", cl)}
        alts = set()
        for c in classes:
            s = suffixes_for(suf.get(c, {}), feat)
            if s: alts |= s
        if not alts: miss += 1; continue
        got = {orth_apply(stem + s) for s in alts}
        if got == set(surf.split("|")): ok += 1
        else: bad += 1
    tot = ok + bad + miss
    print(f"  foma reimplementation: {ok:,d} / {tot:,d} exact   "
          f"({100*ok/tot:.4f}%)   diff {bad}   no-suffix {miss}")
    print(f"\n  rule applications over {tot:,d} cells")
    for k, _ in ORTH_RULES + [(n, None) for n, _, _ in PRON] + [("Cleanup1", None)]:
        v = OFIRED.get(k, 0)
        print(f"    {k:9s} {v:9,d}" + ("   DEAD — never fires" if v == 0 else ""))

def run_phon():
    ok = bad = skip = 0
    gold_n = got_n = inter = 0
    missed = collections.Counter(); byfeat = collections.Counter()
    byfeat_ok = collections.Counter(); ex = collections.defaultdict(list)
    for stem, cl, feat, surf in rows():
        c = re.sub(r"(Sg|pl)Root$", "", cl)
        got = derive(stem, c, feat)
        want = set(surf.split("|"))
        byfeat[feat] += 1
        if got is None: skip += 1; continue
        gold_n += len(want); got_n += len(got); inter += len(want & got)
        if want & got:
            ok += 1; byfeat_ok[feat] += 1
        else:
            bad += 1
            missed[(c, feat)] += 1
            if len(ex[(c, feat)]) < 2:
                ex[(c, feat)].append((stem, sorted(want), sorted(got)))
    tot = ok + bad + skip
    print(f"  phonemic derivation:   {ok:,d} / {tot:,d} cells agree   "
          f"({100*ok/tot:.4f}%)   miss {bad:,d}   skip {skip:,d}")
    print(f"  surfaces: recall {100*inter/gold_n:.2f}% ({inter:,d}/{gold_n:,d})   "
          f"precision {100*inter/got_n:.2f}% ({inter:,d}/{got_n:,d})")
    print(f"\n  juncture rules fired")
    for k, v in FIRED.most_common(): print(f"    {k:18s} {v:11,d}")
    print(f"\n  worst (class, bundle) cells")
    for (c, feat), n in missed.most_common(14):
        s, w, g = ex[(c, feat)][0]
        print(f"    {c:4s} {feat:24s} {n:7,d}   {s} -> want {w[:2]}  got {g[:2]}")

def run_series():
    """spec/TLP1.md §7 item 1 — does assimilate() over-predict?"""
    print("  ம் + வல்லினம், by the encoding's own rule  (n & ~7) | (f & 7)")
    m = B("ம்")[0]
    for name in ("க்", "ச்", "ட்", "த்", "ப்", "ற்"):
        f = B(name)[0]
        out = T.decode(bytes([T.assimilate(m, f)]))
        print(f"    ம் + {name}  ->  {out}{name}")
    print("\n  attested in the grid (surfaces where a ம்-final stem meets கள்)")
    hits = collections.Counter()
    for stem, cl, feat, surf in rows():
        if feat != "noun+pl+nom" or not stem.endswith("ம்"): continue
        for s in surf.split("|"):
            base = stem[:-2]
            if s.startswith(base) and len(s) > len(base):
                hits[s[len(base):len(base)+2]] += 1
    for k, v in hits.most_common(6): print(f"    ...{k}  {v:,d}")

def run_count():
    suf, _ = load_lexc()
    allo = set()
    for c, tab in suf.items():
        for f, xs in tab.items(): allo |= {x.lstrip("^") for x in xs if x}
    bundles = {f for tab in suf.values() for f in tab}
    morphs = sum(len(v) for v in MORPH.values())
    print("  orthographic (tamil-noun.foma + Nouns.lexc)")
    print(f"    rewrite rules                    {len(ORTH_RULES) + len(PRON) + 2:4d}")
    print(f"    suffix allomorphs in the lexicon {len(allo):4d}")
    print(f"    feature bundles they cover       {len(bundles):4d}")
    print(f"    TOTAL parameters                 {len(ORTH_RULES)+len(PRON)+2+len(allo):4d}")
    # Counted from this file's own source -- an earlier version printed a literal 11,
    # which was never checked: P7 had been folded into P4 and P8 is a stem-form rule.
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    nrules = len(set(re.findall(r'FIRED\["(P\d+) ', src)))
    print("\n  phonemic (tools/phon_rules.py, over TLP1)")
    print(f"    labelled rules (P-numbers in source) {nrules:3d}")
    print(f"    morphemes (உருபு + சாரியை + clitics) {morphs:4d}")
    print(f"    class rows x 4 parameters        {len(STEMFORM)*4:4d}")
    print(f"    TOTAL parameters                 {nrules + morphs + len(STEMFORM)*4:4d}")

def run_vikarpam():
    """How much of the precision gap is விகற்பம் that Naṉṉūl 243 licenses?

    Every surface this derivation produces is licensed by the rules.  The question is
    whether a surface the gold omits was produced by engaging one of the OPTIONAL
    mechanisms -- which nūṟpā 243 declares may come, be omitted, or be optional -- or
    by the obligatory core, in which case it is a real over-generation.
    """
    # A mechanism being OPTIONAL means both engaging it and not engaging it are
    # licensed, so attributing விகற்பம் only to candidates that engaged one undercounts
    # it.  The defensible criterion is at the cell: if any gold surface WAS derived, the
    # rules are right and the leftovers are a selection among alternants; if none was,
    # the cell genuinely failed.
    OPT = ("sar", "var", "odb", "cdb", "plain", "nohard")
    cell_vik = cell_fail = 0; fail_by = collections.Counter(); fail_ex = {}
    spur = collections.Counter(); gold_dec = collections.Counter()
    core_by = collections.Counter(); core_ex = {}
    tot_spur = tot_gold = 0
    for stem, cl, feat, surf in rows():
        c = re.sub(r"(Sg|pl)Root$", "", cl)
        cand = derive_labeled(stem, c, feat)
        if not cand: continue
        want = set(surf.split("|"))
        hit = bool(want & set(cand))
        if hit: cell_vik += len(set(cand) - want)
        else:
            cell_fail += len(cand)
            fail_by[(c, feat)] += 1
            fail_ex.setdefault((c, feat), (stem, sorted(cand)[:1], sorted(want)[:2]))
        for s_, dec in cand.items():
            used = tuple(n for n, f in zip(OPT, (dec[0], dec[1] > 0) + tuple(dec[2:]))
                         if f)
            if s_ in want: gold_dec[used] += 1; tot_gold += 1
            else:
                spur[used] += 1; tot_spur += 1
                if not used:
                    core_by[(c, feat)] += 1
                    core_ex.setdefault((c, feat), (stem, s_, sorted(want)[:2]))
    print(f"  surfaces the gold lists    {tot_gold:,d}")
    print(f"  surfaces the gold omits    {tot_spur:,d}")
    core = spur[()]
    print(f"\n  omitted surfaces by which OPTIONAL mechanism produced them")
    for k, v in spur.most_common():
        tag = "+".join(k) if k else "NONE -- the obligatory core"
        print(f"    {tag:34s} {v:10,d}   {100*v/tot_spur:5.1f}%")
    tot = tot_gold + tot_spur
    print(f"\n  by the cell criterion")
    print(f"    விகற்பம் -- a gold surface WAS derived, the rest are alternants")
    print(f"                             {cell_vik:,d} = "
          f"{100*cell_vik/tot_spur:.2f}% of the omitted surfaces")
    print(f"    genuine failure -- no gold surface derived in that cell")
    print(f"                             {cell_fail:,d} = {100*cell_fail/tot:.2f}% "
          f"of all {tot:,d} derived surfaces")
    print(f"    precision against Naṉṉūl {100*(1-cell_fail/tot):.2f}%")
    print(f"\n  the failed cells, by (class, bundle)")
    for (c, feat), n in fail_by.most_common(10):
        stem, got, want = fail_ex[(c, feat)]
        print(f"    {c:7s} {feat:22s} {n:7,d}   {stem}: derived {got[0]}  gold {want}")

def run_cite():
    print("  Naṉṉūl Eḻuttatikāram, 5. உருபுபுணரியல் — the chapter that governs "
          "the உருபு seam\n")
    for n, (verse, gist) in sorted(NURPA.items()):
        print(f"  நூற்பா {n}")
        for ln in verse.split(" / "): print("      " + ln)
        print(f"    -> {gist}\n")
    print("  what each parameter is cited to")
    for k, n in sorted(CITE.items(), key=lambda x: x[1]):
        print(f"    {k:10s} {n}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "phon"
    {"orth": run_orth, "phon": run_phon, "series": run_series,
     "count": run_count, "vikarpam": run_vikarpam, "cite": run_cite}[cmd]()
