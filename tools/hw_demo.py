#!/usr/bin/env python3
"""
Ask the noun generator hardware (as simulated from hdl/rtl/tamil_noun_gen.sv) for the forms of a word.

    python3 tools/hw_demo.py மரம் C15 noun+loc
    python3 tools/hw_demo.py குழந்தை C2 noun+dat noun+pl+dat

For each bundle it prints what the hardware produced and what phon_rules.derive() says, and whether they are
the same set. The class is the declension class as phon_rules names it (C1..C16, NDBLT, NDBLR, NCLUST, NMURRI).
Needs iverilog; the testbench is hdl/tb/tb_noun_gen.v.
"""
import sys, subprocess, tempfile, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import tlp1 as T
import phon_rules as P
import gen_noun_gen_hdl as G


def main():
    if len(sys.argv) < 4: sys.exit(__doc__)
    stem, cls, bundles = sys.argv[1], sys.argv[2], sys.argv[3:]
    G.OUT_VH.write_text(G.rom_vh(), encoding="utf-8")
    recs = [G.record(stem, cls, b) for b in bundles]
    if None in recs: sys.exit("a bundle could not be derived (unknown feature, or the stem is not Tamil)")
    hdl = ROOT / "hdl"
    with tempfile.TemporaryDirectory() as d:
        vec = pathlib.Path(d) / "v.hex"
        vec.write_text("".join(" ".join(f"{x:x}" for x in r) + "\n" for r in recs), encoding="utf-8")
        vvp = pathlib.Path(d) / "t.vvp"
        subprocess.run(["iverilog", "-g2012", "-I.", "-o", str(vvp), "tb/tb_noun_gen.v", "rtl/tamil_noun_gen.sv",
                        "rtl/tamil_join.sv"], cwd=hdl, check=True)
        out = subprocess.run(["vvp", str(vvp), f"+vec={vec}", "+show"], cwd=hdl, capture_output=True, text=True).stdout
    forms = {}
    for line in out.splitlines():
        if line.startswith("FORM "):
            p = line.split(); forms.setdefault(int(p[1]), set()).add(T.decode(bytes(int(x, 16) for x in p[2:])))
    for i, b in enumerate(bundles):
        hw, py = forms.get(i, set()), P.derive(stem, cls, b)
        print(f"{stem}  {cls}  {b}")
        print("   hardware :", "  ".join(sorted(hw)))
        print("   python   :", "  ".join(sorted(py)), "   ->", "same set" if hw == py else "DIFFERENT")


if __name__ == "__main__":
    main()
