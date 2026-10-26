# The noun rules, stated over phonemes

`tools/phon_rules.py` derives a noun's declension over TLP1 bytes (one byte per sound, [spec/TLP1.md](../spec/TLP1.md)).
It restates the 28 rewrite rules and 1,609 stored suffix spellings of ThamizhiMorph's `tamil-noun.foma` as a small set of
sound rules, and is measured against the full grid of 1,554,418 stem-and-case cells.

```
python3 tools/phon_rules.py count     # parameter counts
python3 tools/phon_rules.py orth      # the foma reimplementation (see the note on the grid below)
python3 tools/phon_rules.py phon      # derive phonemically and compare with the reference grid
python3 tools/phon_rules.py vikarpam  # the licensed-alternant (விகற்பம்) measurement
```

## The reference, reimplemented first

To measure against what ThamizhiMorph's rules actually do, the 28 rules were reimplemented in Python as an ordered
composition. Run against the unpatched ThamizhiMorph grid (`TAMILOS_GRID=data/derived/nouns_grid.tsv`), it reproduces
**1,554,407 of 1,554,418 cells (99.9993%)**. The 11 differences are one stem, கடல், declared in two classes. Eleven of the
28 rules never fire on the grid.

## The phonemic restatement

Three stages over TLP1 bytes: a stem-form per declension class, one உருபு per feature, and juncture rules where two
morphs meet. The rules with their sources of authority:

| | rule | replaces |
|---|---|---|
| P1 | assimilation: a மெல்லினம் takes the place of a following வல்லினம் (the place bits of TLP1; Tolkāppiyam பிறப்பியல் 7–9) | R12 |
| P2 | hardening before a வல்லினம்: ல்→ற், ள்→ட் (Naṉṉūl 227), and ன்→ற் | R8 R9 R10 R16 |
| P3 | nasal loss at a pada juncture | R17 R18 |
| P4 | வல்லினம் மிகல்: the suffix-initial வல்லினம் doubles after a vowel | lexicon |
| P5 | hiatus: a குற்றியலுகரம் drops before a vowel (Naṉṉūl 164) | R4, Cleanup1 |
| P6 | உடம்படுமெய்: ய் after a front vowel, வ் otherwise | lexicon |
| P8 | ன் → ர் before கள் (the உயர்திணை plural) | R6 |
| P9 | coalescence: மர + அத்து → மரத்து (Naṉṉūl 252; அத்து is listed in 244) | R13 |
| P10 | a clitic doubles its initial வல்லினம் after a vowel | lexicon |
| P11 | ஒற்று இரட்டல்: the final ஒற்று doubles before a vowel உருபு | lexicon |
| P12 | the dative is கு alone after a base ending in இ, ஈ or ஐ, with neither the உ சாரியை nor the இன் route: குழந்தைக்கு, not குழந்தையுக்கு or குழந்தையிற்கு. The உருபு is கு (Tolkāppiyam, வேற்றுமையியல் 14), the உ is a சாரியை that need not appear (Tolkāppiyam உருபியல் 30; Naṉṉūl 244, 243), and where is Arden 110 | lexicon |
| none | R1 R2 R7 R11 R15 R101 | |

Six of the 28 rules only delete a pulli before a vowel sign, or a doubled stem-final consonant, and have no counterpart
over TLP1: a consonant byte followed by a vowel byte is already a syllable, so there is nothing to delete.

The Naṉṉūl 243 / 253 position, that a சாரியை may come, drop or vary and the grammar does not say which, is why the output
for a slot is a set of forms. The licensed alternants are carried and tagged (`tools/build_vikarpam_grid.py`).

## Parameters

```
orthographic   28 rewrite rules + 1,609 suffix allomorphs        = 1,637
phonemic       11 labelled rules + 27 morphemes + 20 classes x 4 =   118
```

About 80 of the 118 are class values read off the lexicon, not from a verse. The 1,609 spellings collapse because the lexicon
pre-spells the result of sandhi: six spellings of the plural (ங்கள், க்கள், ட்கள், ற்கள், ர்கள், கள்) are one morpheme, கள், once
the juncture is derived.

## Measured against the reference grid

| | |
|---|---:|
| cells in which a reference form is derived | **99.23%** of 1,554,418 |
| surface recall (every licensed variant generated) | 97.92% |
| precision, all licensed variants | 60.84% |
| precision, one form per cell (`TAMILOS_PHON_VARIANTS=min`) | 96.38% |
| independent UD Tamil nouns (644 of 740) | 87.03% |

- The cell figure is a **coverage ceiling, not a precision**: a cell counts as derived if any reference form appears in it.
- Precision against ThamizhiMorph is a lower bound: the reference lists only some of the alternants the nūṟpā license.
- The UD figure is a **development score**: its causes were fixed from the same misses, and the first run was 81.08%. The
  dative is the weakest case at 69.3%. The treebank is fetched by `tools/fetch_ud_ttb.sh` (non-commercial licence).
- With the licensed alternants tagged, the grid grows from 2,224,413 to 3,625,132 surfaces; 98.54% of the surfaces the
  reference omits are such alternants (again a cell-level ceiling).

Each figure is a row of [../paper/CLAIMS.tsv](../paper/CLAIMS.tsv) with the command that regenerates it.
