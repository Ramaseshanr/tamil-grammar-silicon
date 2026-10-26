#!/usr/bin/env python3
"""
The order of the parts of a noun form, as a small grammar, checked against the feature bundles the reference
grid uses.

The grammar names the slots (number, case, an extension that only some cases take, a particle) and their order.
It is written once, as data; the EBNF printed here is rendered from that data and the check enumerates the same
data, so the text and the check cannot drift apart. It is deliberately a grammar of order, not of which
combinations a noun takes: that is a property of the noun's class.

    python3 tools/check_noun_grammar.py            # the check, in the form the claims ledger records
    python3 tools/check_noun_grammar.py --ebnf     # only the EBNF text

Exits non-zero if a bundle of data/derived/nouns_grid_final.tsv (the reference grid) is not a sentence of the grammar.
"""
import sys, pathlib, itertools

ROOT = pathlib.Path(__file__).resolve().parent.parent

# expression forms: ("tok", t) a feature tag, ("ref", name) another rule, ("seq", [..]), ("alt", [..]), ("opt", e)
T = lambda t: ("tok", t)
R = lambda n: ("ref", n)
SEQ = lambda *e: ("seq", list(e))
ALT = lambda *e: ("alt", list(e))
OPT = lambda e: ("opt", e)

RULES = [
    ("noun_form", SEQ(T("noun"), OPT(R("stem_kind")), OPT(R("case_part")), OPT(R("vparticle")), OPT(R("particle")))),
    ("stem_kind", ALT(T("infInc"), T("pl"))),
    ("case_part", ALT(
        SEQ(T("nom"), OPT(T("cmpr"))),
        SEQ(T("acc"), OPT(ALT(T("vpart"), T("vpartp")))),
        SEQ(T("dat"), OPT(ALT(T("ben"), T("n"), T("pl")))),
        T("inst"), T("loc"), T("abl"), T("gen"), T("soc"), T("so"))),
    ("vparticle", ALT(T("um"), T("ee"), T("oo"), T("aa"))),
    ("particle", ALT(T("foc"), T("psp"), R("sandhi"))),
    ("sandhi", ALT(T("sandhik"), T("sandhic"), T("sandhip"), T("sandhit"))),
]
NOTES = {
    "noun_form": "the order of the slots",
    "stem_kind": "infInc: the oblique stem with the இன் சாரியை; pl: the plural கள்",
    "case_part": "a case; only some cases take an extension",
    "vparticle": "உம் ஏ ஓ ஆ: the vowel-initial particles, after the case [Tolkāppiyam இடையியல் 7-9; Naṉṉūl 422, 423, 425]",
    "particle": "foc தான், psp a postposition, or a joining consonant at a word boundary",
    "sandhi": "க் ச் ப் த்",
}
RULE = dict(RULES)


def render(e, top=False):
    k = e[0]
    if k == "tok": return f'"{e[1]}"'
    if k == "ref": return e[1]
    if k == "opt": return "[ " + render(e[1], True) + " ]"
    if k == "seq": return ", ".join(render(x) for x in e[1])
    if k == "alt":
        s = " | ".join(render(x) for x in e[1])
        return s if top else "( " + s + " )"


def ebnf():
    w = max(len(n) for n, _ in RULES)
    out = []
    for n, e in RULES:
        body = render(e, True)
        if e[0] == "alt" and e[1] and any(x[0] == "seq" for x in e[1]):
            body = "\n" + " " * (w + 3) + ("\n" + " " * (w + 1) + "| ").join(render(x, True) for x in e[1])
            body = body.lstrip("\n")
            body = ("\n" + " " * (w + 1) + "| ").join(render(x, True) for x in e[1])
        out.append(f"{n.ljust(w)} = {body} ;   (* {NOTES[n]} *)")
    return "\n".join(out)


def sentences(e):
    k = e[0]
    if k == "tok": return [(e[1],)]
    if k == "ref": return sentences(RULE[e[1]])
    if k == "opt": return [()] + sentences(e[1])
    if k == "alt": return [s for x in e[1] for s in sentences(x)]
    if k == "seq":
        parts = [sentences(x) for x in e[1]]
        return [tuple(itertools.chain.from_iterable(c)) for c in itertools.product(*parts)]


def main():
    if "--ebnf" in sys.argv:
        print(ebnf()); return 0
    lang = set(sentences(R("noun_form")))
    bundles = sorted({l.split("\t")[2] for l in (ROOT / "data/derived/nouns_grid_final.tsv").read_text(encoding="utf-8").splitlines()
                      if l.count("\t") >= 3})
    bad = [b for b in bundles if tuple(t for t in b.split("+") if t) not in lang]
    print(ebnf())
    print()
    print(f"feature bundles in the grid : {len(bundles)}")
    print(f"accepted by the grammar     : {len(bundles) - len(bad)}/{len(bundles)}")
    print(f"combinations it licenses    : {len(lang)}")
    sys.path.insert(0, str(ROOT / "tools"))
    import phon_rules as P
    derived = [x for x in bundles if not P.morphemes(x.lstrip("+"))[1]]
    print(f"derived by tools/phon_rules : {len(derived)}/{len(bundles)}  (the rest carry tags it has no ending for: "
          + ", ".join(sorted({u for x in bundles for u in P.morphemes(x.lstrip('+'))[1]})) + ")")
    for b in bad: print("  NOT ACCEPTED:", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
