# TF1 — the Tamil feature register (noun side)

**Draft 1** · 2026-10-18 · codec `tools/tf1.py` · validator `tools/validate_tf1.py` ·
frozen table `spec/tf1_bundles.tsv`

TLP1 encodes how a word is **spelled**, one byte per sound. TF1 encodes what a word **is**:
a 64-bit register of its grammatical features, so that two words can be compared with an AND
rather than by parsing strings.

SanskritOS has both layers: SLP1 for the letters and **PL128** for the features, a 128-bit
register per word with dedicated planes for morphology, kāraka, it-saṃjñā and phonology.
TamilOS had only the first layer. In the grids the features are text (`noun+pl+loc`), and
the only feature-like bits on the chip are the declension class and an `ok` flag. TF1 is the
missing layer. This draft covers **nouns only**, because that is what the data supports.

TF1 borrows PL128's discipline — one-hot flags, a plane per domain so that fields cannot
alias — and nothing else. PL128's own header records aliasing bugs fixed by giving each
domain its own plane, and that is the lesson taken.

## 1. Where the layout comes from

The planes are not chosen for convenience. Naṉṉūl says what a noun is:

> **275** இடுகுறி காரணம் மரபோடு ஆக்கம் / தொடர்ந்து தொழில் அல காலம் தோற்றா /
> **வேற்றுமைக்கு இடனாய்த் திணைபால் இடத்து ஒன்று / ஏற்பவும் பொதுவும் ஆவன பெயரே**

A noun (பெயர்) is a word that shows no tense, serves as the host of **வேற்றுமை**, and takes one
of **திணை, பால், இடம்**, whether specifically or in common. So the grammar assigns a noun two
groups of features, and TF1 has two planes to match.

| plane | group | source |
|---|---|---|
| 0 | number, வேற்றுமை, and the morphological extensions | **291–292, 297**; the data |
| 1 | திணை, பால், இடம் | **275**; **no data source** — reserved |

The eight cases and their order:

> **291** வேற்றுமை செய்வன எட்டே வேற்றுமை
> **292** பெயரே ஐ ஆல் கு இன் அது கண் / விளி என்று ஆகும் அவற்றின் பெயர் முறை

and the sociative ஓடு/ஒடு belongs to the **third** case:

> **297** மூன்றாவதன் உருபு ஆல் ஆன் ஓடு ஒடு / கருவி கருத்தா உடனிகழ்வு அதன்பொருள்

That is why `SOC` sits beside `INST` in the register: ThamizhiMorph lists the sociative as a
case of its own, Naṉṉūl does not.

## 2. Layout

Bit index is the shift. Bits not listed are **reserved**, and `check()` rejects any register
that sets one.

```
 plane 0                                                         
   0  SG      1  PL                                  NUMBER      exactly one
   4  NOM     5  ACC     6  INST    7  SOC           CASE        at most one,
   8  DAT     9  ABL    10  GEN    11  LOC                        in வேற்றுமை order
  12  VOC     reserved: eighth case, nothing in the data
  16  BEN    17  SO_RAW 18  INFINC                   EXTENSION
  20  FOC    21  CMPR                                PARTICLE
  24  SANDHI_K  25 SANDHI_C  26 SANDHI_P  27 SANDHI_T  SANDHI      at most one

 plane 1 (bits 32..63)   RESERVED. திணை, பால், இடம் — see §5.
```

Number is **explicit** — `SG` and `PL` — although the source has only `pl`. In the grids
singular is the absence of the atom, so `encode()` sets `SG` when `pl` is absent. An explicit
flag is what lets a match say "both are plural" instead of "neither is marked".

`INFINC` and `SO_RAW` record ThamizhiMorph analysis markers (the சாரியை-bearing oblique, and
§4.3) and are not claims about Tamil.

### Invariants, enforced by `check()`

1. no reserved bit set, including `VOC` and all of plane 1;
2. exactly one of `SG`, `PL`;
3. at most one case flag, counting `SO_RAW` as a case flag;
4. at most one sandhi flag;
5. `BEN` only with `DAT`.

## 3. The data it has to carry

`nouns_grid_final.tsv`, 1,554,418 rows:

```
bundle strings      67
atoms               18   8 cases, ben, so, pl, foc, cmpr, infInc, 4 sandhi
registers           66   (one set-level collision, §4.1)
(class, bundle)    713   pairs actually populated
```

Every row is covered, every bundle encodes and validates, and `encode(decode(r)) == r`.

### The dense code and the ROM address

The 66 registers get **dense codes 0 to 65**, frozen in `spec/tf1_bundles.tsv` in ascending
register order. The code fits **7 bits**, so the address into a suffix ROM is

```
{ class[4:0], code[6:0] }   =   12 bits
```

