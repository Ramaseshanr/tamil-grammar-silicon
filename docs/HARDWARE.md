# The noun classifier in hardware

The decision of which declension class a noun takes is combinational logic, generated from the Python derivation and
checked against it on every stem.

```
tools/derive_nouns.py  ->  tools/gen_hdl.py  ->  hdl/gen/tamil_noun_class.v   (generated)
                                                  hdl/rtl/tamil_noun_front.sv   (hand-written: streaming window + core)
```

`hdl/build.sh` regenerates the logic, builds the testbenches, runs them, and synthesizes; any failing gate stops it.

## What the classifier reads

Class is a pure function of 29 bits: the last three phonemes (`p1`, `p2`, `p3`, eight bits each), the stem length
(`len`, 3 bits, saturating at 4) and a count of vowels (`uyir`, 2 bits, saturating at 3). Over the 43,647 stems that can be
classified there are 1,048 distinct windows and **no window with two classes**, so the streaming state is a three-deep
shift register and two saturating counters. A 41-phoneme stem needs no more state than a 4-phoneme one.

Each test in the classifier is a mask and a compare, because TLP1 was laid out for it: `is_mey(b)` is `(b & 0xC0) == 0x40`,
`is_uyir(b)` is `(b & 0xC0) == 0x00`, and `is_nedil(b)`, the நெடில்/குறில் contrast the டு/று-final stems turn on (Naṉṉūl
181–182), is the single bit test `b & 0x08`.

## Results (Lattice ECP5, Yosys `synth_ecp5`, nextpnr-ecp5)

| | LUT4 | flip-flops |
|---|---:|---:|
| `tamil_noun_class`, the decision | **132** | 0 |
| `tamil_noun_front`, the streaming datapath | **196** | 36 |

Placed and routed on an LFE5U-85F: maximum frequency **142.53 MHz** (the 100 MHz target passes), under 1% of the part. At
one phoneme per cycle a nine-phoneme stem classifies in about 65 ns, roughly 15 million stems per second per engine (an
estimate, not a measured throughput).

Verification, with zero mismatches in both gates: every one of the 1,048 windows, and all 43,647 stems streamed one
phoneme per cycle, against `derive_nouns.classify()`. The Python is the authority; the HDL is regenerated from it.

## The juncture unit: where a stem meets its ending

`hdl/rtl/tamil_join.sv` is the second block, and the first to hold sūtra rules as logic. It is `tools/phon_rules.py::join()`
written branch for branch in the same priority order, each branch annotated with its verse. It does not move strings; it says
what the seam does: whether the left form loses its last byte, whether one byte is inserted (and which), and whether the right
form loses its first byte.

| rule | what it does | source |
|---|---|---|
| P9 | two identical vowels become one (மர + அத்து → மரத்து) | Naṉṉūl 252 (அத்து is listed in 244) |
| P5 | a குற்றியலுகரம் drops before a vowel | Naṉṉūl 164 |
| P6 | a glide fills a vowel-vowel seam, ய் after i, e, ai, otherwise வ் | உடம்படுமெய் |
| P3 | a nasal is lost at a word boundary | |
| P1 | ம் takes the place of a following வல்லினம்: `(a & ~7) | (b & 7)` | Tolkāppiyam பிறப்பியல் 7–9 |
| P2 | ல் ள் ன் harden before a வல்லினம்: `(a & 7) | 0x40` | Naṉṉūl 227 |
| P11 | the final ஒற்று doubles before a vowel உருபு (monosyllables) | |
| P4 | a வல்லினம் doubles after a vowel | |
| P10 | a particle doubles its initial வல்லினம் | |

P8 (ன் → ர் before கள்) and P12 (the dative கு after இ, ஈ, ஐ) are stem-form and morpheme-selection rules, not seam rules; they
belong to the next blocks.

**Verification.** `hdl/tb/tb_join.v` applies the unit's outputs to a left and a right form and compares the whole resulting string
with `phon_rules.join()`, for every combination of the 35 valid phonemes at each side of the seam, the one fact about the byte before
the seam that the rules use, and all 256 flag settings (627,200 vectors), plus 300,000 seeded random vectors over all 256 byte values:
**927,200 of 927,200 agree**. Comparing whole strings, not output bits, matters: when the two bytes at the seam are equal, dropping the
left one and dropping the right one give the same string.

**Synthesis (Yosys, ECP5): 73 LUT4, no flip-flops**, with 16 PFUMX and 4 L6MUX21. It is combinational, so there is no clock figure yet.

## The noun generator: a stem in, every licensed form out

