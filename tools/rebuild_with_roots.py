#!/usr/bin/env python3
"""
Insert the new roots into the lexc sources and recompile the FST models with foma.

The shipped .fst files have their lexicon baked in, so adding a root means rebuilding.
Verified first that recompiling an untouched class reproduces the shipped model exactly
(C11: 2,576,470 paths, 66,925 bytes — identical), so the build is faithful.

Writes into a scratch build directory; the vendored gold under data/gold/ is never
modified.

  python3 tools/rebuild_with_roots.py <builddir>

⚠️ Compilation is delegated to tools/compile_models.py, which compiles EVERY verb model,
not only the classes that gained roots. The earlier version compiled only the touched
ones, so verb-c3.fst and verb-c62.fst were never written into the build directory at all —
and build_verb_grid, reading its models from there, produced zero cells for C3 (46 roots,
including செல்) and C62 without a word of complaint. செல் looked like a verb with no past
tense for a whole session. A partial recompile IS the bug, so there is no flag to ask for
one. If you edit the lexc files after this runs (add_aar_cell.py does), run
compile_models.py again before generating; tools/build_verbs.sh gets the order right.
"""
import re, sys, shutil, pathlib, collections

ROOT  = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import buildcheck as B
import compile_models as C

SRC   = ROOT / "data/gold/thamizhi-morph/foma/src"
NEW   = ROOT / "data/derived/new_roots.tsv"
BUILD = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/tamilos-build")

# class -> (lexc file, foma script, output model)
WHERE = {
    "C11": ("ThamizhiVerbs-C11.lexc", "ThamizhiFST-C11.foma", "verb-c11.fst"),
    "C12": ("ThamizhiVerbs-C12.lexc", "ThamizhiFST-C12.foma", "verb-c12.fst"),
    "C4":  ("ThamizhiVerbs-C4.lexc",  "ThamizhiFST-C4.foma",  "verb-c4.fst"),
    "C3":  ("ThamizhiVerbs-C3.lexc",  "ThamizhiFST-C3.foma",  "verb-c3.fst"),
    "C62": ("ThamizhiVerbs-C62.lexc", "ThamizhiFST-C62.foma", "verb-c62.fst"),
}
REST = ("ThamizhiVerbs-otherthan-3-4-62-11-12.lexc",
        "ThamizhiFST-otherthan-3-4-62-11-12.foma", "verb-c-rest.fst")

def main():
    B.need("foma", "flookup")
    if not SRC.is_dir():
        B.record("SRC", f"{SRC} is not a directory", "the vendored gold is missing")
    B.report("rebuild")

    BUILD.mkdir(parents=True, exist_ok=True)
    src = list(SRC.glob("*.lexc")) + list(SRC.glob("*.foma"))
    if not src:
        B.record("SRC", f"no .lexc/.foma under {SRC}")
    for f in src:
        shutil.copy(f, BUILD / f.name)
    print(f"copied {len(src)} source files -> {BUILD}")

    byclass = collections.defaultdict(list)
    for line in NEW.read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) >= 2: byclass[p[1]].append(p[0])
    print(f"roots to add: {sum(len(v) for v in byclass.values())}  "
          f"{dict((k,len(v)) for k,v in byclass.items())}")

    gained = set()
    for cls, roots in byclass.items():
        lexc, foma, out = WHERE.get(cls, REST)
        path = BUILD / lexc
        lines = path.read_text(encoding="utf-8").splitlines()
        pat = re.compile(rf'^\S+\s+{cls}Vinf\s*;')
        last = max((i for i, l in enumerate(lines) if pat.match(l)), default=None)
        if last is None:
            # Was a warning-and-continue. Silently dropping the roots meant the measured
            # coverage was of a lexicon nobody had actually built.
            B.record("ROOT INSERT", f"no existing {cls}Vinf root line in {lexc}; "
                                    f"{len(roots)} roots would be dropped",
                     f"check that {cls} belongs in {lexc}, or add it to WHERE")
            continue
        for r in roots:
            lines.insert(last + 1, f"{r}\t{cls}Vinf;")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        gained.add(out)
        print(f"  {cls:<5} +{len(roots):<4} -> {lexc}")
    B.report("rebuild")           # do not compile a lexicon that lost roots

    print()
    C.compile_all(BUILD, gained)
    B.report("rebuild")
    print(f"\nbuild dir: {BUILD}   all {len(B.VERB_MODELS)} models present and loadable")

if __name__ == "__main__":
    try:
        main()
    except B.BuildError as e:
        print(f"\nREBUILD FAILED\n{e}", file=sys.stderr)
        sys.exit(2)
