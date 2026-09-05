#!/usr/bin/env python3
"""Validate the fast routing manifest, representative cases, and routing semantics."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "ROUTING_INDEX.json"
CASES_FILE = ROOT / "scripts" / "routing_cases.json"
EDGE_CASES_FILE = ROOT / "scripts" / "routing_edge_cases.json"


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def normalize_signal(value: str) -> str:
    return " ".join(value.lower().split())


def canonical_phrase(value: str) -> str:
    """Normalize ordinary punctuation variants while keeping word boundaries stable."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def signal_specificity(signal: str) -> int:
    phrase = canonical_phrase(signal)
    return len(phrase.split()) if phrase else 0


def signal_matches(text: str, signal: str) -> bool:
    """Match curated signals as normalized phrases, not arbitrary token bags.

    Hyphen/slash/underscore differences are treated as separators so natural
    challenge wording can match index phrases. Punctuation-only single-token
    signals such as ws:// or core:: retain literal matching semantics to avoid
    collapsing them into overly generic words.
    """
    canonical_signal = canonical_phrase(signal)
    tokens = canonical_signal.split()

    if len(tokens) == 1 and re.search(r"[^a-z0-9\\s]", signal, re.IGNORECASE):
        return normalize_signal(signal) in normalize_signal(text)

    if not canonical_signal:
        return False

    canonical_text = canonical_phrase(text)
    return f" {canonical_signal} " in f" {canonical_text} "


def select_route(text: str, routes: list[dict]) -> dict:
    """Return a deterministic fast-route decision for regression testing.

    Specificity ordering follows the routing contract:
      1. longest matched signal in words;
      2. total specificity across all matched signals for that route;
      3. number of matched signals.

    Equal top scores are deliberately ambiguous and must fall back to the
    category router rather than being resolved by route order.
    """
    ranked: list[dict] = []

    for route in routes:
        hits = [signal for signal in route["signals"] if signal_matches(text, signal)]
        if not hits:
            continue

        specificities = [signal_specificity(signal) for signal in hits]
        score = (
            max(specificities),
            sum(specificities),
            len(hits),
        )
        ranked.append(
            {
                "id": route["id"],
                "score": score,
                "hits": hits,
            }
        )

    if not ranked:
        return {"state": "fallback", "routes": []}

    best_score = max(item["score"] for item in ranked)
    top = [item for item in ranked if item["score"] == best_score]

    if len(top) != 1:
        return {"state": "ambiguous", "routes": top, "score": best_score}

    return {"state": "match", "routes": top, "score": best_score}


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
    pair_to_route: dict[tuple[str, str | None], str] = {}

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

        pair = (primary, reference)
        indexed_pairs.add(pair)
        previous_route = pair_to_route.get(pair)
        if previous_route is not None and previous_route != route_id:
            fail(
                f"canonical pair {primary} -> {reference} is mapped by both "
                f"{previous_route} and {route_id}; semantic regression cannot infer one route"
            )
            errors += 1
        else:
            pair_to_route[pair] = route_id

    try:
        cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse routing_cases.json: {exc}")
        return 1

    missing_coverage = 0
    semantic_passes = 0

    for case in cases:
        label = case.get("case")
        primary = case.get("primary_skill")
        refs = case.get("references", [])
        reference = refs[0] if refs else None
        pair = (primary, reference)

        if pair not in indexed_pairs:
            fail(
                "routing index lacks representative coverage for "
                f"{label!r}: {primary} -> {reference}"
            )
            errors += 1
            missing_coverage += 1
            continue

        expected_route = pair_to_route.get(pair)
        if not expected_route or not isinstance(label, str):
            continue

        decision = select_route(label, routes)
        state = decision["state"]
        route_ids = [item["id"] for item in decision["routes"]]

        if state == "fallback":
            fail(
                f"representative case {label!r} does not match any routing signal; "
                f"expected {expected_route}"
            )
            errors += 1
        elif state == "ambiguous":
            fail(
                f"representative case {label!r} is ambiguous across {route_ids}; "
                f"expected unique route {expected_route}"
            )
            errors += 1
        elif route_ids[0] != expected_route:
            fail(
                f"representative case {label!r} selects {route_ids[0]} "
                f"instead of expected {expected_route}; hits={decision['routes'][0]['hits']}"
            )
            errors += 1
        else:
            semantic_passes += 1

    try:
        edge_cases = json.loads(EDGE_CASES_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot parse routing_edge_cases.json: {exc}")
        return 1

    edge_passes = 0
    for pos, case in enumerate(edge_cases, start=1):
        label = case.get("case")
        expected_state = case.get("expected_state")

        if not isinstance(label, str) or not label.strip():
            fail(f"routing edge case #{pos} has invalid case text")
            errors += 1
            continue
        if expected_state not in {"match", "ambiguous", "fallback"}:
            fail(f"{label!r}: invalid expected_state {expected_state!r}")
            errors += 1
            continue

        decision = select_route(label, routes)
        actual_state = decision["state"]
        actual_routes = [item["id"] for item in decision["routes"]]

        if actual_state != expected_state:
            fail(
                f"edge case {label!r}: expected state {expected_state}, "
                f"got {actual_state} with routes {actual_routes}"
            )
            errors += 1
            continue

        if expected_state == "match":
            expected_route = case.get("expected_route")
            if expected_route not in seen_ids:
                fail(f"{label!r}: expected_route is missing from routing index: {expected_route!r}")
                errors += 1
                continue
            if actual_routes != [expected_route]:
                fail(
                    f"edge case {label!r}: expected route {expected_route}, "
                    f"got {actual_routes}"
                )
                errors += 1
                continue

        if expected_state == "ambiguous":
            expected_routes = case.get("expected_routes")
            if not isinstance(expected_routes, list) or not expected_routes:
                fail(f"{label!r}: ambiguous case requires expected_routes")
                errors += 1
                continue
            if set(actual_routes) != set(expected_routes):
                fail(
                    f"edge case {label!r}: expected ambiguity {sorted(expected_routes)}, "
                    f"got {sorted(actual_routes)}"
                )
                errors += 1
                continue

        edge_passes += 1

    print(f"Routing index routes: {len(routes)}")
    print(f"Unique signals: {len(seen_signals)}")
    print(f"Representative pairs covered: {len(cases) - missing_coverage}/{len(cases)}")
    print(f"Representative semantic routes: {semantic_passes}/{len(cases)}")
    print(f"Routing edge regressions: {edge_passes}/{len(edge_cases)}")
    print(f"Errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
