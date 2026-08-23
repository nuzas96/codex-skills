#!/usr/bin/env python3
"""Validate representative V2 routing cases against the repository tree."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = Path(__file__).with_name("routing_cases.json")


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def main() -> int:
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    errors = 0

    if not isinstance(cases, list) or not cases:
        fail("routing_cases.json must contain a non-empty list")
        return 1

    seen_cases: set[str] = set()

    for index, case in enumerate(cases, start=1):
        label = case.get("case")
        primary = case.get("primary_skill")
        references = case.get("references", [])

        if not isinstance(label, str) or not label.strip():
            fail(f"case #{index} has no valid label")
            errors += 1
            continue
        if label in seen_cases:
            fail(f"duplicate routing case label: {label}")
            errors += 1
        seen_cases.add(label)

        if not isinstance(primary, str) or not primary:
            fail(f"{label}: missing primary_skill")
            errors += 1
            continue

        skill_file = ROOT / primary / "SKILL.md"
        if not skill_file.is_file():
            fail(f"{label}: primary skill missing: {primary}/SKILL.md")
            errors += 1

        if not isinstance(references, list):
            fail(f"{label}: references must be a list")
            errors += 1
            continue

        for raw in references:
            if not isinstance(raw, str) or not raw:
                fail(f"{label}: invalid reference value: {raw!r}")
                errors += 1
                continue

            ref = ROOT / raw
            if not ref.is_file():
                fail(f"{label}: missing routed reference: {raw}")
                errors += 1
                continue

            try:
                rel_parts = ref.resolve().relative_to((ROOT / primary).resolve()).parts
            except ValueError:
                fail(f"{label}: reference escapes primary owner {primary}: {raw}")
                errors += 1
                continue

            if not rel_parts:
                fail(f"{label}: reference must be a file inside {primary}: {raw}")
                errors += 1

    print(f"Routing cases: {len(cases)}")
    print(f"Errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
