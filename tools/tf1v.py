#!/usr/bin/env python3
"""
TF1, verb side -- the register for a finite or non-finite verb form.  spec/TF1.md §7

Same 128-bit register as the noun side (tools/tf1.py), one plane per domain:

   plane 0   bits 0,1  SG PL         shared with nouns; a verb takes them from its PNG slot
   plane 1   AGREEMENT: இடம் / திணை / பால் / HON / ANY, shared with nouns, plus the twelve raw
             ThamizhiMorph person-number-gender slots at bits 48..59
   plane 2   bits 64..95   VERB MORPHOLOGY, below

The register holds FEATURES. The `=value` part of a source atom (`past=ட்`, `3sgm=அன்`) is the
EXPONENT, the surface morph that realises the feature. It is not a feature, nobody ANDs it, and
it is carried by a separate dense bundle code over the full source string: 715 strings, 10 bits.

   64 FIN   65 NONFIN                            FINITENESS   exactly one
   66 PAST  67 PRES  68 FUT  69 FUTADJPART       TENSE        at most one
   70 IMP   71 OPT   72 NEG  73 CON              MOOD
   74 MOODPART 75 NEGPART 76 ADJPART 77 VPART 78 INF   PARTICLE / NON-FINITE
   79 CAUS  80 PASSIVE 81 MIDDLE 82 COMPLEX 83 SIM 84 AUX   VOICE / DERIVATION
   85 STRONG 86 WEAK                             class markers
   87 EUPH
   88 SANDHI_K 89 SANDHI_C 90 SANDHI_P 91 SANDHI_T 92 SANDHI_HYPHEN
"""
import csv, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tf1 as N

ROOT = pathlib.Path(__file__).resolve().parent.parent
TABLE = ROOT / "spec/tf1v_bundles.tsv"
_m = N._m

class TF1VError(N.TF1Error):
    pass

# ------------------------------------------------------------------ plane 2: verb morphology
FIN, NONFIN = 64, 65
PAST, PRES, FUT, FUTADJPART = 66, 67, 68, 69
IMP, OPT, NEG, CON = 70, 71, 72, 73
MOODPART, NEGPART, ADJPART, VPART, INF = 74, 75, 76, 77, 78
CAUS, PASSIVE, MIDDLE, COMPLEX, SIM, AUX = 79, 80, 81, 82, 83, 84
STRONG, WEAK = 85, 86
EUPH = 87
SANDHI_K, SANDHI_C, SANDHI_P, SANDHI_T = 88, 89, 90, 91
SANDHI_HYPHEN = 92        # a SPELLING flag: the source writes `sandhi-k` as well as `sandhik`

TENSE_MASK  = _m(PAST, PRES, FUT, FUTADJPART)
SANDHI_MASK = _m(SANDHI_K, SANDHI_C, SANDHI_P, SANDHI_T)
PLANE2_DEFINED = (_m(FIN, NONFIN, IMP, OPT, NEG, CON, MOODPART, NEGPART, ADJPART, VPART, INF,
                     CAUS, PASSIVE, MIDDLE, COMPLEX, SIM, AUX, STRONG, WEAK, EUPH, SANDHI_HYPHEN)
                  | TENSE_MASK | SANDHI_MASK)

# the twelve raw ThamizhiMorph slots, plane 1 bits 48..59
SLOTS = ["1sg", "1pl", "2sg", "2pl", "2sgh", "3sgm", "3sgf", "3sge", "3sghe", "3sgn", "3ple", "3pln"]
_SLOT_BIT = {s: 48 + i for i, s in enumerate(SLOTS)}
PNG_MASK = _m(*_SLOT_BIT.values())

# slot -> (இடம், number, திணை, பால், honorific).  Anchored to the verses:
#   325 ஆண்பால் · 326 பெண்பால் · 327 பல்லோர் படர்க்கை · 328 ஒன்றன் · 329 பலவின் ·
#   331 தன்மை ஒருமை · 332 தன்மை பன்மை · 335 முன்னிலை ஒருமை · 337 முன்னிலை பன்மை
# 3sge, 3sghe and 3ple all take 327's பலர்பால் endings (அர் ஆர் ப மார்). The NUMBER is
# ThamizhiMorph's label as given, which for 3sge, 3sghe and 2sgh is the referent's number and
# not the form's; see spec/TF1.md §7.4.
PNG_MAP = {
    "1sg":   (N.TANMAI,    N.SG, None,       None,    False),
    "1pl":   (N.TANMAI,    N.PL, None,       None,    False),
    "2sg":   (N.MUNNILAI,  N.SG, None,       None,    False),
    "2pl":   (N.MUNNILAI,  N.PL, None,       None,    False),
    "2sgh":  (N.MUNNILAI,  N.SG, None,       None,    True),
    "3sgm":  (N.PADARKKAI, N.SG, N.UYAR,     N.AAN,   False),
    "3sgf":  (N.PADARKKAI, N.SG, N.UYAR,     N.PEN,   False),
    "3sge":  (N.PADARKKAI, N.SG, N.UYAR,     N.PALAR, False),
    "3sghe": (N.PADARKKAI, N.SG, N.UYAR,     N.PALAR, True),
    "3sgn":  (N.PADARKKAI, N.SG, N.AKRINAI,  N.ONRU,  False),
    "3ple":  (N.PADARKKAI, N.PL, N.UYAR,     N.PALAR, False),
    "3pln":  (N.PADARKKAI, N.PL, N.AKRINAI,  N.PALA,  False),
}
_DERIVED_MASK = N.NUMBER_MASK | N.IDAM_MASK | N.TINAI_MASK | N.PAL_MASK | _m(N.HON)

