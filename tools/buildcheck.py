#!/usr/bin/env python3
"""
Preconditions for the verb build, checked loudly.

Two of the five verb-coverage gains in audit/STEM_ALTERNATION.md were not grammar at all:
a missing `.fst` and a mis-picked cell list. Both were SILENT -- an entire conjugation
class produced zero cells, the builder printed a tidy table, and the process exited 0.
Each was found only by chasing one specific missing word, and each cost more than the
grammar work it was mistaken for.

Every check here converts one of those silent modes into a non-zero exit with the remedy
printed. The standing rule:

    A build that cannot produce a class must not produce a grid.

Usage from a build tool:

    import buildcheck as B
    B.need("flookup")
    B.require_models(FST, ["verb-c3.fst", ...])
    got = B.flookup(FST, model, items)          # raises if flookup itself failed
    ...
    B.report()                                  # raises if anything was recorded

or standalone, to check a build directory before using it:

    python3 tools/buildcheck.py [builddir]
    python3 tools/buildcheck.py --selftest     reproduce each caught failure and assert it
"""
import os, re, sys, shutil, pathlib, subprocess, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLD_FST = ROOT / "data/gold/thamizhi-morph/FST-Models"
SRC      = ROOT / "data/gold/thamizhi-morph/foma/src"

# Every verb model the grid builder can select, and the foma script that compiles it.
# Keep this in step with build_verb_grid.DEDICATED / REST -- check_map() enforces that.
VERB_MODELS = {
    "verb-c3.fst":     "ThamizhiFST-C3.foma",
    "verb-c4.fst":     "ThamizhiFST-C4.foma",
    "verb-c62.fst":    "ThamizhiFST-C62.foma",
    "verb-c11.fst":    "ThamizhiFST-C11.foma",
    "verb-c12.fst":    "ThamizhiFST-C12.foma",
    "verb-c-rest.fst": "ThamizhiFST-otherthan-3-4-62-11-12.foma",
}

def rel(p):
    """Path for display. TAMILOS_VGRID / TAMILOS_VOUT may be absolute and outside the
    repo -- build_verbs.sh points them at the build directory -- and relative_to() then
    raises, which turned a finished 1.36M-cell stage into a traceback."""
    try:    return str(pathlib.Path(p).relative_to(ROOT))
    except ValueError: return str(p)

# Which lexc source each model's lexicon comes from. Used to decide whether a rebuilt
# model SHOULD be identical to the shipped one: unchanged source must give the same
# relation. ThamizhiVerbs-C62.lexc declares C6Vinf, not C62Vinf -- see BUILD_GUARDS.md §3.
VERB_LEXC = {
    "verb-c3.fst":     "ThamizhiVerbs-C3.lexc",
    "verb-c4.fst":     "ThamizhiVerbs-C4.lexc",
    "verb-c62.fst":    "ThamizhiVerbs-C62.lexc",
    "verb-c11.fst":    "ThamizhiVerbs-C11.lexc",
    "verb-c12.fst":    "ThamizhiVerbs-C12.lexc",
    "verb-c-rest.fst": "ThamizhiVerbs-otherthan-3-4-62-11-12.lexc",
}

def source_unchanged(build, model):
    """True when this model's .lexc and .foma in `build` are byte-identical to the gold.

    The honest precondition for asserting that a rebuild reproduces the shipped model.
    "Which classes gained roots" is not the same question -- add_aar_cell.py edits cells,
    not roots, and a build directory can be modified by anything.
    """
    build = pathlib.Path(build)
    for name in (VERB_LEXC.get(model), VERB_MODELS.get(model)):
        if not name: return None
        a, b = build / name, SRC / name
        if not (a.exists() and b.exists()): return None
        if a.read_bytes() != b.read_bytes(): return False
    return True

class BuildError(RuntimeError):
    """Raised for any violated precondition. Build tools let it reach main()."""

_problems = []

def record(kind, msg, fix=None):
    """Note a problem and keep going, so one run reports every fault, not the first."""
    _problems.append((kind, msg, fix))
    print(f"  !! {kind}: {msg}", file=sys.stderr, flush=True)

