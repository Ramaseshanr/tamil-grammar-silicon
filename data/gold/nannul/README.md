# Naṉṉūl — canonical nūṟpā index

`nurpa.json` — **all 462 nūṟpā**, the complete Naṉṉūl, from **two independent
transcriptions**:

| field | source | orthography | count |
|---|---|---|---:|
| `verse` | ta.wikisource.org | **sandhi-joined** (புணர்ச்சி), as printed | 390 |
| `verse_split` | projectmadurai.org `pmuni0147` | **split** (பிரித்து) | 460 |

Project Madurai's etext is by **Dr. Thomas Malten** (Inst. of Indology and Tamil Studies,
Univ. of Köln), conformed to the **Mani Thirunavukkarasu Mudaliar** edition (Vavilla
Ramasamy Sastrulu & Sons, Madras, **1926**) and proof-read. It supplies the **பாயிரம்
(1–55)** that Wikisource lacks, and its table of contents independently confirms every iyal
range the Wikisource extraction produced:

```
  பாயிரம் 1-55 · எழுத்ததிகாரம் 56-257 (56-127 · 128-150 · 151-203 · 204-239 · 240-257)
                · சொல்லதிகாரம் 258-462 (258-319 · 320-351 · 352-419 · 420-441 · 442-462)
```

## Why two transcriptions are worth more than one

They differ on **382 of 388** shared nūṟpā — which is not disagreement about the text but
about word-splitting:

```
  142  joined : தடறவொற் றின்னே யைம்பான் மூவிடத் / திறந்த காலந் தருந்தொழி லிடைநிலை
       split  : த ட ற ஒற்று இன்னே ஐம்பால் மூ இடத்து / இறந்தகாலம் தரும் தொழில் இடைநிலை
```

The joined form is what the edition prints; the **split form is machine-readable**, because
it names the morphemes — `த ட ற ஒற்று` *is* the list of past-tense markers. Citing wants
the first; extracting grammatical content wants the second.

It has already corrected a reading. Nūṟpā **327**: the split text gives
`அர் ஆர் ப ஊர் அகரம் மார் ஈற்ற` — **six** plural-epicene விகுதி. The Bamini pipeline had
yielded "அர், ஆர், ப, மரர்": மரர் was residue for **மார்**, and **ஊர்** and **அகரம்** were
missed entirely.

## Why it matters

Until now no source could do all three things at once:

| source | Unicode | canonical numbers | quotable wording | vendorable |
|---|---|---|---|---|
| UHH-Tamilex | yes | **no** — per atikāram | — | **no** (no LICENSE) |
| MS Univ DJL11/12 | no — Bamini | yes | no — decode residue | **no** (copyright) |
| Vellaivaranar scan | yes (OCR) | **no** — 326 reads as 824 | no — OCR errors | unconfirmed |
| **this** | **yes** | **yes** | **yes** | **yes** |

The per-atikāram numbering of the Tamilex edition forced a relabel of all 1,146 noun
citations once. This index ends that problem.

## Provenance and licence

Text from **ta.wikisource.org**, pages `நன்னூல் எழுத்ததிகாரம் 1–5` and
`நன்னூல் சொல்லதிகாரம் 1–5`.

- **Naṉṉūl** by **பவணந்தி முனிவர் (Pavaṇanti Munivar)**, 13th century — **public domain**.
- The Wikisource transcription and arrangement is **CC BY-SA 4.0**; this directory
  redistributes it with attribution under the same terms.

Citations elsewhere in this project name the **Saiva Siddhanta Kazhagam** edition as the
authority (`docs/METHOD.md`); this index supplies the same canonical numbering and is
used to check wording.

The `verse_split` field comes from Project Madurai, whose terms require its header to stay with the
text: see `PROJECT_MADURAI_HEADER.txt`.

## ⚠️ Known gaps

390 of the 407 nūṟpā present on those pages were extracted. **17 are missing** — 134, 171,
172, 174, 175, 206, 258, 282, 338, 363–366, 368, 369 and a few more — because their
wikitext formatting differs from the `'''நூற்பா: N'''` + `:verse` pattern the extractor
matches. The numbering has **no gaps** in 56–462; only the verse text is absent for those
17. Nūṟpā 1–55 (the பாயிரம்) are on a page not yet fetched.

None of the 17 is currently cited by this project.
