#!/usr/bin/env python3
"""
TF1 -- the Tamil feature register, noun side.  spec/TF1.md

TLP1 encodes how a word is SPELLED: one byte per sound.  TF1 encodes what a word IS: a
bit-vector of its grammatical features, so that two words can be compared with an AND.
SanskritOS has both layers (SLP1 for the letters, PL128 for the features); TamilOS had
only the first.

Layout, bit index = shift:

    0  SG    1  PL                                     NUMBER
    4  NOM   5  ACC   6  INST  7  SOC                  CASE, in Naṉṉūl's வேற்றுமை order
    8  DAT   9  ABL  10  GEN  11  LOC   (12 VOC: reserved, no data)
   16  BEN  17  SO_RAW  18  INFINC                     EXTENSION
   20  FOC  21  CMPR                                   PARTICLE
   24  SANDHI_K  25 SANDHI_C  26 SANDHI_P  27 SANDHI_T SANDHI

   plane 1, bits 32..63: AGREEMENT (இடம் / திணை / பால்). Defined below, shared with the
   verb register (tools/tf1v.py). For NOUNS it is unpopulated -- no data source exists for
   a noun's திணை or பால் -- so the noun codec refuses to set it.
   plane 2, bits 64..95: VERB morphology (tools/tf1v.py). Nouns leave it zero.
   plane 3, bits 96..127: reserved.

The register is 128 bits wide, one plane per domain, so that a noun's case flag and a
verb's finiteness flag can never share a bit. SanskritOS widened PL64 to PL128 for the same
reason; its header records the aliasing bugs. Draft 1 of TF1 was 64 bits and noun-only; the
noun registers are numerically unchanged by the widening.

Authority: Naṉṉūl 275 (a noun hosts வேற்றுமை and carries திணை, பால் or இடம்), 291-292 (eight
cases, in this order), 297 (ஓடு/ஒடு belong to the third case, hence SOC beside INST).
"""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TABLE = ROOT / "spec/tf1_bundles.tsv"

class TF1Error(ValueError):
    pass

# ------------------------------------------------------------------ field layout
SG, PL = 0, 1
NOM, ACC, INST, SOC, DAT, ABL, GEN, LOC = range(4, 12)
VOC = 12                                     # reserved: nothing in the data
BEN, SO_RAW, INFINC = 16, 17, 18
FOC, CMPR = 20, 21
SANDHI_K, SANDHI_C, SANDHI_P, SANDHI_T = 24, 25, 26, 27

def _m(*bits):
    r = 0
    for b in bits: r |= 1 << b
    return r

NUMBER_MASK  = _m(SG, PL)
CASE_MASK    = _m(NOM, ACC, INST, SOC, DAT, ABL, GEN, LOC)
EXT_MASK     = _m(BEN, SO_RAW, INFINC)
PART_MASK    = _m(FOC, CMPR)
SANDHI_MASK  = _m(SANDHI_K, SANDHI_C, SANDHI_P, SANDHI_T)
DEFINED_MASK = NUMBER_MASK | CASE_MASK | EXT_MASK | PART_MASK | SANDHI_MASK   # the NOUN bits

WIDTH = 128
FULL = (1 << WIDTH) - 1
PLANE0 = 0xFFFFFFFF
PLANE1 = 0xFFFFFFFF << 32
PLANE2 = 0xFFFFFFFF << 64
PLANE3 = 0xFFFFFFFF << 96
# for a NOUN, everything outside the noun bits is reserved: VOC, the whole of plane 1 (no data
# source for a noun's gender), the verb plane, and plane 3
RESERVED_MASK = FULL & ~DEFINED_MASK

# ------------------------------------------------------------------ plane 1: AGREEMENT
# Shared by nouns and verbs. Naṉṉūl 275 gives a noun திணை, பால் or இடம்; 324-338 give each
# verb ending its இடம் and, in the third person, its பால். A verb fills these from its
# person-number-gender slot; a noun cannot yet, for want of data.
TANMAI, MUNNILAI, PADARKKAI = 32, 33, 34            # இடம்   1st, 2nd, 3rd person
UYAR, AKRINAI = 35, 36                              # திணை   rational, non-rational
AAN, PEN, PALAR, ONRU, PALA = 37, 38, 39, 40, 41    # பால்   m, f, rational plural, n sg, n pl
HON = 42                                            # மரியாதை honorific
ANY = 43                                            # "இடம்பால் எங்கும்" -- nūṟpā 338: agrees with every subject
IDAM_MASK  = _m(TANMAI, MUNNILAI, PADARKKAI)
TINAI_MASK = _m(UYAR, AKRINAI)
PAL_MASK   = _m(AAN, PEN, PALAR, ONRU, PALA)
AGR_MASK   = IDAM_MASK | TINAI_MASK | PAL_MASK | _m(HON, ANY)

