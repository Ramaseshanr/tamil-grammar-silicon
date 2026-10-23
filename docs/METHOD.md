# Method: what decides, and what may not

These are standing rules for the derivation, not observations. They say which source wins when
two disagree, and what is not allowed to enter the derivation at all.

## The order of precedence

| rank | source | standing |
|---|---|---|
| 1 | **Naṉṉūl** (Saiva Siddhanta Kazhagam edition; Tolkāppiyam where it speaks) | decides |
| 2 | **Arden, *A Progressive Grammar of Common Tamil* (1910)** | admissible where Naṉṉūl is silent; cited as Arden, never as a nūṟpā |
| 3 | **ThamizhiMorph** | data to compare against, never an authority |
| 4 | **Corpus frequency** (Tamil Wikipedia counts) | may confirm or promote a form; may never demote or decide one |
| 5 | **Fitted parameters** | must be labelled `[fitted]` and counted |

Where Naṉṉūl is silent, the silence is recorded, so that no lower source becomes the authority by default.
Of Tolkāppiyam seven chapters are in the repository (Project Madurai, each checked against Wikisource): from the எழுத்ததிகாரம்
பிறப்பியல் (21 nūṟpā), புணரியல் (40), உருபியல் (30), உயிர்மயங்கியல் (93), புள்ளிமயங்கியல் (110) and குற்றியலுகரப் புணரியல்
(77), and from the சொல்லதிகாரம் வேற்றுமையியல் (22). Nūṟpā numbers restart in each iyal, so a citation names the iyal (editions that
number the Eḻuttatikāram straight through, such as tamilvu's, give புணரியல் 23 as 125, உருபியல் 13 as 185 and புள்ளிமயங்கியல் 15
as 310); elsewhere Tolkāppiyam is cited by name only.

## Corpus counts

A raw surface count is evidence about a string, not about a form. The same string can be a verb ending, a noun
plural, a place name or an unrelated word. So:

- a count may promote a form only where the surface is unambiguous (`tools/build_vikarpam_grid.py` refuses to
  promote any surface that is itself a declared stem, and reports each one it blocks);
- where a nūṟpā states a condition a corpus cannot see, the nūṟpā decides and the count is inadmissible. The example
  is Collatikāram 327, **மார் வினையொடு முடிமே** ("மார் concludes with a verb"), a syntactic condition, so
  `tools/build_vikarpam_verbs.py` never promotes a மார் form on frequency;
- absence from a corpus is not evidence of ungrammaticality. `tools/retag_by_corpus.py` promotes only (a surface must
  occur at least 20 times) and cannot demote.

## No learned model in the derivation

**No learned model may enter the derivation, the kernel or the silicon path.** The noun declension is a decidable
function of its inputs; a learner there can only approximate it. Parameters that are fitted are fitted to the lexicon,
labelled, and counted: of the noun rules' 1,219 parameters, 1,146 carry a nūṟpā citation (94.0%; `tools/cite_rules.py`)
and 73 are labelled fitted.

## Where a nūṟpā is silent, or licenses more than one answer

- **Naṉṉūl 243** says a சாரியை may appear, be omitted, or be optional (விகற்பம்); **253** declines to say which goes
  where. So the right output for a slot is a **set** of forms, and each licensed form is carried and tagged, not selected.
  (`tools/build_vikarpam_grid.py`.)
- **Naṉṉūl 227** licenses both alternants (உறழ்வு) in non-case joins. Both are kept.
- Naṉṉūl is a 13th-century grammar of classical Tamil. It cannot say which of two licensed alternants is the modern
  standard, and it does not cover most of the modern verb system's analytic formations, loan phonology or the Grantha
  letters. Where it cannot speak the parameter is labelled `[fitted]` or `[Arden]` and counted.
- The dative: Tolkāppiyam names the case உருபு **கு** itself (வேற்றுமையியல் 14, கு எனப் பெயரிய வேற்றுமைக் கிளவி), so the உ of
  உக்கு is a சாரியை. Tolkāppiyam's உருபியல் lists the words that take a சாரியை and says that for every other word it is not obligatory
  (30, as I read it); Naṉṉūl lists உ among the சாரியை (244) and lets any சாரியை be left out (243), but neither says where the உ is
  absent in the dative. The
  condition, that the உ is absent after a base ending in இ, ஈ or ஐ, is Arden 110 (rank 2), and that part is labelled as such.
  ThamizhiMorph's குழந்தையுக்கு and குழந்தையிற்கு are not generated: after இ, ஈ or ஐ the dative is கு only (குழந்தைக்கு, தந்தைக்கு),
  while the இற்கு route stays for other stems (மரத்திற்கு, பசுவிற்கு).
- Where ThamizhiMorph contradicts a nūṟpā, the project follows the nūṟpā: the டு/று-final stems are relabelled by
  Naṉṉūl 181–182 (`tools/relabel_nannul.py`).

## The edition

All nūṟpā numbers are those of the Saiva Siddhanta Kazhagam edition. `data/gold/nannul/nurpa.json` supplies the same
numbering from two transcriptions (Wikisource, and Project Madurai's word-split text); the PDFs of the MS University and
Tamil Virtual University editions were consulted but are not redistributed. Licences: [../LICENSES.md](../LICENSES.md).