The grid has 20 declension classes, so 20 × 66 = 1,320 addresses are possible and 713 are
populated. `validate_tf1.py` fails if the grid and the frozen table disagree, so the address
field cannot drift silently. That guard was tested by corrupting the table: the validator
exits 2 with the corrupted table and 0 with the real one.

**This is not the 805-pointer figure** quoted in `docs/HARDWARE.md`. That sizing counted
(class, stem-form, variant, bundle) tuples, and 713 counts (class, bundle) pairs. The two
measure different things and should not be compared.

## 4. Three things the data forced

### 4.1 One collision, and it is harmless

`noun+dat+pl` and `noun+pl+dat` are the same atom set, so they get the same register,
`0x0000000000000102`. The first occurs in 19 classes and the second in exactly one, **C5pl**,
the plural-only stems such as குடிமக்கள். **No class holds both**, so the (class, bundle) to
(class, register) map is injective — 713 pairs to 713 — and the ROM address is unambiguous.
The collapse is also linguistically right: both are the dative plural, and the order is
ThamizhiMorph's lexc writing it two ways.

Because source order varies, `decode()` returns a **canonical** string, not the source
string. Equality is checked on atom sets.

### 4.2 No case is not nominative

`noun+foc` and `noun+pl+foc` carry no case atom, and **43,691 rows each** use them, beside
`noun+nom+foc` with 26,957 and `noun+pl+nom+foc` with 1,071. They are distinct bundles in the
source and are kept distinct: an unmarked case is **not** `NOM`. Whether the lexicon means
them to be the same analysis is a question about ThamizhiMorph, and the register does not
settle it by merging them. A field absent from either side never matches, so two unmarked
words do not "agree in case".

### 4.3 `noun+so` is probably a typo, and is kept anyway

1,605 rows carry `so`, always with the suffix ுடன், the same as `soc`'s second form. It looks
like a mistyped `soc`. It has its own flag, `SO_RAW`, so the register is lossless, and the
suspicion is recorded here and not acted on.

## 5. What is not here

**Plane 1 is reserved and empty.** Naṉṉūl 275 says a noun takes திணை, பால் or இடம், and
nūṟpā 265 (*படர்க்கை வினைமுற்று நாமம் குறிப்பின் / பெறப்படும் திணைபால் அனைத்தும்*) ties the third-person finite verb to திணை and பால் as something obtained from the noun or by implication. That is a reading, and the direction of it is not settled here. The intended fields are
திணை (2 flags: உயர்திணை, அஃறிணை), பால் (5: ஆண், பெண், பலர், ஒன்று, பல) and இடம் (3: தன்மை,
முன்னிலை, படர்க்கை). **There is no data source for a noun's திணை or பால்.**
`Nouns.lexc` holds a stem and a declension class and nothing else. Some classes hint at it
(C11 is the ன்-final rational masculines, C5 is பலர்), but that is an inference and not a
stored fact, and the codec refuses to set these bits so it cannot be mistaken for one.

Tamil agreement is also not Sanskrit's. Gender does not show in the noun's declension. It
shows on the **verb**, as one of the 12 person-number-gender endings in the verb grid (`1sg
1pl 2sg 2pl 2sgh 3sgm 3sgf 3sge 3sghe 3sgn 3ple 3pln`). A noun-to-verb check therefore needs
both the missing noun field and a verb-side register.

**Verbs have no register at all**, and this draft says nothing about them.

**No hardware.** `agree()` is a software predicate: one AND and a nonzero test. For a field
holding at most one flag it gives the same answer as SanskritOS's `shastric_alu`, which
reduces each side's one-hot flags to a 2-bit id and tests `(id != 0) && (id_a == id_b)`. It is
a different formulation of the same predicate, not that circuit. Neither has been synthesised
for TamilOS, and there is no LUT figure for TF1.

## 6. Open

1. **A source for திணை and பால்.** The one external candidate is the UD treebank, which tags
   gender on nouns, but it is non-commercial and overlaps only 740 of our lemmas.
2. **Is `noun+foc` the same analysis as `noun+nom+foc`?** §4.2. Needs a reading of the
   lexicon's intent.
3. **`so` against `soc`.** §4.3.
4. **`INFINC` is an analysis marker**, and a register for generation might prefer to derive
   it from the class rather than carry it.
5. **A verb register**, with the 12 endings as the person-number-gender plane.
6. **Incidental, in the source and not in TF1:** the C5pl dative plural lists
   *குடிமக்கடுக்கு* beside குடிமக்களுக்கு. The first is not a word, and looks like a hardening
   rule firing on a plural stem. It has not been investigated.

---

# 7. Draft 2 — the verb side

**2026-10-18** · codec `tools/tf1v.py` · validator `tools/validate_tf1v.py` · frozen table
`spec/tf1v_bundles.tsv`

