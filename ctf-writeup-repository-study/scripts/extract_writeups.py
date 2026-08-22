#!/usr/bin/env python3
"""
Batched read helper for CTF writeup repository study.

Walks a directory tree (e.g. a shallow git clone in /tmp), finds every
`writeup.md` (with optional extension override), groups by top-level category
directory, and prints a single structured dump suitable for triage in one
tool output block.

Usage:
    python3 extract_writeups.py /tmp/DalCTF2026
    python3 extract_writeups.py /tmp/some-repo --glob "WRITEUP.md"
    python3 extract_writeups.py /tmp/some-repo --max-lines 30   # skip very long writeups
    python3 extract_writeups.py /tmp/some-repo --summary         # just counts

Designed for the ctf-writeup-repository-study skill workflow — do NOT use
this to read source code, binaries, or anything that isn't a writeup.
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(
        description="Batched-read every writeup.md in a CTF writeup repo."
    )
    p.add_argument("path", help="Repo root (e.g. /tmp/DalCTF2026)")
    p.add_argument(
        "--glob",
        default="writeup.md",
        help="Filename glob to match (default: writeup.md). Case-sensitive.",
    )
    p.add_argument(
        "--max-lines",
        type=int,
        default=0,
        help="If > 0, truncate writeups longer than this many lines (mark with [TRUNCATED]).",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Just print per-category counts and total line/char stats; skip content.",
    )
    args = p.parse_args()

    repo = Path(args.path)
    if not repo.is_dir():
        print(f"ERROR: {repo} is not a directory", file=sys.stderr)
        return 1

    writeups = sorted(repo.rglob(args.glob))
    if not writeups:
        print(f"ERROR: no files matching {args.glob!r} under {repo}", file=sys.stderr)
        return 2

    by_cat: dict[str, list[Path]] = defaultdict(list)
    for w in writeups:
        parts = w.relative_to(repo).parts
        cat = parts[0] if len(parts) > 1 else "?"
        by_cat[cat].append(w)

    total_chars = 0
    total_lines = 0
    for cat in sorted(by_cat):
        files = by_cat[cat]
        cat_lines = sum(sum(1 for _ in open(f, encoding="utf-8", errors="replace")) for f in files)
        cat_chars = sum(f.stat().st_size for f in files)
        total_lines += cat_lines
        total_chars += cat_chars
        print(f"{cat:20} {len(files):3} files  {cat_lines:5} lines  {cat_chars:7} chars")

    print(
        f"\n{'TOTAL':20} {len(writeups):3} files  {total_lines:5} lines  {total_chars:7} chars"
    )

    if args.summary:
        return 0

    print("\n" + "=" * 60)
    for cat in sorted(by_cat):
        print(f"\n{'=' * 60}\n=== {cat} ({len(by_cat[cat])} writeups) ===\n{'=' * 60}")
        for w in by_cat[cat]:
            rel = w.relative_to(repo)
            try:
                content = w.read_text(encoding="utf-8", errors="replace").strip()
            except Exception as e:
                print(f"\n--- {rel} --- READ ERROR: {e}")
                continue

            if args.max_lines and content.count("\n") + 1 > args.max_lines:
                lines = content.splitlines()
                content = "\n".join(lines[: args.max_lines]) + f"\n... [TRUNCATED, was {len(lines)} lines]"

            print(f"\n--- {rel} ({len(content)} chars) ---")
            print(content)
            print("---END---")

    return 0


if __name__ == "__main__":
    sys.exit(main())