def _derived(slot):
    idam, num, tinai, pal, hon = PNG_MAP[slot]
    r = _m(idam, num)
    if tinai is not None: r |= _m(tinai)
    if pal is not None:   r |= _m(pal)
    if hon:               r |= _m(N.HON)
    return r

# the verb's allowed bits: number, the agreement plane, the raw slots, plane 2
VERB_DEFINED = N.NUMBER_MASK | N.AGR_MASK | PNG_MASK | PLANE2_DEFINED

# ------------------------------------------------------------------ atoms
_FLAG = {"fin": FIN, "nonfin": NONFIN, "past": PAST, "pres": PRES, "fut": FUT,
         "futANDadjpart": FUTADJPART, "imp": IMP, "opt": OPT, "neg": NEG, "con": CON,
         "moodpart": MOODPART, "negpart": NEGPART, "adjpart": ADJPART, "vpart": VPART,
         "inf": INF, "caus": CAUS, "passive": PASSIVE, "middle": MIDDLE, "complex": COMPLEX,
         "sim": SIM, "aux": AUX, "strong": STRONG, "weak": WEAK, "euph": EUPH}
_SANDHI = {"k": SANDHI_K, "c": SANDHI_C, "p": SANDHI_P, "t": SANDHI_T}
# Every source string respects ONE global atom order (45 atoms, acyclic, 0 of 715 violate it),
# found by topological sort in tools/validate_tf1v.py and frozen here.
ATOM_ORDER = ['verb', 'fin', 'nonfin', 'sim', 'complex', 'passive', 'caus', 'strong', 'past',
              'pres', 'inf', 'weak', 'middle', 'fut', '3sghe', '3ple', '3sge', '1pl', '2sgh',
              '3pln', '3sgn', 'moodpart', 'imp', '2sg', 'neg', '2pl', 'euph', '1sg', '3sgf',
              '3sgm', 'vpart', 'adjpart', 'sandhic', 'sandhik', 'sandhip', 'sandhit',
              'futANDadjpart', 'negpart', 'opt', 'sandhi-c', 'sandhi-k', 'sandhi-p',
              'sandhi-t', 'aux', 'con']

def _pop(x): return bin(x).count("1")

# ------------------------------------------------------------------ parsing
def parse(bundle):
    """[(atom, exponent-or-None), ...] in source order, without the leading `verb`."""
    toks = [t for t in bundle.strip().split("+") if t]
    if not toks or toks[0] != "verb":
        raise TF1VError(f"not a verb bundle: {bundle!r}")
    out = []
    for t in toks[1:]:
        a, eq, v = t.partition("=")
        out.append((a, v if eq else None))
    bases = [a for a, _ in out]
    if len(set(bases)) != len(bases):
        raise TF1VError(f"repeated atom in {bundle!r}")
    return out

def strip_exponents(bundle):
    """The source string with every `=value` removed, in the source's own spelling."""
    return "+" + "+".join(["verb"] + [a for a, _ in parse(bundle)])

# ------------------------------------------------------------------ validity
def check(reg):
    """Raise TF1VError unless `reg` is a well-formed VERB register."""
    if not 0 <= reg < (1 << N.WIDTH):
        raise TF1VError(f"not a {N.WIDTH}-bit register: {reg}")
    if reg & ~VERB_DEFINED:
        raise TF1VError(f"bits outside the verb layout: 0x{reg & ~VERB_DEFINED:032X}")
    if _pop(reg & _m(FIN, NONFIN)) != 1:
        raise TF1VError("exactly one of FIN, NONFIN")
    if _pop(reg & _m(SIM, COMPLEX)) != 1:
        raise TF1VError("exactly one of SIM, COMPLEX")
    if bool(reg & _m(PASSIVE)) != bool(reg & _m(COMPLEX)):
        raise TF1VError("PASSIVE if and only if COMPLEX (true of all 184 such strings)")
    if _pop(reg & TENSE_MASK) > 1:
        raise TF1VError("at most one tense flag")
    if _pop(reg & _m(STRONG, WEAK)) > 1:
        raise TF1VError("at most one of STRONG, WEAK")
    if _pop(reg & _m(ADJPART, VPART, INF)) > 1:
        raise TF1VError("at most one of ADJPART, VPART, INF")
    if _pop(reg & SANDHI_MASK) > 1:
        raise TF1VError("at most one sandhi flag")
    if reg & _m(SANDHI_HYPHEN) and not reg & SANDHI_MASK:
        raise TF1VError("SANDHI_HYPHEN without a sandhi flag")
    slots = [s for s in SLOTS if reg & _m(_SLOT_BIT[s])]
    if len(slots) > 1:
        raise TF1VError("at most one person-number-gender slot")
    if slots:
        if not reg & _m(FIN):
            raise TF1VError("a PNG slot only on a FIN form")
        want = _derived(slots[0])
        if reg & _DERIVED_MASK != want:
            raise TF1VError(f"agreement bits of {slots[0]} are 0x{reg & _DERIVED_MASK:X}, "
                            f"expected 0x{want:X}")
    elif reg & _DERIVED_MASK:
        raise TF1VError("agreement or number bits without a PNG slot")
    if bool(reg & _m(N.ANY)) != (bool(reg & _m(OPT)) and not slots):
        raise TF1VError("ANY if and only if OPT with no PNG slot (nūṟpā 338)")
    return reg

