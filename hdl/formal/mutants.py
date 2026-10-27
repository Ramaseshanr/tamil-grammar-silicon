#!/usr/bin/env python3
"""
Does the formal check have teeth? Break tamil_join.sv in seven ways, one at a time, and require the proof to fail
each time. (An eighth change, a mask of 0xF0 for 0xF8 in the assimilation rule, is not listed: the rule applies only
when a is ம் = 0x54, where both masks give 0x50, so the change is not a change and the proof rightly still passes.)

    cd hdl/formal && python3 mutants.py
"""
import subprocess, pathlib, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
HDL = HERE.parent
RTL = (HDL / "rtl/tamil_join.sv").read_text(encoding="utf-8")
MUTANTS = {
    "P5 forgets the consonant before the உ":   ("kural && (a == `U) && b_v && a2m)", "kural && (a == `U) && b_v)"),
    "P2 ignores the nohard flag":              ("hard_a && b_val && !pada && !nohard", "hard_a && b_val && !pada"),
    "the glide swaps ய் and வ்":                ("ins_b = front ? `YA : `VA;", "ins_b = front ? `VA : `YA;"),
    "P3 happens away from a pada juncture":    ("end else if (pada && a_mel) begin", "end else if (a_mel) begin"),
    "P9 coalesces without the increment":      ("end else if (inc && a_v && (a == b)) begin", "end else if (a_v && (a == b)) begin"),
    "P2 hardens to the wrong class":           ("ins_b = (a & 8'h07) | 8'h40;", "ins_b = (a & 8'h07) | 8'h50;"),
    "P11 doubles the wrong sound":             ("ins_v = 1'b1; ins_b = a;\n        end else if (a_v && b_val && gem", "ins_v = 1'b1; ins_b = b;\n        end else if (a_v && b_val && gem"),
}


def run(sby_text, cwd):
    (cwd / "m.sby").write_text(sby_text)
    return subprocess.run(["sby", "-f", "m.sby"], cwd=cwd, capture_output=True, text=True).returncode


def main():
    base = (HERE / "join.sby").read_text()
    caught = 0
    for name, (a, b) in MUTANTS.items():
        assert a in RTL, f"mutation site not found: {name}"
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "mut.sv").write_text(RTL.replace(a, b), encoding="utf-8")
            sby = (base.replace("rtl/tamil_join.sv ../rtl/tamil_join.sv", f"rtl/tamil_join.sv {d}/mut.sv")
                       .replace("gen/tamil_phon.vh ../gen/tamil_phon.vh", f"gen/tamil_phon.vh {HDL}/gen/tamil_phon.vh")
                       .replace("formal/join_spec.sv join_spec.sv", f"formal/join_spec.sv {HERE}/join_spec.sv")
                       .replace("formal/join_equiv.sv join_equiv.sv", f"formal/join_equiv.sv {HERE}/join_equiv.sv"))
            rc = run(sby, d)
        print(f"  {'caught' if rc else 'MISSED':7s} {name}")
        caught += bool(rc)
    print(f"\n  mutants caught : {caught}/{len(MUTANTS)}")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
