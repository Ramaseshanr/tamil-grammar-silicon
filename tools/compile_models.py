#!/usr/bin/env python3
"""
Compile every verb model in a build directory, and prove each one loads.

Compilation is a separate tool because it is not a single step in the pipeline: roots go
in (rebuild_with_roots.py), then cells (add_aar_cell.py), and both edit the same .lexc
files. Whoever edits last must recompile, and the only safe rule is that compilation
always covers ALL models. Selective recompiling is what left verb-c3.fst and verb-c62.fst
out of the build directory for a whole session — see audit/BUILD_GUARDS.md.

  python3 tools/compile_models.py <builddir>
"""
import re, sys, time, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import buildcheck as B

COMPILE_TIMEOUT = int(__import__("os").environ.get("TAMILOS_COMPILE_TIMEOUT", "1800"))

def paths_of(fst):
    """Path count of a compiled model. `load stack` reports it without enumerating."""
    fst = pathlib.Path(fst)
    if not fst.exists(): return None
    try:
        r = subprocess.run(["foma", "-e", f"load stack {fst}", "-e", "quit"],
                           stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    m = re.findall(r'([\d,]+) paths', r.stdout)
    return m[-1] if m else None

def compile_one(build, foma, out, why=""):
    """Compile one model and prove the result is loadable. Never fail quietly."""
    build = pathlib.Path(build)
    dst = build / out
    if dst.exists(): dst.unlink()        # a stale model must not survive a failed compile
    t = time.time()
    try:
        # stdin=DEVNULL is not optional. foma exits 0 on every failure tested -- a missing
        # script, an empty stack, a broken regex -- and on a bad argument it falls through
        # to its interactive REPL. With an inherited open stdin it then blocks on a read
        # and never returns; one such process sat for 25 hours. See audit/FOMA.md.
        r = subprocess.run(["foma", "-l", foma, "-e", f"save stack {out}", "-e", "quit"],
                           cwd=build, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True,
                           timeout=COMPILE_TIMEOUT)
    except subprocess.TimeoutExpired:
        B.record("COMPILE", f"{out}: foma exceeded {COMPILE_TIMEOUT}s",
                 "raise TAMILOS_COMPILE_TIMEOUT, or check the .foma script for a blowup")
        return False
    paths = re.findall(r'([\d,]+) paths', r.stdout)
    sz = dst.stat().st_size if dst.exists() else 0
    bad = None
    # r.returncode is nearly worthless here -- foma returns 0 for every failure mode
    # measured. It is checked anyway, but the real evidence is the artefact below.
    if r.returncode != 0:      bad = f"foma rc={r.returncode}"
    elif sz == 0:              bad = "no output file"
    else:                      bad = B.probe(dst)   # non-empty is not the same as loadable
    print(f"  {out:<18} {paths[-1] if paths else '?':>12} paths   {sz:>9,} bytes   "
          f"{time.time()-t:5.0f}s   {why}", flush=True)
    if bad:
        tail = (r.stderr or r.stdout).strip().splitlines()[-3:]
        B.record("COMPILE", f"{out} did not build from {foma}: {bad}",
                 f"foma said: {' / '.join(tail) if tail else 'nothing'}")
        return False
    return True

def equivalent(a, b):
    """Are two .fst files the same RELATION? The only sound way to compare them.

    A .fst is gzip and carries a metadata word that varies between runs, so two compiles
    of identical source can differ in bytes and in gzip size while encoding the same
    machine -- measured: verb-c-rest at 131,829 vs 131,831 bytes, same 7,759,116 paths,
    `test equivalent` TRUE. Checksumming a .fst proves nothing. See audit/FOMA.md.
    """
    a, b = pathlib.Path(a), pathlib.Path(b)
    if not (a.exists() and b.exists()): return None
    try:
        r = subprocess.run(["foma", "-e", f"load stack {a}", "-e", f"load stack {b}",
                            "-e", "test equivalent", "-e", "quit"],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           timeout=600)
    except subprocess.TimeoutExpired:
        return None
    m = re.findall(r'^([01]) \(1 = TRUE', r.stdout, re.M)
    return (m[-1] == "1") if m else None

def compile_all(build, gained=(), compare=True):
    """Compile all six verb models. `gained` only labels the output, never selects."""
    build = pathlib.Path(build)
    print(f"compiling all {len(B.VERB_MODELS)} verb models in {build}:")
    for out, foma in sorted(B.VERB_MODELS.items()):
        if not (build / foma).exists():
            B.record("FOMA SCRIPT", f"{foma} not in {build}",
                     "copy data/gold/thamizhi-morph/foma/src/* into the build dir first")
            continue
        compile_one(build, foma, out, "new roots" if out in gained else "")
    if compare:
        # The shipped models are the reference. Compare PATH COUNTS, not bytes -- and for a
        # class that gained nothing, assert the stronger property that the rebuilt net is
        # the same relation as the shipped one.
        print("\nvs shipped gold:")
        for out in sorted(B.VERB_MODELS):
            sp, bp = paths_of(B.GOLD_FST / out), paths_of(build / out)
            note = ""
            # Assert equivalence only where the SOURCE is byte-identical to the gold.
            # That is the real precondition; "gained no roots" is not, because
            # add_aar_cell.py edits cells and a build directory can be modified by anything.
            same_src = B.source_unchanged(build, out)
            if same_src is True:
                eq = equivalent(B.GOLD_FST / out, build / out)
                note = ("   source unchanged, equivalent to shipped" if eq is True else
                        "   !! source unchanged but NOT equivalent" if eq is False else
                        "   (source unchanged; equivalence not determined)")
                if eq is False:
                    B.record("NOT EQUIVALENT",
                             f"{out}: its .lexc/.foma are identical to the gold, yet the "
                             f"rebuilt net is not the same relation as the shipped model",
                             "foma itself is giving a different answer -- check its version")
            elif same_src is False:
                note = "   source edited"
            print(f"  {out:<18} shipped {str(sp):>12}   built {str(bp):>12}{note}",
                  flush=True)
    B.require_models(build, sorted(B.VERB_MODELS))

def main():
    if len(sys.argv) < 2:
        print(__doc__.strip()); return 2
    B.need("foma", "flookup")
    B.report("compile")
    build = pathlib.Path(sys.argv[1])
    if not build.is_dir():
        B.record("BUILDDIR", f"{build} is not a directory")
        B.report("compile")
    compile_all(build)
    B.report("compile")
    print(f"\nall {len(B.VERB_MODELS)} models present and loadable in {build}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except B.BuildError as e:
        print(f"\nCOMPILE FAILED\n{e}", file=sys.stderr)
        sys.exit(2)
