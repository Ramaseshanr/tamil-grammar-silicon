# TLP1 — Tamil Linear Phonemic encoding

**Draft 2** · 2026-10-16 (draft 1: 2026-09-29) · reference implementation `tools/tlp1.py` · validator `tools/validate_tlp1.py`

The SLP1 analogue for Tamil: one byte per phoneme, flat, no abugida.

SanskritOS's byte-level `no_std` kernel is possible because SLP1 gives one byte per
phoneme. Tamil Unicode cannot do that — it is an abugida in which a consonant letter
carries an inherent அ, a pulli kills it, and vowel signs replace it, so a single
"character" may be one phoneme or two. TLP1 is the substrate that makes the same kernel
shape possible for Tamil.

TLP1 is **phonemic, not phonetic**. Tamil script underspecifies voicing (க is [k], [g],
[x] or [h] by position), but that alternation is fully rule-derivable, so it belongs in a
realisation layer, not the encoding. One phoneme, one byte.

---

## 1. Inventory

The classical eḻuttu inventory — 12 உயிர் + 18 மெய் + ஆய்தம் = **31 phonemes** — fits in
5 bits. TLP1 spends a full byte anyway, because the spare bits are what make the grammar's
own categories testable with a mask.

| | |
|---|---|
| உயிர் | 12 — 5 குறில் / 7 நெடில் |
| மெய் | 18 — வல்லினம் 6, மெல்லினம் 6, இடையினம் 6 |
| ஆய்தம் | ஃ |
| grantha (loans) | ஜ ஷ ஸ ஹ ஶ — outside the classical 31, required for real text |

## 2. Byte layout

```
 bit   7  6 | 5  4 | 3 | 2  1  0
      [ CAT ]  ...
```

| CAT | Class | Fields |
|---|---|---|
| `00` | **UYIR** | bit 3 = நெடில் (length) · bits 2–0 = quality |
| `01` | **MEY** | bits 5–4 = இனம் · bits 2–0 = index within இனம் |
| `10` | **EXTRA** | ஆய்தம், grantha |
| `11` | **CTRL** | boundaries |

### Vowels — `00 0 0 L QQQ`

quality `a i u e o ai au` = 0…6; `L` = length.

| | அ | ஆ | இ | ஈ | உ | ஊ | எ | ஏ | ஒ | ஓ | ஐ | ஔ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | `00` | `08` | `01` | `09` | `02` | `0A` | `03` | `0B` | `04` | `0C` | `0D` | `0E` |

ஐ and ஔ are inherently நெடில். The 4 unused combinations (short *ai*, short *au*, and two
spare qualities) are invalid and rejected by the validator.

### Consonants — `01 II 0 PPP`

இனம் `II`: `00` வல்லினம், `01` மெல்லினம், `10` இடையினம்.

| இனம் | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| **வல்லினம்** `40–45` | க் | ச் | ட் | த் | ப் | ற் |
| **மெல்லினம்** `50–55` | ங் | ஞ் | ண் | ந் | ம் | ன் |
| **இடையினம்** `60–65` | ழ் | ய் | ள் | ர் | வ் | ல் |

**The index axis is place of articulation** — velar, palatal, retroflex, dental, labial,
alveolar — and **all three இனம் are aligned on it.** For வல்லினம் and மெல்லினம் this is the
traditional ordering, which already pairs each plosive with its homorganic nasal.

**The place field is not our analysis; it is quoted.** Tolkāppiyam எழுத்ததிகாரம்
பிறப்பியல் gives one pair per nūṟpā, each naming the articulator the two share:

```
 7  ககார ஙகாரம் முதல் நா அண்ணம்.          க ங   root of the tongue, palate    place 0
 8  சகார ஞகாரம் இடை நா அண்ணம்.            ச ஞ   middle of the tongue          place 1
 9  டகார ணகாரம் நுனி நா அண்ணம்.           ட ண   tip of the tongue             place 2
11  நா நுனி பரந்து … தகார நகாரம்           த ந   tongue tip at the teeth       place 3
15  இதழ் இயைந்து பிறக்கும் பகார மகாரம்.    ப ம   the lips meeting              place 4
12  அணரி நுனி நா அண்ணம் ஒற்ற … றஃகான் னஃகான்  ற ன   curled tongue tip          place 5
```

Naṉṉūl 79 compresses the first three into one verse: *கஙவும் சஞவும் டணவும் முதலிடை /
நுனி நா அண்ணம் உற முறை வருமே*. `python3 tools/check_pirappiyal.py` checks the
correspondence mechanically: all six pairs share a place in TLP1, and the six pairs occupy
the six place values exactly once each.

**Draft 2 places இடையினம் on the same scale**, which draft 1 did not. ல் sits at alveolar
(5) and ள் at retroflex (2), the places of the consonants they alternate with, so
ல் → ற்/ன் and ள் → ட்/ண் preserve the place field. ய் (palatal) and வ் (labial) are at
their true places too. **ழ் and ர் take the velar and dental slots, which இடையினம் leaves
empty, and those two placements are arbitrary** — neither takes part in a place-preserving
alternation, so nothing reads their place. The place field is phonetically true for 16 of
18 மெய், against 12 of 18 in draft 1.

