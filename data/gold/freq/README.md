# Modern Tamil frequency table

`tawiki_freq.tsv` — word form ⇥ count, 807,232 forms with count ≥ 2.

| | |
|---|---|
| Source | Tamil Wikipedia, `tawiki-latest-pages-articles.xml.bz2` |
| Retrieved | 2026-09-29, `dumps.wikimedia.org/tawiki/latest/` |
| Licence | **CC BY-SA 4.0** — Wikimedia contributors |
| Dump size | 264 MB compressed |
| Extracted | 313,419 pages · **39,061,503 Tamil tokens** · 2,008,117 unique forms |
| Built by | `tools/build_freq.py` (streams the bz2; the text is never stored) |

Only counts are kept — no Wikipedia text is redistributed in this repository.

## What it is for, and what it is not for

It exists to answer one question: **is this form actually used in modern written Tamil?**

It answers that question **only in the positive direction.** A form with 631 occurrences is
in modern use. A form with 0 occurrences is *not thereby ungrammatical* — it may simply be
a rare word, a rare inflection, or outside an encyclopaedia's register (docs/METHOD.md).

## Known bias

Wikipedia is crowd-written and not normative, and its most frequent tokens include
structural artefacts — பகுப்பு (Category) at 567,426 and மேற்கோள்கள் (References) at
128,170 are wiki furniture, not Tamil prose. Treat counts as evidence of *use*, never of
*correctness*.

## Getting the exact table

`tawiki_freq.tsv` is not committed. `tools/fetch_freq.sh` downloads the table this repository was measured with
from the `freq-2026-09-29` release (gzipped) and checks it against `data/frozen/MANIFEST.sha256`. Rebuilding with
`tools/build_freq.py` reads the current dump and will give different counts.
