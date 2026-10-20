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

## Layout

```
hdl/
  src/main.rs, src/classify_gen.rs   the LogicBlock and the generated if/else of the 49 contexts
  gen/tamil_noun_class.v             generated combinational core
  gen/tamil_classes.vh               generated class-code legend
  rtl/tamil_noun_front.sv            hand-written streaming window and core instance
  tb/                                gate 1: every distinct window; gate 2: every stem, a phoneme per cycle
  vectors/                           generated from derive_nouns.classify()
  syn/                               synthesis scripts
  build.sh                           regenerate, build, verify, synthesize
```

## What is not built

This is the classifier only. The rest of the noun datapath is specified, not built:

| block | status |
|---|---|
| declension classifier | built, verified, synthesized |
| TLP1 codec (UTF-8 to phoneme) | not started |
| stem-form unit (drop at most 1, insert at most 4 phonemes) | not started |
| suffix ROM | sized, not built |
| concatenate and emit | not started |

So the chip decides a stem's class; it does not yet generate மரத்தில். There is no verb hardware.
