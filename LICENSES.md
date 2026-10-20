# Licences

The text of every licence used here is in `LICENSES/`. `NOTICE` lists third-party work this
repository includes or derives from. The table says which terms apply to which path.

| Path | Terms | Notes |
|---|---|---|
| `tools/`, `hdl/` (source, generated Verilog, test vectors), `LICENSE`, build scripts | Apache-2.0 | `hdl/vectors/stem_vectors.hex` derives from ThamizhiMorph stems (also Apache-2.0). |
| `spec/`, `docs/`, `paper/CLAIMS.tsv` | CC BY 4.0 | Prose, tables and the claims ledger. |
| `data/gold/UD_Tamil-MWTT/` | CC BY-SA 4.0 | Its own `LICENSE.txt` applies. Share-alike covers adaptations of that corpus, not the rest of the repository. |
| `data/gold/nannul/` | CC BY-SA 4.0, plus Project Madurai's terms | `verse` field from ta.wikisource.org (CC BY-SA 4.0). `verse_split` field from Project Madurai pmuni0147, which may be distributed only with its header kept intact: `PROJECT_MADURAI_HEADER.txt`. The verses themselves are 13th-century and public domain. |
| `data/gold/tolkappiyam/` | Project Madurai terms | Header kept verbatim in `pirappiyal.json`. |
| `data/gold/arden/`, `data/gold/arden1910/` | Public-domain source; index CC BY 4.0 | Arden died in 1897. |
| `data/gold/freq/` | Counts only (CC BY-SA 4.0 source) | `tawiki_freq.tsv` is not tracked; `tools/build_freq.py` rebuilds it. |

## Not in this repository

| Material | Terms | Why absent |
|---|---|---|
| ThamizhiMorph | Apache-2.0 | Fetched, not vendored. `tools/fetch_thamizhi_morph.sh` pins commit `adbacceda5e8aa902e4b6ed58a3edf5f78cd46fb`. Its own `LICENSE` arrives with it. |
| UD_Tamil-TTB | CC BY-NC-SA 3.0 (non-commercial) | A non-commercial licence conflicts with an Apache-2.0 repository. `tools/fetch_ud_ttb.sh` fetches the commit the evaluations used. No shipped table or HDL file is derived from it; it is used only to evaluate and validate. |
| University of Madras Tamil Lexicon (DSAL) | CC BY-NC-ND | No derivatives allowed. Not built on. |
| Naṉṉūl PDFs (MS University, Tamil Virtual University) | Copyright | Consulted only. Only nūṟpā numbers, our reading and measurements are published. |

## Open questions

- Copyright holder in `NOTICE` and the licence choice for `spec/`, `docs/` and `paper/` (CC BY 4.0
  versus CC BY-SA 4.0) are the author's call.