TF1 is now **128 bits**, one plane per domain, so a noun's case flag and a verb's finiteness
flag can never share a bit. Noun registers are numerically unchanged, and `spec/tf1_bundles.tsv`
is byte-identical.

| plane | bits | domain |
|---|---|---|
| 0 | 0–31 | noun morphology (§2); bits 0,1 `SG`,`PL` are shared |
| 1 | 32–63 | **agreement**, shared: இடம் 32–34, திணை 35–36, பால் 37–41, `HON` 42, `ANY` 43, and the twelve raw person-number-gender slots 48–59 |
| 2 | 64–95 | verb morphology |
| 3 | 96–127 | reserved |

## 7.1 Features and exponents

The `=value` part of a source atom (`past=ட்`, `3sgm=அன்`) is the **exponent**, the surface morph
that realises a feature. It is not a feature and nobody ANDs it. The register holds features;
a separate **dense code over the full source string** carries the exponent: 715 strings, 10 bits.

```
grid 1,318,782 rows · 715 feature strings · 45 atoms · 233 registers
up to 16 exponent combinations share one register
ROM address {class[4:0], code[9:0]} = 15 bits;  2,817 of 14,300 addresses populated
```

Plane 2: `FIN NONFIN` (64–65), tense `PAST PRES FUT FUTADJPART` (66–69), mood `IMP OPT NEG CON`
(70–73), particle `MOODPART NEGPART ADJPART VPART INF` (74–78), voice `CAUS PASSIVE MIDDLE
COMPLEX SIM AUX` (79–84), class markers `STRONG WEAK` (85–86), `EUPH` (87), sandhi (88–91) and
`SANDHI_HYPHEN` (92, a spelling flag: the source writes both `sandhik` and `sandhi-k`).

## 7.2 What was measured

- All 715 strings encode and **round-trip exactly as features**. The noun side could only
  round-trip atom sets, because noun atom order varies. Verb strings obey **one global atom
  order**: 45 atoms, acyclic, no pair in both orders, 0 of 715 violate it.
- **`complex` and `passive` are the same set**, 184 strings each. One is redundant and both
  are kept so the register is lossless.
- 715 strings give 233 registers and 233 atom sets, so no distinction was lost or merged.

## 7.3 A wrong inference, caught by testing it

I first assumed tense is tied to finiteness, from two counts that happened to match (632
finite strings and 632 with a tense atom). It is not:

- **13 registers are finite with no tense**: the imperatives, the optatives, and the
  `3ple=மார்` forms, whose விகுதி carries the future itself.
- **6 registers are non-finite with a tense**: the tensed participles, e.g.
  `past=ட்+adjpart=அ`.

So the invariant is *at most one tense flag*, and the validator asserts only invariants it has
checked against the data. Sandhi flags occur on **no** finite form, and that is asserted too.

## 7.4 Agreement

A verb's PNG slot fills plane 1 by `PNG_MAP` in `tf1v.py`, each row anchored to a verse (325
ஆண்பால், 326 பெண்பால், 327 பல்லோர் படர்க்கை, 328 ஒன்றன், 329 பலவின், 331–332 தன்மை, 335 and 337
முன்னிலை). A first- or second-person slot sets இடம் and number only, because Naṉṉūl **324**
gives பால் only to the third person.

**The optative takes every subject.** Nūṟpā **338** says it agrees *இடம்பால் எங்கும்*, so an
optative with no PNG slot carries `ANY` and `agrees()` returns true for any subject, even an
empty one. A participle states no agreement and `agrees()` raises, since "does not agree" and
"is not an agreeing form" are different answers.

`agrees(subject, verb)` is a software predicate: the subject must carry every இடம், திணை, பால்
and number flag the verb carries, and `HON` is a property of the verb form that the subject is
not required to share. **It has been tested on synthetic subjects only**, because no noun has
plane-1 data (§5), and nothing has been synthesised.

## 7.5 Open

1. **Number for `3sge`, `3sghe` and `2sgh`.** I took ThamizhiMorph's labels as given, which
   give the *referent's* number. The verb *form* is the plural-rational ending of 327 and 337.
   A noun-to-verb match must choose between semantic and grammatical number. **Undecided.**
2. **`3sge`, `3sghe` and `3ple` all map to பலர்பால்**, anchored to 327, whose endings அர் ஆர் ப
   மார் the project's own citation layer already assigns to all three. That mapping is mine.
3. **Two imperative strings have no PNG slot** (`imp+neg+euph`), although Naṉṉūl 335–336 makes
   the imperative second person. They could be derived, and are not, because that would go
   beyond the data.
4. **`மார் forms carry no tense flag`**, although the விகுதி marks the future. The register
   records what the string says.
5. **`strong` and `weak` are class markers of the root**, not features of the form, and are
   carried because the source string carries them.
6. **Not built:** a noun source for plane 1, any hardware, and any LUT figure.