# the source vocabulary: ThamizhiMorph's atoms, one flag each. `sg` is not an atom in the
# source -- singular is the ABSENCE of `pl` -- so encode() derives SG from it.
ATOM = {"pl": PL, "nom": NOM, "acc": ACC, "inst": INST, "soc": SOC, "dat": DAT,
        "abl": ABL, "gen": GEN, "loc": LOC, "ben": BEN, "so": SO_RAW, "infInc": INFINC,
        "foc": FOC, "cmpr": CMPR, "sandhik": SANDHI_K, "sandhic": SANDHI_C,
        "sandhip": SANDHI_P, "sandhit": SANDHI_T}
_ATOM_OF_BIT = {b: a for a, b in ATOM.items()}
# canonical string order. The source's own order varies (`+dat+pl` in 19 classes,
# `+pl+dat` in one), so decode() is canonical, not a reproduction of the source string.
_CANON = ["infInc", "pl", "nom", "acc", "inst", "soc", "dat", "abl", "gen", "loc", "so",
          "ben", "cmpr", "foc", "sandhik", "sandhic", "sandhip", "sandhit"]

def _pop(x):
    return bin(x).count("1")

# ------------------------------------------------------------------ validity
def check(reg):
    """Raise TF1Error unless `reg` is a well-formed NOUN register: no bit outside the noun layout."""
    if not 0 <= reg < (1 << WIDTH):
        raise TF1Error(f"not a {WIDTH}-bit register: {reg}")
    if reg & RESERVED_MASK:
        raise TF1Error(f"reserved bits set: 0x{reg & RESERVED_MASK:016X}")
    if _pop(reg & NUMBER_MASK) != 1:
        raise TF1Error("a noun register needs exactly one of SG, PL")
    if _pop(reg & (CASE_MASK | _m(SO_RAW))) > 1:
        raise TF1Error("at most one case flag")
    if _pop(reg & SANDHI_MASK) > 1:
        raise TF1Error("at most one sandhi flag")
    if reg & _m(BEN) and not reg & _m(DAT):
        raise TF1Error("BEN only follows DAT")
    return reg

def is_valid(reg):
    try: check(reg); return True
    except TF1Error: return False

# ------------------------------------------------------------------ codec
def atoms(bundle):
    """The atom set of a source bundle string, without the leading `noun`."""
    toks = [t for t in bundle.strip().split("+") if t]
    if not toks or toks[0] != "noun":
        raise TF1Error(f"not a noun bundle: {bundle!r}")
    out = toks[1:]
    if len(set(out)) != len(out):
        raise TF1Error(f"repeated atom in {bundle!r}")
    return out

def encode(bundle):
    reg = 0
    for a in atoms(bundle):
        if a not in ATOM:
            raise TF1Error(f"unknown atom {a!r} in {bundle!r}")
        reg |= 1 << ATOM[a]
    if not reg & _m(PL):
        reg |= _m(SG)                          # singular is the absence of `pl`
    return check(reg)

def decode(reg):
    """Canonical bundle string for a register."""
    check(reg)
    have = [a for a in _CANON if reg & (1 << ATOM[a])]
    return "noun" + "".join("+" + a for a in have)

def to_hex(reg):
    return f"0x{reg:016X}"

# ------------------------------------------------------------------ matching
def has(reg, atom):
    return bool(reg & (1 << ATOM[atom]))

def agree(a, b, mask):
    """True when both registers carry a flag in `mask` and it is the same flag.

    One AND and a nonzero test. For a field that holds at most one flag, which check()
    enforces, this gives the same answer as SanskritOS's shastric_alu, which reduces each
    side's one-hot flags to a 2-bit id and tests (id != 0) && (id_a == id_b). It is a
    different formulation of the same predicate, not that circuit, and neither has been
    synthesised for TamilOS. A field absent from either side never matches."""
    return bool(a & b & mask)

def same_number(a, b): return agree(a, b, NUMBER_MASK)
def same_case(a, b):   return agree(a, b, CASE_MASK)

# ------------------------------------------------------------------ dense bundle code
_TABLE = None
def _table():
    global _TABLE
    if _TABLE is None:
        if not TABLE.exists():
            raise TF1Error(f"{TABLE} missing; run tools/validate_tf1.py --write")
        rows = list(csv.DictReader(TABLE.open(encoding="utf-8"), delimiter="\t"))
        _TABLE = ({int(r["reg"], 16): int(r["code"]) for r in rows},
                  {int(r["code"]): int(r["reg"], 16) for r in rows})
    return _TABLE

def dense(reg):
    """Dense code 0..N-1 for a register in the frozen universe -- the ROM address field."""
    try: return _table()[0][reg]
    except KeyError: raise TF1Error(f"register 0x{reg:016X} is not in the frozen universe")

def from_dense(code):
    try: return _table()[1][code]
    except KeyError: raise TF1Error(f"no bundle has dense code {code}")

def universe_size():
    return len(_table()[0])

if __name__ == "__main__":
    for b in ("noun+nom", "noun+pl+loc", "noun+dat+pl+sandhik", "noun+infInc+dat+ben"):
        r = encode(b)
        print(f"  {b:26s} {to_hex(r)}  {decode(r)}")