`hdl/rtl/tamil_noun_gen.sv` is the first block that generates Tamil. Given a stem as TLP1 bytes, its declension class and a case
bundle, it streams out every form the rules license, one byte per cycle. It is `tools/noun_gen_model.py` as a machine, and that file
is `phon_rules.derive()` restated in the shape the hardware needs. It uses the classifier's job (the class), the juncture unit
(every seam) and a small sequencer:

1. copy the stem into a working buffer;
2. **stem form:** drop the class's truncation and join its linking increment (அத்து, ற்று, டு, று: Naṉṉūl 244 and 164), or turn a
   final ன் into ர் before கள் (P8) — the 20 class rows;
3. **endings:** up to seven slots (plural, the சாரியை இன், case உருபு, benefactive, comparative, focus, sandhi). At each slot it
   counts the options the current state allows, since Naṉṉūl 243 lets a சாரியை come, drop out or vary, and walks them like an
   odometer, so every combination is emitted once;
4. **each ending is joined at the seam** by the juncture unit (227 hardening, 164 உ-drop, assimilation, glides, doubling). The
   dative after இ, ஈ or ஐ is கு with no உ (P12, Arden 110);
5. stream the form out, then step the odometer.

The two ROMs (the class table and the endings) are generated from `phon_rules.STEMFORM` and `phon_rules.MORPH`, never retyped.

**Verification.** `hdl/tb/tb_noun_gen.v` loads each stem, runs the generator, collects every form it streams, and requires the
*set* of forms to equal `phon_rules.derive()` for that cell. The software model `tools/noun_gen_model.py` is identical to the
derivation on all 1,552,669 encodable cells. In hardware the sample gate (every class-and-bundle pair plus random cells, 3,992 cells, 9,342 forms) runs inside `build.sh`, and the
exhaustive gate, `hdl/gen_exhaustive.sh`, drives **all 1,552,669 cells of the reference through the RTL: 3,627,061 forms, the set of forms
equal to `phon_rules.derive()` in every cell, no mismatch** (about ten minutes on ten cores, in simulation).

**Synthesis (Yosys, ECP5): 869 LUT4, 200 flip-flops, and 44 distributed-RAM blocks** for the two 64-byte buffers. After place and route
the whole generator is 1,283 logic cells, about 1.5% of an LFE5U-85F, at a maximum clock, after routing, of **54.7 MHz** (it fails a 100 MHz target:
the stem-form and seam arithmetic is one long combinational path, and it has not been pipelined).

**What it is not.** Its inputs are decoded fields (the case, plural, benefactive, comparative, focus and sandhi bits), not the TF1 register
yet. The class is the generator's own index into the 20 classes; the classifier assigns only 17 of them. It reads TLP1 bytes, so it still
needs the text codec in front. It takes a stem of up to 48 sounds. A form takes on the order of a hundred cycles.

## Layout

```
hdl/
  src/main.rs, src/classify_gen.rs   the LogicBlock and the generated if/else of the 49 contexts
  gen/tamil_noun_class.v             generated combinational core
  gen/tamil_classes.vh               generated class-code legend
  rtl/tamil_noun_front.sv            hand-written streaming window and core instance
  rtl/tamil_join.sv                  hand-written juncture rules, each branch with its verse
  rtl/tamil_noun_gen.sv              hand-written sequencer: stem form, endings, seams, every licensed form
  tb/                                gate 1: every distinct window; gate 2: every stem, a phoneme per cycle; gate 3: the juncture unit; gate 4: the noun generator
  vectors/                           generated from derive_nouns.classify(), phon_rules.join() and phon_rules.derive()
  syn/                               synthesis scripts
  build.sh                           regenerate, build, verify, synthesize
```

## What is not built

This is the classifier only. The rest of the noun datapath is specified, not built:

| block | status |
|---|---|
| declension classifier | built, verified, synthesized |
| TLP1 codec (UTF-8 to phoneme) | not started |
| stem-form unit (drop at most 1, insert at most 4 phonemes) | built inside the generator |
| suffix ROM | built inside the generator (generated from `phon_rules.MORPH`) |
| juncture rules (the seam) | built, verified, synthesized: 73 LUT4 |
| concatenate and emit (the sequencer) | built: `tamil_noun_gen` |
| a generator driven by the TF1 register, with the classifier in front | not started |

So the generator produces the noun forms from a stem, a class and a case bundle, and matches the Python derivation. What is missing is the plumbing around it: the TF1 register as its input, the classifier feeding its class, and the text codec. There is no verb hardware.