def is_valid(reg):
    try: check(reg); return True
    except N.TF1Error: return False

# ------------------------------------------------------------------ codec
def encode(bundle):
    """The FEATURE register of a source bundle; exponents are not part of it."""
    reg = 0
    for a, _ in parse(bundle):
        if a in _FLAG:
            reg |= _m(_FLAG[a])
        elif a in _SLOT_BIT:
            reg |= _m(_SLOT_BIT[a]) | _derived(a)
        elif a.startswith("sandhi"):
            k = a[len("sandhi"):].lstrip("-")
            if k not in _SANDHI or a not in ("sandhi" + k, "sandhi-" + k):
                raise TF1VError(f"unknown sandhi atom {a!r}")
            reg |= _m(_SANDHI[k])
            if "-" in a: reg |= _m(SANDHI_HYPHEN)
        else:
            raise TF1VError(f"unknown atom {a!r} in {bundle!r}")
    if reg & _m(OPT) and not reg & PNG_MASK:
        reg |= _m(N.ANY)                       # nūṟpā 338: the optative takes every subject
    return check(reg)

def decode_features(reg):
    """Feature string in the global atom order, exponents omitted, source spelling kept."""
    check(reg)
    have = []
    for a in ATOM_ORDER[1:]:
        if a in _FLAG and reg & _m(_FLAG[a]): have.append(a)
        elif a in _SLOT_BIT and reg & _m(_SLOT_BIT[a]): have.append(a)
        elif a.startswith("sandhi"):
            k = a[len("sandhi"):].lstrip("-")
            if reg & _m(_SANDHI[k]) and ("-" in a) == bool(reg & _m(SANDHI_HYPHEN)):
                have.append(a)
    return "+" + "+".join(["verb"] + have)

def slot_of(reg):
    for s in SLOTS:
        if reg & _m(_SLOT_BIT[s]): return s
    return None

# ------------------------------------------------------------------ agreement
def agrees(subject, verb):
    """Does a finite verb form agree with a subject register?

    The verb states what it requires; the subject must carry each flag the verb carries, in
    இடம், திணை, பால் and number. HON is a property of the VERB form and is not required of
    the subject. An optative (ANY) agrees with everything, per nūṟpā 338. A verb that states no
    agreement at all, such as a participle, is not an agreeing form and raises.

    SYNTHETIC ONLY: no noun has plane-1 data, so this can be exercised only on registers
    built by hand. It is a software predicate; nothing here has been synthesised."""
    check(verb)
    if verb & _m(N.ANY):
        return True
    if not verb & _m(*_SLOT_BIT.values()):
        raise TF1VError("this verb form states no agreement (a participle or a bare imperative)")
    for mask in (N.IDAM_MASK, N.TINAI_MASK, N.PAL_MASK, N.NUMBER_MASK):
        need = verb & mask
        if need and not subject & need:
            return False
    return True

# ------------------------------------------------------------------ dense bundle code
_TABLE = None
def _table():
    global _TABLE
    if _TABLE is None:
        if not TABLE.exists():
            raise TF1VError(f"{TABLE} missing; run tools/validate_tf1v.py --write")
        rows = list(csv.DictReader(TABLE.open(encoding="utf-8"), delimiter="\t"))
        _TABLE = ({r["bundle"]: int(r["code"]) for r in rows},
                  {int(r["code"]): (r["bundle"], int(r["reg"], 16)) for r in rows})
    return _TABLE

def dense(bundle):
    """Dense code 0..714 for a FULL source string, exponents included: the ROM address field."""
    try: return _table()[0][bundle]
    except KeyError: raise TF1VError(f"bundle not in the frozen universe: {bundle!r}")

def bundle_of(code):
    try: return _table()[1][code][0]
    except KeyError: raise TF1VError(f"no bundle has dense code {code}")

def reg_of(code):
    try: return _table()[1][code][1]
    except KeyError: raise TF1VError(f"no bundle has dense code {code}")

def universe_size():
    return len(_table()[0])

if __name__ == "__main__":
    for b in ("+verb+fin+sim+weak+past=ட்+3sgm=அன்", "+verb+fin+sim+opt=க", "+verb+nonfin+sim+vpart=உ"):
        r = encode(b)
        print(f"  {b}\n     {N.to_hex(r)}  slot={slot_of(r)}  {decode_features(r)}")
