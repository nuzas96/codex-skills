#!/usr/bin/env python3
"""Validate the fast routing manifest against canonical V2 skills and cases."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "ROUTING_INDEX.json"
CASES_FILE = ROOT / "scripts" / "routing_cases.json"


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def normalize_signal(value: str) -> str:
    return " ".join(value.lower().split())


def main() -> int:
    errors = 0

    try:
        index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse ROUTING_INDEX.json: {exc}")
        return 1

    if index.get("schema_version") != 1:
        fail("schema_version must be 1")
        errors += 1

    fallback = index.get("fallback_skill")
    if not isinstance(fallback, str) or not (ROOT / fallback).is_file():
        fail(f"fallback_skill missing or invalid: {fallback!r}")
        errors += 1

    routes = index.get("routes")
    if not isinstance(routes, list) or not routes:
        fail("routes must be a non-empty list")
        return 1

    seen_ids: set[str] = set()
    seen_signals: dict[str, str] = {}
    indexed_pairs: set[tuple[str, str | None]] = set()

    for pos, route in enumerate(routes, start=1):
        if not isinstance(route, dict):
            fail(f"route #{pos} is not an object")
            errors += 1
            continue

        route_id = route.get("id")
        primary = route.get("primary_skill")
        reference = route.get("reference")
        signals = route.get("signals")

        if not isinstance(route_id, str) or not route_id.strip():
            fail(f"route #{pos} has invalid id")
            errors += 1
        elif route_id in seen_ids:
            fail(f"duplicate route id: {route_id}")
            errors += 1
        else:
            seen_ids.add(route_id)

        if not isinstance(primary, str) or not primary:
            fail(f"{route_id}: missing primary_skill")
            errors += 1
            continue

        skill_file = ROOT / primary / "SKILL.md"
        if not skill_file.is_file():
            fail(f"{route_id}: primary skill missing: {primary}/SKILL.md")
            errors += 1

        if reference is not None:
            if not isinstance(reference, str) or not reference:
                fail(f"{route_id}: reference must be string or null")
                errors += 1
            else:
                ref_path = ROOT / reference
                if not ref_path.is_file():
                    fail(f"{route_id}: mapped reference missing: {reference}")
                    errors += 1
                else:
                    try:
                        ref_path.resolve().relative_to((ROOT / primary).resolve())
                    except ValueError:
                        fail(f"{route_id}: reference escapes canonical owner {primary}: {reference}")
                        errors += 1

        if not isinstance(signals, list) or not signals:
            fail(f"{route_id}: signals must be a non-empty list")
            errors += 1
        else:
            local_signals: set[str] = set()
            for raw in signals:
                if not isinstance(raw, str) or not raw.strip():
                    fail(f"{route_id}: invalid signal {raw!r}")
                    errors += 1
                    continue
                signal = normalize_signal(raw)
                if signal in local_signals:
                    fail(f"{route_id}: duplicate signal inside route: {raw!r}")
                    errors += 1
                local_signals.add(signal)

                owner = seen_signals.get(signal)
                if owner is not None and owner != route_id:
                    fail(f"signal {raw!r} is duplicated across {owner} and {route_id}")
                    errors += 1
                else:
                    seen_signals[signal] = route_id

        indexed_pairs.add((primary, reference))

    try:
        cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse routing_cases.json: {exc}")
        return 1

    missing_coverage = 0
    for case in cases:
        primary = case.get("primary_skill")
        refs = case.get("references", [])
        reference = refs[0] if refs else None
        pair = (primary, reference)
        if pair not in indexed_pairs:
            fail(
                "routing index lacks representative coverage for "
                f"{case.get('case')!r}: {primary} -> {reference}"
            )
            errors += 1
            missing_coverage += 1

    print(f"Routing index routes: {len(routes)}")
    print(f"Unique signals: {len(seen_signals)}")
    print(f"Representative cases covered: {len(cases) - missing_coverage}/{len(cases)}")
    print(f"Errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
