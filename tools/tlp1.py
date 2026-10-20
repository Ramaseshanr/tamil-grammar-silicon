#!/usr/bin/env python3
"""
TLP1 -- Tamil Linear Phonemic encoding, one byte per phoneme.

The SLP1 analogue for Tamil. Tamil Unicode is an abugida: a consonant letter
carries an inherent அ, a pulli kills it, vowel signs replace it. That is fine for
display and hostile to a byte-level kernel. TLP1 flattens text to a phoneme
sequence in which the classical eluttu categories are BIT FIELDS, so the tests
the grammar actually performs are single mask operations.

    bit   7 6 | 5 4 | 3 2 1 0
          CAT |   VALUE

    CAT 00 UYIR   (vowel)      bit3 = nedil/length, bits2-0 = quality
    CAT 01 MEY    (consonant)  bits5-4 = inam, bits2-0 = index within inam
    CAT 10 EXTRA  (aytam, grantha)
    CAT 11 CTRL   (boundaries)

Vallinam and mellinam share their index axis as PLACE, in the traditional
order velar/palatal/retroflex/dental/labial/alveolar, so a plosive and its
homorganic nasal differ by exactly one bit.
"""

import unicodedata

# ---------------------------------------------------------------- categories
CAT_UYIR, CAT_MEY, CAT_EXTRA, CAT_CTRL = 0x00, 0x40, 0x80, 0xC0
CAT_MASK = 0xC0

INAM_VAL, INAM_MEL, INAM_IDAI = 0x00, 0x10, 0x20     # vallinam / mellinam / idaiyinam
INAM_MASK = 0x30
NEDIL = 0x08                                          # vowel length bit

MORPH_BOUNDARY = 0xC0     # '^' in the foma sources
WORD_BOUNDARY  = 0xC1
PADA_BOUNDARY  = 0xC2

# quality indices
A, I, U, E, O, AI, AU = 0, 1, 2, 3, 4, 5, 6

def uyir(q, long_):  return CAT_UYIR | (NEDIL if long_ else 0) | q
def mey(inam, idx):  return CAT_MEY | inam | idx

# ---------------------------------------------------------------- inventory
# 12 uyir
_V = {
    "அ": uyir(A, 0),  "ஆ": uyir(A, 1),
    "இ": uyir(I, 0),  "ஈ": uyir(I, 1),
    "உ": uyir(U, 0),  "ஊ": uyir(U, 1),
    "எ": uyir(E, 0),  "ஏ": uyir(E, 1),
    "ஒ": uyir(O, 0),  "ஓ": uyir(O, 1),
    "ஐ": uyir(AI, 1), "ஔ": uyir(AU, 1),          # inherently nedil
}
# dependent vowel signs -> same phonemes
_SIGN = {
    "ா": uyir(A, 1), "ி": uyir(I, 0), "ீ": uyir(I, 1),
    "ு": uyir(U, 0), "ூ": uyir(U, 1), "ெ": uyir(E, 0),
    "ே": uyir(E, 1), "ை": uyir(AI, 1), "ொ": uyir(O, 0),
    "ோ": uyir(O, 1), "ௌ": uyir(AU, 1),
}
# 18 mey, in the traditional order, place-aligned across vallinam/mellinam
_VALLINAM = ["க", "ச", "ட", "த", "ப", "ற"]
_MELLINAM = ["ங", "ஞ", "ண", "ந", "ம", "ன"]
# DRAFT 2. இடையினம் is placed on the SAME place scale as the other two series, not on an
# ordinal one, so that ல்/ள் sit at the place of the consonants they alternate with:
#   ல் -> ற் / ன்  (alveolar, 5)      ள் -> ட் / ண்  (retroflex, 2)
# ய் (palatal) and வ் (labial) are at their true places too. ழ் and ர் take the velar and
# dental slots, which இடையினம் leaves empty; those two placements are arbitrary, and that
# is the price of the layout -- the place field is phonetically true for 16 of 18 மெய்,
# against 12 of 18 in draft 1. Neither ழ் nor ர் takes part in a place-preserving
# alternation, so nothing reads their place.
_IDAIYINAM = ["ழ", "ய", "ள", "ர", "வ", "ல"]
PLACE_NAMES = ["velar", "palatal", "retroflex", "dental", "labial", "alveolar"]

_C = {}
for i, ch in enumerate(_VALLINAM):  _C[ch] = mey(INAM_VAL, i)
for i, ch in enumerate(_MELLINAM):  _C[ch] = mey(INAM_MEL, i)
for i, ch in enumerate(_IDAIYINAM): _C[ch] = mey(INAM_IDAI, i)

AYTAM = CAT_EXTRA | 0x00
_GRANTHA = {"ஜ": 0x90, "ஷ": 0x91, "ஸ": 0x92, "ஹ": 0x93, "ஶ": 0x94}

PULLI = "்"

# reverse tables
_R_V     = {v: k for k, v in _V.items()}
_R_SIGN  = {v: k for k, v in _SIGN.items()}
_R_C     = {v: k for k, v in _C.items()}
_R_GRAN  = {v: k for k, v in _GRANTHA.items()}

# ---------------------------------------------------------------- predicates
def is_uyir(b):      return (b & CAT_MASK) == CAT_UYIR
def is_mey(b):       return (b & CAT_MASK) == CAT_MEY
def is_vallinam(b):  return (b & (CAT_MASK | INAM_MASK)) == (CAT_MEY | INAM_VAL)
def is_mellinam(b):  return (b & (CAT_MASK | INAM_MASK)) == (CAT_MEY | INAM_MEL)
def is_idaiyinam(b): return (b & (CAT_MASK | INAM_MASK)) == (CAT_MEY | INAM_IDAI)
def is_nedil(b):     return is_uyir(b) and bool(b & NEDIL)
def is_kuril(b):     return is_uyir(b) and not (b & NEDIL)
def place(b):        return b & 0x07