def report(what="build"):
    """Raise if anything was recorded. Call once, at the end, before writing output."""
    if not _problems:
        return
    lines = [f"{len(_problems)} precondition(s) failed -- {what} NOT written", ""]
    for kind, msg, fix in _problems:
        lines.append(f"  [{kind}] {msg}")
        if fix:
            lines.append(f"      fix: {fix}")
    raise BuildError("\n".join(lines))

def need(*binaries):
    """The toolchain must be on PATH. foma absent means every compile silently no-ops."""
    for b in binaries:
        if not shutil.which(b):
            record("TOOLCHAIN", f"{b} not on PATH",
                   "brew install foma   (or build from github.com/mhulden/foma)")

PROBE_TIMEOUT = int(os.environ.get("TAMILOS_PROBE_TIMEOUT", "30"))

def probe(path):
    """Can flookup actually load this model? Returns None if fine, else the reason.

    Existence is not enough on either count. A zero-length or badly truncated .fst passes
    os.path.exists and makes flookup exit 1 on every call -- which generate() discarded.
    And a .fst truncated mid-structure is worse than useless: flookup neither loads it nor
    exits, it spins. An interrupted compile leaves exactly that file, so the probe is
    timed and a timeout counts as a failure.
    """
    p = pathlib.Path(path)
    if not p.exists():          return "missing"
    if p.stat().st_size == 0:   return "zero-length"
    try:
        r = subprocess.run(["flookup", "-i", str(p)], input="zzz\n",
                           capture_output=True, text=True, timeout=PROBE_TIMEOUT)
        # `input=` already gives a pipe that is closed, so flookup sees EOF. Never let
        # these tools inherit an open stdin: on a bad argument foma drops to its REPL and
        # blocks on a read forever. One did exactly that for 25 hours. See audit/FOMA.md.
    except subprocess.TimeoutExpired:
        return (f"flookup hung for {PROBE_TIMEOUT}s loading it -- the file is truncated "
                f"({p.stat().st_size:,} bytes); delete it and recompile")
    if r.returncode != 0:
        return f"flookup cannot load it (rc={r.returncode}: {r.stderr.strip() or 'no message'})"
    return None

def require_models(fstdir, models, label="model"):
    """Every model the build will select must exist AND load. This is the சென்றார் guard."""
    fstdir = pathlib.Path(fstdir)
    if not fstdir.is_dir():
        record("FSTDIR", f"{fstdir} is not a directory",
               "run tools/rebuild_with_roots.py <builddir> first")
        return
    for m in models:
        why = probe(fstdir / m)
        if why is None:
            continue
        foma = VERB_MODELS.get(m)
        fix = (f"cd {fstdir} && foma -l {foma} -e 'save stack {m}' -e quit" if foma
               else f"copy {m} from {GOLD_FST}")
        record("MODEL", f"{label} {m} in {fstdir}: {why}", fix)

def check_map(dedicated, rest):
    """The builder's class->model map must not name a model this module cannot verify."""
    named = set(dedicated.values()) | {rest}
    unknown = sorted(named - set(VERB_MODELS))
    if unknown:
        record("MAP", f"build_verb_grid selects models unknown to buildcheck: {unknown}",
               "add them to buildcheck.VERB_MODELS with their foma script")

LOOKUP_TIMEOUT = int(os.environ.get("TAMILOS_LOOKUP_TIMEOUT", "1800"))

