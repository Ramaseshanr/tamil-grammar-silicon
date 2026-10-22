# Rebuilding data/derived

`data/derived/` is 4.6 GB and is not in the repository. This is how to make it again, and what
can and cannot be rebuilt exactly.

```
tools/rebuild_derived.sh
```

About six minutes. It builds from `data/gold/` and `data/frozen/`, then compares **fifteen derived
files and the frequency table to `data/frozen/MANIFEST.sha256`, byte for byte**. It stops on the first
mismatch. `tools/rebuild_derived.sh --verify` checks an existing `data/derived/` without building.

## What you need

- `python3` (3.13 was used), `git`, `unzip`, `shasum`
- `foma` and `flookup` (the FST toolchain; Homebrew: `brew install foma`)
- `tools/fetch_thamizhi_morph.sh` runs by itself (it pins upstream commit `adbacce…`)
- `tools/fetch_ud_ttb.sh` only if you want the UD evaluations, not for the rebuild
- network access: `tools/fetch_freq.sh` downloads the frequency table (see below)

Yosys, nextpnr and iverilog are needed only for the hardware (`hdl/build.sh`), not for `data/derived`.

## The order

| # | Stage | Command | Produces | Time |
|---|---|---|---|---|
| 1 | Base noun grid | `tools/generate_noun_grid.py` | `nouns_grid`, `nouns_empty`, `nouns_oneway` | 35 s |
| 1b | Stem list | `tools/list_noun_stems.py` | `noun_stems_classed` | 0 s |
| 2 | Frozen inputs | copy from `data/frozen/` | `noun_rules.json`, `new_roots.tsv` | 0 s |
| 3 | Patch chain | `patch_gold` → `relabel_nannul` → `build_tagged_gold` → `retag_by_corpus` → `fix_nstems` | `nouns_grid_arden` → `_nannul` → `_tagged` → `_tagged2` → `nouns_grid_final` | 35 s |
| 4 | Verbs | `tools/build_verbs.sh` | `verbs_grid_final` | 100 s |
| 5 | விகற்பம் grids | `build_vikarpam_grid`, `build_vikarpam_verbs` | `nouns_grid_vikarpam`, `verbs_grid_vikarpam` | 110 s |
| 6 | Rules and citations | `derive_nouns learn` (with `TAMILOS_PAIRED=1`), `cite_rules`, `cite_verbs` | `noun_rules_paired`, `noun_rules_cited`, `verb_rules_cited` | 45 s |
| 7 | HDL | `tools/gen_hdl.py` | regenerates `hdl/gen`, `hdl/src`, `hdl/vectors`; must leave `git diff hdl/` empty | 5 s |

Stage order matters. In the verb stage, roots and cells go into the `.lexc` files before the models
are compiled; `build_verbs.sh` enforces that (`tools/buildcheck.py` makes a build that cannot produce a class fail loudly). Each noun stage
reads the previous one, and stage 3 reads the frozen `noun_rules.json`.

## What was checked, and how

On 2026-10-19 the driver's stages were run in an empty copy of the repository and every output was compared
with the files this project's claims were measured on. Every output matched exactly except one: the last
(`mech`) column of `nouns_grid_vikarpam.tsv`, which differed between runs on about 440,000 rows. That was a bug,
not a drift: `derive_labeled` kept whichever optional-mechanism combination a hash-randomised set visited first
when one surface could be reached several ways. It now keeps the derivation with the fewest optional mechanisms, so
the file is the same under any `PYTHONHASHSEED` (checked with two seeds). The surfaces, licence tags, registers and
counts were never affected (2,224,413 → 3,650,836 surfaces, as the ledger says).

## What cannot be rebuilt exactly

**The frequency table.** `tawiki_freq.tsv` (807,232 forms, Tamil Wikipedia, retrieved 2026-09-29) comes from
`tools/build_freq.py`, which reads `tawiki-latest-pages-articles.xml.bz2`. "Latest" moves, and Wikimedia keeps only
recent dumps, so a fresh build gives different counts, and the register tags and added verb forms that depend on
a count threshold (20) can change. So the exact table is a release asset (4 MB gzipped, counts only, CC BY-SA 4.0):
`tools/fetch_freq.sh` downloads it from the `freq-2026-09-29` release and refuses it unless its checksum matches
the manifest, and `tools/rebuild_derived.sh` calls it when the table is missing. Building your own with `build_freq.py`
is fine for exploration, but expect different grids, and the driver will stop.

**`data/frozen/noun_rules.json`.** The original was learned on 2026-09-29 under TLP1 draft 1. Eight committed versions
of `tools/derive_nouns.py` were tried on the base grid, and none reproduces that file, so the learner cannot regenerate
it. The frozen copy is the original with its byte values translated to draft 2, and with that translation the patch
chain reproduces exactly. Only `patch_gold.py` reads it.

**`data/frozen/new_roots.tsv`.** An input, not an output; see `data/frozen/README.md`.

## Not rebuilt

- Older intermediates that may sit in a working `data/derived/` (earlier verb-grid versions, `verbs_gold*`, pickles and
  similar) are not produced by the driver; the one-order `tools/build_verbs.sh` superseded them.
- The driver does not fetch UD Tamil-TTB (`tools/fetch_ud_ttb.sh`, only needed for the UD evaluations).
