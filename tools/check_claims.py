#!/usr/bin/env python3
"""
Gate for the paper drafts: a claimed number whose source has changed since it was last
verified is STALE, and says so.

A living paper's failure mode is not being wrong, it is going quietly out of date. Every
number in paper/*.md is listed in paper/CLAIMS.tsv with the command that regenerates it,
the files whose change invalidates it, and the commit it was last verified at. This walks
the ledger and reports which claims the repository has moved out from under.

It does NOT re-run the commands -- several take minutes. It tells you which ones to re-run.

This gate is deliberately conservative: it compares commits, so it cannot tell a
behaviour change from a comment change and will flag both. When it fires, read the diff
before blessing -- a comment-only edit (a corrected citation, say) is safe to bless
without re-running, and anything else is not.

Adding a claim: commit its source file FIRST, then add the row, or the row carries a
commit older than the file it depends on and reports stale on the next run. `--bless`
exists for that case -- but only use it when you have just run the command.

    python3 tools/check_claims.py          # report
    python3 tools/check_claims.py --strict # exit 1 if anything is stale (for a hook/CI)
    python3 tools/check_claims.py --bless  # mark every claim verified at HEAD
"""
import csv, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "paper/CLAIMS.tsv"

def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a],
                          capture_output=True, text=True).stdout.strip()

def last_touch(paths):
    """The most recent commit touching any of these paths."""
    best = None
    for p in paths:
        h = git("log", "-1", "--format=%H", "--", p)
        if not h: continue
        if best is None or not is_ancestor(h, best): best = h
    return best

def is_ancestor(a, b):
    return subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", a, b],
                          capture_output=True).returncode == 0

def main():
    strict = "--strict" in sys.argv
    bless = "--bless" in sys.argv
    head = git("rev-parse", "HEAD")
    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8"), delimiter="\t"))

    if bless:
        short = git("rev-parse", "--short", "HEAD")
        for r in rows: r["verified_at"] = short
        with LEDGER.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter="\t", lineterminator="\n")
            w.writeheader(); w.writerows(rows)
        print(f"  blessed {len(rows)} claims at {short}")
        return 0

    stale, unknown, fresh = [], [], 0
    for r in rows:
        srcs = [s.strip() for s in r["sources"].split(",") if s.strip()]
        touched = last_touch(srcs)
        ver = git("rev-parse", r["verified_at"]) if r["verified_at"] else ""
        if not ver:
            unknown.append((r, "never verified")); continue
        if touched and not is_ancestor(touched, ver):
            stale.append((r, touched[:9]))
        else:
            fresh += 1

    print(f"  paper/CLAIMS.tsv — {len(rows)} claims   fresh {fresh}   "
          f"stale {len(stale)}   unverified {len(unknown)}")
    if git("status", "--porcelain"):
        print("  ! working tree is dirty; uncommitted edits are not considered")
    for r, why in stale:
        print(f"\n  STALE  {r['id']}  = {r['value']}")
        print(f"         {r['claim']}")
        print(f"         source moved at {why}, verified at {r['verified_at']}")
        print(f"         re-run:  {r['command']}")
    for r, why in unknown:
        print(f"\n  ?      {r['id']}  — {why}")
    if stale and strict:
        return 1
    if not stale and not unknown:
        print("  ok: every claimed number is at least as new as its source")
    return 0

if __name__ == "__main__":
    sys.exit(main())