def flookup(fstdir, model, items, chunk=200000):
    """flookup -i, but a failed invocation is an error, not an empty result.

    The old version swallowed the return code. A missing verb-c3.fst produced rc=1 and an
    empty stdout for every chunk, and the class simply had no cells.
    """
    res = collections.defaultdict(set)
    path = pathlib.Path(fstdir) / model
    for i in range(0, len(items), chunk):
        part = items[i:i + chunk]
        try:
            p = subprocess.run(["flookup", "-i", str(path)],
                               input="\n".join(part) + "\n", capture_output=True,
                               text=True, timeout=LOOKUP_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise BuildError(f"flookup on {path} exceeded {LOOKUP_TIMEOUT}s for "
                             f"{len(part):,} items -- model truncated, or raise "
                             f"TAMILOS_LOOKUP_TIMEOUT")
        if p.returncode != 0 or (p.stderr and "error" in p.stderr.lower()):
            raise BuildError(f"flookup failed on {path} "
                             f"(rc={p.returncode}, chunk {i}..{i+len(part)}): "
                             f"{p.stderr.strip() or 'no message'}")
        for line in p.stdout.splitlines():
            q = line.split("\t")
            if len(q) == 2 and q[1] != "+?":
                res[q[0]].add(q[1])
    return res

# ---------------------------------------------------------------- grid invariants
TENSES = ("past", "pres", "fut")

def tense_of(feats):
    """Which tense a cell's feature string carries, or None for a non-finite cell."""
    for t in TENSES:
        if f"+{t}=" in feats:
            return t
    return None

def check_class(cls, feats, produced):
    """A class must produce cells, and must produce them in all three tenses.

    The C6 bug is exactly this shape: the cell list offered only past=க், which C6 roots
    reject, so 88 roots generated cells in the present and future and ZERO in the past.
    A per-class total would have looked healthy. A per-tense total does not.
    """
    if not produced:
        record("EMPTY CLASS", f"{cls} has roots and a cell list but generated 0 cells",
               "wrong model selected, or its .fst does not contain this class")
        return
    want = {t for t in (tense_of(f) for f in feats) if t}
    got  = {t for t in (tense_of(f) for f in produced) if t}
    for t in sorted(want - got):
        record("EMPTY TENSE", f"{cls}: {t} cells were offered but none generated "
                              f"({sum(1 for f in feats if tense_of(f) == t)} offered)",
               "the cell list's tense marker is one this class's roots reject -- "
               "union the LEXICON blocks rather than taking the first")

def check_roots(cls, rts, got, feats):
    """No root may generate zero cells after every model has been tried.

    The per-class and per-tense checks both pass while a handful of roots produce nothing,
    because a class of 95 roots looks healthy on 91 of them. This is the check that found
    நெகு, இகு, தொகு and நகு -- C6 roots compiled only into verb-c62.fst, which the class
    does not select.
    """
    dead = [r for r in rts if not any((r + f) in got for f in feats)]
    if dead:
        shown = ", ".join(dead[:8]) + (f" … +{len(dead)-8} more" if len(dead) > 8 else "")
        record("DEAD ROOTS", f"{cls}: {len(dead)} of {len(rts)} roots generate no cells "
                             f"in any model -- {shown}",
               "the root is in a lexc file whose model no class selects, or its class "
               "assignment in data/derived/new_roots.tsv is wrong")

def check_cells(roots, cells):
    """Every class with roots needs a cell list; every cell list needs all three tenses."""
    for cls in sorted(set(roots) - set(cells)):
        record("NO CELLS", f"{cls} has {len(roots[cls])} roots but no cell list",
               f"no 'LEXICON {cls}Vinf' block matched in {SRC}")
    for cls, feats in sorted(cells.items()):
        if cls not in roots:
            continue
        missing = [t for t in TENSES if not any(tense_of(f) == t for f in feats)]
        if missing:
            record("NO TENSE", f"{cls}: cell list has no {'/'.join(missing)} cells",
                   f"check the LEXICON {cls}Vinf blocks -- the class may be declared "
                   f"more than once and the blocks must be unioned")

def check_grid_tags(path, require=True):
    """Every row's register-tag count must equal its surface count.

    The tags are what make a Naṉṉūl-licensed but corpus-absent form recoverable instead of
    deleted, so a silently misaligned column would quietly restore the bug they exist to
    fix. Adding a column has already broken two parsers in this project once.
    """
    path = pathlib.Path(path)
    if not path.exists():
        record("GRID TAGS", f"{path} does not exist"); return {}
    bad = untagged = rows = 0
    first = None
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            q = line.rstrip("\n").split("\t")
            if len(q) < 4: continue
            rows += 1
            if len(q) < 5:
                untagged += 1; continue
            ns, nt = len(q[3].split("|")), len(q[4].split("|"))
            if ns != nt:
                bad += 1
                if first is None: first = f"line {i}: {ns} surfaces, {nt} tags"
    if bad:
        record("GRID TAGS", f"{path.name}: {bad:,} of {rows:,} rows have a tag count that "
                            f"does not match the surface count ({first})",
               "the writer must emit one tag per surface, in the same order")
    if require and rows and untagged == rows:
        record("GRID TAGS", f"{path.name}: no row has a register column",
               "fix_verb_grid.py should emit a 5th column of B/C tags")
    return {"rows": rows, "untagged": untagged, "misaligned": bad}

def check_total(n, floor):
    """A grid far below its known size means a stage no-oped. Refuse to overwrite."""
    if n < floor:
        record("GRID SIZE", f"{n:,} cells is below the floor of {floor:,}",
               "a class or a whole stage produced nothing; fix the faults above")

# ----------------------------------------------------------------------- self-test
def selftest():
    """Rebuild each failure this module exists for, and assert it is still caught.

    A guard nobody has seen fire is not a guard. Each case below is a real state this
    build has been in.
    """
    import tempfile, shutil as sh
    global _problems
    cases, failed = [], 0

    def case(name, fn, want):
        global _problems
        _problems = []
        try:
            fn()
        except BuildError:
            pass
        kinds = [k for k, _, _ in _problems]
        ok = want in kinds
        if want is None: ok = not kinds
        cases.append((ok, name, want, kinds))
        return ok

    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        sh.copy(GOLD_FST / "verb-c11.fst", d / "verb-c11.fst")          # one good model
        # 1. the சென்றார் state: a model absent from the build dir
        case("missing model", lambda: require_models(d, ["verb-c3.fst"]), "MODEL")
        # 2. an interrupted compile: a truncated .fst that hangs flookup
        (d / "verb-c62.fst").write_bytes((GOLD_FST / "verb-c62.fst").read_bytes()[:200])
        os.environ["TAMILOS_PROBE_TIMEOUT"] = "5"
        global PROBE_TIMEOUT; PROBE_TIMEOUT = 5
        case("truncated model", lambda: require_models(d, ["verb-c62.fst"]), "MODEL")
        # 3. a zero-length .fst, which exists() happily accepts
        (d / "verb-c4.fst").write_bytes(b"")
        case("zero-length model", lambda: require_models(d, ["verb-c4.fst"]), "MODEL")
        # 4. a good model must NOT be reported
        case("good model passes", lambda: require_models(d, ["verb-c11.fst"]), None)
        # 5. the C6 state: past cells offered, none generated
        offered = ["+verb+fin+past=க்+3sgn=அது", "+verb+fin+pres=கிற்+3sgn=அது",
                   "+verb+fin+fut=வ்+3sgn=அது"]
        case("empty tense", lambda: check_class("C6", offered, set(offered[1:])),
             "EMPTY TENSE")
        # 6. the நெகு state: a class is fine but some of its roots generate nothing
        case("dead roots", lambda: check_roots("C6", ["நகு", "படு"],
                                               {"படு" + offered[0]: {"பட்டது"}},
                                               [offered[0]]), "DEAD ROOTS")
        # 7. a class with roots but no cell list
        case("no cell list", lambda: check_cells({"C9": ["x"]}, {}), "NO CELLS")
        # 8. a cell list with no past cells at all
        case("cell list lacks a tense",
             lambda: check_cells({"C9": ["x"]}, {"C9": offered[1:]}), "NO TENSE")
        # 9. a grid far below its known size
        case("grid floor", lambda: check_total(12, 1200000), "GRID SIZE")
        # 10. a model the builder selects that this module cannot verify
        case("unknown model in map", lambda: check_map({"CX": "verb-cx.fst"},
                                                       "verb-c-rest.fst"), "MAP")

    _problems = []
    print()
    for ok, name, want, kinds in cases:
        mark = "ok  " if ok else "FAIL"
        exp = want or "(nothing)"
        print(f"  {mark} {name:<26} expected {exp:<12} got {kinds or '[]'}")
        failed += 0 if ok else 1
    print(f"\n{len(cases) - failed}/{len(cases)} guards fire as intended")
    return 0 if failed == 0 else 1

# ---------------------------------------------------------------------- standalone
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    build = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else GOLD_FST
    print(f"checking {build}", flush=True)
    need("flookup", "foma")
    require_models(build, sorted(VERB_MODELS))
    try:
        report(f"check of {build}")
    except BuildError as e:
        print(f"\nFAIL\n{e}", file=sys.stderr)
        return 2
    print(f"  ok: {len(VERB_MODELS)} verb models present and loadable")
    return 0

if __name__ == "__main__":
    sys.exit(main())