### Extra and control

| | |
|---|---|
| `80` | ஆய்தம் ஃ |
| `90`–`94` | ஜ ஷ ஸ ஹ ஶ (க்ஷ decomposes to க் + ஷ) |
| `C0` | morpheme boundary — the `^` of the foma sources |
| `C1` | word boundary |
| `C2` | pada / compound boundary |

## 3. Why the layout is this way

The grammar's rules are stated over இனம் and over length. Both become single operations:

```c
is_vallinam(b)   (b & 0xF0) == 0x40
is_mellinam(b)   (b & 0xF0) == 0x50
is_idaiyinam(b)  (b & 0xF0) == 0x60
lengthen(v)      v |  0x08                      /* குறில் -> நெடில் */
shorten(v)       v & ~0x08
to_inam(c,i)     (c & 0x07) | 0x40 | i          /* keep the place, change the இனம் */
nasalize(c)      to_inam(c, 0x10)               /* -> homorganic மெல்லினம் */
harden(c)        to_inam(c, 0x00)               /* மெய்யீற்றுப் புணரியல் [Naṉṉūl 227] */
assimilate(n,f)  (n & ~0x07) | (f & 0x07)
```

### The case for the encoding

`tamil-noun.foma` R12, the rule behind மரம் + கள் → மரங்கள்:

```foma
define R12 {ம்} -> 0 || _ "^" [{ங்க}];    # delete ம், let the suffix spell ங்க
```

It must *delete* ம் and have the suffix carry ங்க, because Tamil orthography cannot express
"change this nasal's place of articulation." The phonemic form is one operation:

```
ம் 0x54 (மெல்லினம், labial)    க் 0x40 (வல்லினம், velar)
assimilate: (0x54 & ~0x07) | (0x40 & 0x07) = 0x50 = ங்   →  மரங்கள் ✓
```

and the *same* operation covers every place, where the orthographic grammar needs a
separate delete-rule for each:

```
ம் + க → ங்   ம் + ச → ஞ்   ம் + ட → ண்   ம் + த → ந்   ம் + ப → ம்   ம் + ற → ன்
```

> ⚠️ That six-way generalisation is a **prediction the encoding makes**, not an attested
> fact. ம் + ப → ம் and ம் + க → ங் are secure; ம் + ற → ன் is not something the audit has
> confirmed. Treat the full series as a hypothesis to test against `verbs_gold.tsv` and
> `nouns_grid.tsv` before it is wired into a kernel. Where the encoding over-predicts, that
> is a finding, not a defect in the encoding.
>
> **Tested — `docs/RULES.md` §3.** The noun grid attests exactly one of the six
> (ங், 2,448 cells) and refutes the rule's unrestricted form: **ண் + க் must not assimilate**
> (கண் + கள் is கண்கள்). The operation is restricted to ம் in `tools/phon_rules.py`. The mask
> still computes the series; there is no licence to apply it. Five sixths remain open.

## 4. Boundary semantics

An independent vowel directly after a மெய் is a **compound seam**. Well-formed Tamil writes
a mid-word vowel as a sign, so the independent form means a junction that puṇarcci has not
been applied across. The encoder emits `C2` there.

Without it the encoding is lossy — `ஆண்` + `ஆட்சி` and `ஆணாட்சி` would collapse to the same
bytes. 92 such unsegmented compounds exist in `Nouns.lexc`; the round trip found them.

## 5. Validation — measured

`python3 tools/validate_tlp1.py`, Unicode → TLP1 → Unicode, NFC-normalised identity:

| Corpus | Tokens | Round-trip OK | Mismatches | Not representable |
|---|---:|---:|---:|---:|
| Noun stems (`Nouns.lexc`) | 44,197 | 44,076 (99.73%) | **0** | 121 |
| Generated verb forms | 1,780,404 | 1,689,283 (94.88%) | **0** | 91,121 |
| UD treebank tokens | 13,043 | 11,220 (86.02%) | **0** | 1,823 |
| **Total** | **1,837,644** | — | **0** | — |

**Zero mismatches.** TLP1 is lossless for every well-formed Tamil token in the staged gold.

The residue is correctly rejected, and the rejections are informative:

- **121 noun stems** — TSCII→Unicode damage (`ப10வை` for `பூவை`, `அரு(மை`). Already known.
- **91,121 generated verb forms (5.1%)** — orphan vowel signs and orphan pulli:
  `அஃகியிருும்` (doubled ு), `கொ்ச்சி` (pulli with no base). **This is new.** These are
  ThamizhiMorph generation artefacts, not Tamil.
- **1,823 UD tokens** — punctuation and digits, expected in running text.

### Consequence for the ratchet

**40,143 of the 1,339,024 round-trip-verified gold surfaces (3.00%) are malformed Tamil.**
They survive the FST round trip because the transducer is self-consistent, and TLP1 rejects
them anyway. Round-trip consistency is *not* well-formedness, and the two checks are
independent. Ratchet against the intersection:

