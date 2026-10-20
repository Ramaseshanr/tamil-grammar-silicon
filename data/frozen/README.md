# data/frozen

Small inputs the rebuild needs and cannot regenerate from code, plus the checksums it is
checked against. `tools/rebuild_derived.sh` copies the first two into `data/derived/`.

| File | What it is |
|---|---|
| `noun_rules.json` | The marker strings `tools/patch_gold.py` reads. Provenance and the draft-1 → draft-2 byte translation are in its `_provenance` field. |
| `new_roots.tsv` | The 159 verb roots added to the lexicon, each with a conjugation class assigned from corpus evidence (`tools/add_roots.py`). Nine are weak-confidence and would repay a Tamil speaker's review. The tool that made it reads a grid that already existed, so it cannot be re-run from scratch; this file is its output. |
| `MANIFEST.sha256` | SHA-256 of the 15 derived outputs and of the frequency table, in `shasum -a 256 -c` format. |

Do not edit these to make a build pass. A changed checksum means a changed result.
