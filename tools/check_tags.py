#!/usr/bin/env python3
"""Gate: the verb grid's register column must have one tag per surface, on every row.

  python3 tools/check_tags.py <grid.tsv>
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import buildcheck as B

def main():
    if len(sys.argv) < 2:
        print(__doc__.strip()); return 2
    st = B.check_grid_tags(sys.argv[1])
    if st:
        print(f"  rows {st['rows']:,}   untagged {st['untagged']:,}   "
              f"misaligned {st['misaligned']:,}")
    B.report("register tags")
    print("  ok: one tag per surface on every row")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except B.BuildError as e:
        print(f"\nTAG CHECK FAILED\n{e}", file=sys.stderr)
        sys.exit(2)
