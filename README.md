# tamil-grammar-silicon

Tamil grammar, taken from Naṉṉūl and Tolkāppiyam as axioms and computed into logic.

The question is whether a noun's whole declension can be derived from the grammar's own
rules, with the result small enough to fit in a few hundred gates, instead of being stored as
a table. The sūtra is the specification: each rule cites its nūṟpā where one exists, and the parameters
that are fitted instead are labelled and counted ([docs/METHOD.md](docs/METHOD.md)).

**Status: work in progress, nouns only.** Nothing here is a finished system.

## What exists

| | |
|---|---|
| **TLP1**, a one-byte-per-phoneme encoding built on Tolkāppiyam பிறப்பியல் 7–9 | [spec/TLP1.md](spec/TLP1.md) |
| **Noun rules**: 114 phonemic parameters replace 1,637 spelling-level ones (28 rules and 1,609 endings) | `tools/phon_rules.py`, [docs/RULES.md](docs/RULES.md) |
| **Declension class decision in RTL**: 132 LUT4 and no flip-flops; the streaming datapath is 196 LUT4 and 36 flip-flops (ECP5 synthesis, 142.5 MHz); it agrees with the Python on all 43,647 classified stems | `hdl/`, [docs/HARDWARE.md](docs/HARDWARE.md) |
| **Juncture rules in RTL**: what happens where a stem meets its ending (assimilation, hardening, hiatus, glides), 73 LUT4; matches the Python on 927,200 vectors | `hdl/rtl/tamil_join.sv`, [docs/HARDWARE.md](docs/HARDWARE.md) |
| **Noun generator in RTL**: a stem, a class and a case bundle in, every licensed form out (860 LUT4 on ECP5); in simulation it produces the same set of forms as the Python derivation in **all 1,552,669 reference cells** | `hdl/rtl/tamil_noun_gen.sv`, [docs/HARDWARE.md](docs/HARDWARE.md) |
| **TF1**, a 128-bit feature register for nouns and verbs | [spec/TF1.md](spec/TF1.md) |

## How well it works

- A correct surface form is derived in **99.23%** of 1,554,418 ThamizhiMorph noun cells. That
  is a coverage ceiling, not precision: the derivation also produces forms the reference
  does not list.
- **87.03%** (644 of 740) on independent UD Tamil items. This is a development score: the
  causes were fixed from the same misses, and the first run was 81.08%. Datives are the weak
  spot, at 69.3%.

Every figure above is a row in [paper/CLAIMS.tsv](paper/CLAIMS.tsv) with the command that
regenerates it. `python3 tools/check_claims.py` reports which claims the repository has moved
out from under.

## What does not exist yet

- The plumbing around the noun generator: it takes decoded fields, not the TF1 register; the classifier does
  not yet feed it its class; and nothing converts Tamil text to the bytes it reads. It is verified in simulation
  and meets 54.9 MHz on an ECP5 (it has not been pipelined), not tested on a board.
- Any verb hardware. The verb side stops at the TF1 register and its codec.
- Outside review.

## Authority

Naṉṉūl (the Saiva Siddhanta Kazhagam edition) and Tolkāppiyam decide. ThamizhiMorph is data
to compare against, and corpus counts may confirm a form but never decide one. No learned
model is in the derivation, the kernel or the silicon path. See
[docs/METHOD.md](docs/METHOD.md).

## Layout

`spec/` encodings · `tools/` derivation, validators and the claims gate · `hdl/` RTL and
generated Verilog · `docs/` method, rules, hardware and rebuild · `paper/CLAIMS.tsv` the claims
ledger · `data/gold/` reference data, each source under its own licence. Comments in the code sometimes
cite working notes that are not part of this repository.

## Reproducing

- The UD Tamil-TTB treebank is not redistributed (non-commercial licence). Run
  `tools/fetch_ud_ttb.sh` before the UD evaluations.
- ThamizhiMorph is fetched at a pinned commit, not vendored: run `tools/fetch_thamizhi_morph.sh`.
- `tools/rebuild_derived.sh` rebuilds `data/derived/` from a fresh clone in about six minutes and checks
  every output against `data/frozen/MANIFEST.sha256`. It needs `foma` and network access: the exact frequency
  table is fetched by `tools/fetch_freq.sh` (it cannot be rebuilt from Wikipedia exactly). See
  [docs/REBUILD.md](docs/REBUILD.md).

## How this was made

The research question, the choice of sources, and every judgement about what the grammar says are the author's.
The code, specifications and documents were developed in working sessions with Claude Code (Anthropic's coding
agent), which wrote and ran much of the code and drafted much of the prose. Because of that, nothing here rests on
the assistant's word: every figure is a row of [paper/CLAIMS.tsv](paper/CLAIMS.tsv) with the command that
regenerates it, and the rebuild checks its outputs byte for byte. The verse quotations have been checked by the
author against the printed text; the readings of the grammar have not yet had outside review.

## Licences

Apache-2.0 for code and HDL, CC BY 4.0 for specs and docs, and each data source
under its own terms. See [LICENSES.md](LICENSES.md) and [NOTICE](NOTICE).

Author: Ramaseshan Ramachandran
