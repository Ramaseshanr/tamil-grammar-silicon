# Arden 1910 — the independent authority

A. H. Arden, *A Progressive Grammar of Common Tamil*, 4th ed., 1910.
Public domain. Source: `archive.org/details/progressivegramm00ardeiala`, OCR text staged
here as `arden_1910_djvu.txt`.

**The source this project has needed three times over** — for ṭu-final classification
(`DERIVABILITY.md` §D/§E), derivation precision (`DERIVATION.md`), and verifier soundness
(`VERIFIER.md`). It is an authority ThamizhiMorph does not derive from and did not consult:
ThamizhiMorph cites Graul's verb classification and the authors' own Meta-Morph paper, and
nothing else.

---

## ⚠️ What is usable and what is not

**The 1910 OCR contains zero Tamil-script characters.** Every Tamil word is mangled into
Latin lookalikes — `LDTLD` for மரம், `/5//?` for நரி, `e_&(3j` for உக்கு. The Tamil
**forms** are unrecoverable without deciphering the OCR's glyph substitutions.

**The English rule statements survived intact, and they are the valuable part.** Arden
states each rule with explicit phonological conditions. Those conditions are what
adjudicate ThamizhiMorph; the Tamil forms can be supplied from the rule.

Wikisource has this text but has transcribed only the preface and contents, not the
chapters — it is not a better source today.

---

## Case formation (§§105–114)

| § | Rule |
|---|---|
| 103 | Arden uses **seven cases**: nom, voc, gen, dat, acc, loc, ins. |
| 104 | "In Native Grammars the cases are eight in number, and are arranged in a different manner." Arden knowingly departs from the classical 8 vēṟṟumai. |
| 105 | Nominative singular = the noun itself. |
| 108 | All other cases add casal affixes to the **inflectional base**, "that particular form of the noun that takes the casal affixes". Often identical to the nominative; sometimes not. |
| 109 | Genitive: the bare inflectional base, **or** base + இன். Either may add உடைய. |
| **110** | **Dative: கு after a base ending in இ, ஈ or ஐ; உக்கு after any other letter.** |
| **111** | **Accusative ஐ, locative இல், instrumental ஆல், added to the inflectional base.** |
| 112 | Plural nominative "most commonly formed merely by adding கள்". |
| 113 | Plural inflectional base = plural nominative. |
| **145** | **"The particle இன் may be inserted before the casal affix of any case of any noun, except the nominative and vocative."** — inserted **may**, i.e. optional. |

## The four declensions

| § | Declension | Membership | Inflectional base | Plural |
|---|---|---|---|---|
| 116–118 | **First** | masculine nouns in **ன்** | = nominative | ன் → ர் (மனிதன் → மனிதர்); "in the common dialect கள் is often added" → மனிதர்கள் |
| 124–126 | **Second** | nouns in **ம்** (all neuter) | ம் → **த்து** (மரம் → மரத்து) | + கள் → மரங்கள் |
| **129–131** | **Third** | nouns in **டு** or **று**, *except* words of two short open syllables | **doubles the final consonant** — வீடு → வீட்டு, ஆறு → ஆற்று | + கள் |
| **134** | | **நடு and மறு (two short open syllables) belong to the FOURTH declension**, and so do stems whose டு/று is already doubled (பட்டு, காற்று) | | |
| 135–137 | **Fourth** | everything else | **= nominative** | usually + கள் |
| 138 | | nouns in a long vowel take **க்கள்** (பூ → பூக்கள்) | | |
| 139 | | nouns in உ of two short open syllables take **க்கள்** (குரு → குருக்கள், மறு → மறுக்கள்) | | |
| **141** | | "Some plurals vary in accordance with the grammatical laws of euphony. Thus **கல்** makes **கற்கள்** and **நாள்** makes **நாட்கள்**." | | |

## Agreements with ThamizhiMorph

Arden independently confirms increments this project fitted from data in `DERIVATION.md`:

- ம் → த்த்/த்து (Arden §125 = TamilOS C15 obl) — மரம் → மரத்தை
- ன் → ர்(கள்) (Arden §118 = C11 pl) — மாணவன் → மாணவர்கள்
- ல் → ற்கள், ள் → ட்கள் (Arden §141 = C12/C13/C14 pl) — கல் → கற்கள், நாள் → நாட்கள்
- டு/று double in the oblique (Arden §130 = C6/C8 obl) — காடு → காட்டு

Two grammars a century apart, one hand-written and one fitted from a transducer, agreeing
on the increments. That is a real cross-validation of both.

## Disagreements — Arden against ThamizhiMorph

- **§110** dative கு after இ/ஈ/ஐ. ThamizhiMorph generates ஆசைமொழி**யு**க்கு. Arden gives
  ஆசைமொழி**க்கு**.
- **§134** நடு is fourth-declension, so its base does **not** double. ThamizhiMorph
  generates நட்டை. Arden gives நடுவை.
- **§145** இன் insertion is **optional**. ThamizhiMorph licenses only the இன்-inserted
  plural accusative (விற்கள்**இனை**), never the plain விற்கள்**ஐ**.