> **1,298,881 clean verified verb surfaces.**

Listed in `data/derived/verbs_gold_malformed.txt`.

## 6. Non-Tamil in running text

TLP1 encodes Tamil only. Punctuation, digits and Latin have no code points and `encode()`
raises. Callers segment first — `tlp1.is_tamil(tok)` gates a token. This is deliberate: a
passthrough category would let mojibake into the kernel silently, and the 91,121 forms above
show that is a live risk, not a theoretical one.

## 7. Open for draft 2

1. ~~**Test the assimilation series** (§3) against the gold; record where it over-predicts.~~
   **Done** — `docs/RULES.md` §3. It over-predicts: only ம் is licensed, and ண்
   must be excluded. ண் is not hardened either, and nasal loss applies before ச் ட் த் ப் only.
2. **Decide grantha's status.** Currently `EXTRA`, outside the இனம் lattice, so no rule can
   match them by class. Correct for centamiḻ; probably wrong for modern text.
3. **ஔ and ஐ as units vs. diphthongs.** Encoded as single long vowels, per Tolkāppiyam.
   Revisit if puṇarcci rules need to see their second mora.
4. ~~**Bit 3 of MEY is unused**~~ — still unused, and deliberately so. The draft-2 re-layout
   was done **without** spending it: ல் and ள் needed places 5 and 2, and இடையினம் had two
   free slots for ழ் and ர். So bit 3 remains available for its candidate use, a gemination
   flag that would make க்க் one byte rather than two.
6. ~~**Re-express `tamil-noun.foma`'s 19+6 rules phonemically** and diff the outputs against
   `nouns_grid.tsv`.~~ **Done** — `tools/phon_rules.py`, `docs/RULES.md`.
   **1,637 orthographic parameters → 114 phonemic**, deriving a reference surface in
   **99.23%** of the 1,554,418 cells (surface precision 96.38% when one form is generated
   per cell; figures as of 2026-10-22, kept current in `docs/RULES.md`). **Eleven of the 28 foma rules never fire**, and **six have no phonemic content
   at all** — they delete a pulli before a vowel sign, which in TLP1 is not a deletion but a
   non-event. Four gold defects fell out of the diff.


---

## The mask-and-OR claim, and how draft 1 got it wrong

Draft 1 asserted that homorganic nasalisation was "one mask and one OR". **It was true only
for the வல்லினம் series**, and the failure is worth keeping on the record because of how it
surfaced.

`nasalize(b) = b | INAM_MEL` works for க் → ங் because draft 1 aligned வல்லினம் and
மெல்லினம் on place. இடையினம் was numbered on its own ordinal scale, so ல் sat at place 2
and ன் at place 5. Applying the same expression to ல் set both இனம் bits and produced
`0x72`, which is not a phoneme at all; `decode()` raised `KeyError 114`.

It was found by `tools/add_nurpa327.py` deriving சென்மார் and கொண்மார் — **a 13th-century
nūṟpā was a better test of the encoding than 1.8M tokens of corpus had been.** Then the
மெய்யீற்றுப் புணரியல் hardening rule (**Naṉṉūl 227**) hit the
identical problem independently, and two separate rules were carrying explicit pair maps for
one layout decision.

> **Citation corrected.** Both operations were first cited to **Naṉṉūl 237**
> (*னல முன் றனவும் / ணள முன் டணவும்*), which is about த and ந changing *after* ன்/ல்/ண்/ள்.
> The rule that actually governs them is **227**:
>
> > ல ள வேற்றுமையில் ற டவும் அல்வழி / அவற்றோடு உறழ்வும் வலிவரினாம் மெலி / மேவின் ன ணவும் இடைவரின் இயல்பும் / ஆகும் இருவழியானும்
>
> ல் and ள் become ற் and ட் in வேற்றுமை; they alternate (**உறழ்வு**) in அல்வழி; before a
> **மெல்லினம்** they become ன் and ண்; before an **இடையினம்** they are unchanged. One nūṟpā
> specifies the hardening, the nasalisation *and* the alternation — which is to say it
> specifies `harden()`, `nasalize()` and the B/C register split, and under draft 2 all
> three are the same two instructions with a different இனம் constant.

**Draft 2 removes both.** ல் moves to place 5 and ள் to place 2, and

```
nasalize(c) = (c & 0x07) | 0x50        harden(c) = (c & 0x07) | 0x40
```

holds for every மெய், in both series, with no table. Verified behaviour-preserving: the
derivation reproduces draft 1 to the digit — 1,542,530 / 1,554,418 cells, recall 95.64%,
precision 54.62%, UD 632/740 (measured on 2026-10-16, when the change was made; later fixes have
moved every one of these figures) — because the encoding is internal and every boundary is
Unicode.

One defect in the change is worth recording too. `tools/phon_rules.py` read its phoneme
constants as `0x60 | i`, which assumed the draft-1 ordering; the re-layout silently turned
`RA` into ய் and rewrote every உயர்திணை plural, costing 25 points of cell agreement. The
"nothing may move" check caught it. Those constants now come from `T.encode`, never from an
assumed order.