# ------------------------------------------------- single-op rule primitives
def lengthen(b):     return b | NEDIL             # kuril -> nedil
def shorten(b):      return b & ~NEDIL            # nedil -> kuril
def to_inam(b, inam):
    """Move a மெய் to another இனம், keeping its place. One AND, one OR.

    Draft 2 makes this uniform across all three series. In draft 1 it held only for
    வல்லினம் -> மெல்லினம்; ல் and ள் were numbered on an ordinal scale, so the same
    expression produced 0x72, which is not a phoneme, and both `nasalize` and the
    மெய்யீற்றுப் புணரியல் hardening rule needed explicit pair maps."""
    return (b & 0x07) | CAT_MEY | inam

def nasalize(b):     return to_inam(b, INAM_MEL)  # -> homorganic மெல்லினம்
def harden(b):       return to_inam(b, INAM_VAL)  # [Naṉṉūl 227]
def assimilate(nasal, following):
    """Give `nasal` the place of `following`. maram+kal -> marangkal is
    0x54 -> 0x50 : one mask, one or."""
    return (nasal & ~0x07) | (following & 0x07)

# ---------------------------------------------------------------- transcode
class TLP1Error(ValueError):
    pass

def encode(text, strict=True):
    """Tamil Unicode -> TLP1 bytes."""
    s = unicodedata.normalize("NFC", text)
    out = bytearray()
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch in _C or ch in _GRANTHA:
            out.append(_C.get(ch) if ch in _C else _GRANTHA[ch])
            i += 1
            if i < n and s[i] == PULLI:
                i += 1                              # pure mey
            elif i < n and s[i] in _SIGN:
                out.append(_SIGN[s[i]]); i += 1
            else:
                out.append(_V["அ"])                 # inherent vowel
            continue
        if ch in _V:
            # An independent vowel directly after a mey is a compound seam: in
            # well-formed Tamil a vowel mid-word is written as a sign, so the
            # independent form marks a morpheme junction that puNarcci has not
            # been applied across. Record it, or the two spellings collapse
            # (aaN + aaTci -> aaNaaTci) and the encoding stops being lossless.
            if out and is_mey(out[-1]):
                out.append(PADA_BOUNDARY)
            out.append(_V[ch]); i += 1; continue
        if ch == "ஃ":
            out.append(AYTAM); i += 1; continue
        if ch.isspace():
            out.append(WORD_BOUNDARY); i += 1; continue
        if ch == "^":
            out.append(MORPH_BOUNDARY); i += 1; continue
        if strict:
            raise TLP1Error(f"not Tamil: {ch!r} (U+{ord(ch):04X}) at {i}")
        i += 1
    return bytes(out)

def decode(bs):
    """TLP1 bytes -> Tamil Unicode."""
    out, pending = [], None       # pending = consonant letter awaiting its vowel
    def flush():
        nonlocal pending
        if pending is not None:
            out.append(pending + PULLI); pending = None
    for b in bs:
        if is_mey(b) or b in _R_GRAN:
            flush()
            pending = _R_C[b] if b in _R_C else _R_GRAN[b]
        elif is_uyir(b):
            if pending is not None:
                out.append(pending if b == _V["அ"] else pending + _R_SIGN[b])
                pending = None
            else:
                out.append(_R_V[b])
        elif b == AYTAM:
            flush(); out.append("ஃ")
        elif b == WORD_BOUNDARY:
            flush(); out.append(" ")
        elif b == MORPH_BOUNDARY:
            flush(); out.append("^")
        elif b == PADA_BOUNDARY:
            flush()
        else:
            raise TLP1Error(f"unknown TLP1 byte 0x{b:02X}")
    flush()
    return "".join(out)

def is_tamil(text):
    """True if every character is representable in TLP1."""
    try:
        encode(text); return True
    except TLP1Error:
        return False

def roundtrip(text):
    return decode(encode(text)) == unicodedata.normalize("NFC", text)

# ---------------------------------------------------------------- debugging
def name(b):
    if is_uyir(b):
        q = "aiueo"[b & 7] if (b & 7) < 5 else ("ai" if (b & 7) == AI else "au")
        return f"{q}{'ː' if b & NEDIL else ''}"
    if is_mey(b):
        inam = {INAM_VAL: "val", INAM_MEL: "mel", INAM_IDAI: "idai"}[b & INAM_MASK]
        return f"{_R_C[b]}({inam},{PLACE_NAMES[place(b)] if (b & INAM_MASK) != INAM_IDAI else place(b)})"
    if b == AYTAM: return "aytam"
    if b in _R_GRAN: return f"{_R_GRAN[b]}(grantha)"
    return {MORPH_BOUNDARY: "^", WORD_BOUNDARY: "␣", PADA_BOUNDARY: "‖"}.get(b, f"?{b:02X}")

def dump(text):
    bs = encode(text)
    return " ".join(f"{b:02X}:{name(b)}" for b in bs)

if __name__ == "__main__":
    import sys
    for w in (sys.argv[1:] or ["மரம்", "மரங்கள்", "தமிழ்"]):
        print(f"{w}\n  {dump(w)}\n  roundtrip: {roundtrip(w)}")
