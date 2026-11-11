#!/usr/bin/env python3
"""Validate Skills V2 intake pools and synthetic isolation regressions."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "ctf-skill-upgrade/research-intake"
SCHEMA_PATH = INTAKE / "intake.schema.json"
POOL_FILES = {
    "DEVELOPMENT": INTAKE / "development.jsonl",
    "REGRESSION": INTAKE / "regression.jsonl",
    "HELD-OUT": INTAKE / "held-out.jsonl",
}
EXPECTED_EXPOSURE = {
    "DEVELOPMENT": "public-solution-studied",
    "REGRESSION": "previously-exposed",
    "HELD-OUT": "untouched",
}
ANSWER_TEXT = re.compile(r"\b[A-Za-z0-9_-]{2,32}\{[^{}\r\n]{1,160}\}")
ANSWER_KEYS = {"answer", "flag", "secret", "credential", "candidate", "solution", "writeup_content"}
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, (float,)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def schema_errors(value: object, schema: dict, path: str = "$") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if json_type(value) not in allowed:
            return [f"{path}: expected {'/'.join(allowed)}, got {json_type(value)}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value is not in the allowed set")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: string is empty or too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: string does not match required pattern")
    if isinstance(value, int) and not isinstance(value, bool):
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            errors.append(f"{path}: integer is outside the allowed range")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in sorted(value.keys() - properties.keys()):
                errors.append(f"{path}: unexpected field {key!r}")
        for key, item in value.items():
            if key in properties:
                errors.extend(schema_errors(item, properties[key], f"{path}.{key}"))
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(schema_errors(item, schema["items"], f"{path}[{index}]"))
    return errors


def walk_strings(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(key)
            yield from walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)
    elif isinstance(value, str):
        yield value


def canonical_source(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), parsed.query, ""))
    return value.strip().rstrip("/").lower()


def validate_pools(records_by_pool: dict[str, list[dict]], schema: dict, routes: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    seen_ids: dict[str, str] = {}
    seen_sources: dict[str, str] = {}
    seen_hashes: dict[str, str] = {}
    for pool, records in records_by_pool.items():
        for index, record in enumerate(records, start=1):
            label = f"{pool} record {index}"
            errors.extend(f"{label}: {error}" for error in schema_errors(record, schema))
            if not isinstance(record, dict):
                continue
            record_pool = record.get("pool")
            if record_pool != pool:
                errors.append(f"{label}: pool field does not match its separate registry")
            exposure = record.get("exposure")
            if isinstance(exposure, dict):
                if exposure.get("status") != EXPECTED_EXPOSURE.get(pool):
                    errors.append(f"{label}: exposure status is invalid for {pool}")
                if pool == "HELD-OUT" and exposure.get("pool_integrity") != "none-known":
                    errors.append(f"{label}: HELD-OUT requires no known contamination")
            if pool == "DEVELOPMENT" and record.get("priority") is None:
                errors.append(f"{label}: DEVELOPMENT candidates require priority scores")
            source = record.get("source")
            pin = record.get("pin")
            if isinstance(source, dict):
                writeups = source.get("writeup_urls", [])
                if pool == "DEVELOPMENT" and not writeups:
                    errors.append(f"{label}: DEVELOPMENT requires a public writeup source")
                if pool == "HELD-OUT" and writeups:
                    errors.append(f"{label}: HELD-OUT must not contain writeup sources")
                locator = source.get("challenge_url")
                if isinstance(locator, str):
                    key = canonical_source(locator)
                    if key in seen_sources:
                        errors.append(f"{label}: duplicate challenge source already recorded in {seen_sources[key]}")
                    else:
                        seen_sources[key] = label
            if isinstance(pin, dict):
                if not pin.get("source_revision") and not pin.get("artifact_sha256"):
                    errors.append(f"{label}: pin a source revision or at least one artifact SHA-256")
                artifact_hashes = pin.get("artifact_sha256")
                for digest in artifact_hashes if isinstance(artifact_hashes, list) else []:
                    if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
                        continue
                    if digest in seen_hashes:
                        errors.append(f"{label}: duplicate artifact hash already recorded in {seen_hashes[digest]}")
                    else:
                        seen_hashes[digest] = label
            challenge_id = record.get("challenge_id")
            if isinstance(challenge_id, str):
                key = challenge_id.lower()
                if key in seen_ids:
                    errors.append(f"{label}: duplicate challenge id already recorded in {seen_ids[key]}")
                else:
                    seen_ids[key] = label
            existing_routes = record.get("existing_routes")
            for route in existing_routes if isinstance(existing_routes, list) else []:
                if not isinstance(route, dict):
                    continue
                route_id = route.get("route_id")
                if not isinstance(route_id, str):
                    continue
                current = routes.get(route_id)
                if current is None:
                    errors.append(f"{label}: unknown Skills V2 route {route_id!r}")
                elif route.get("primary_skill") != current.get("primary_skill") or route.get("reference") != current.get("reference"):
                    errors.append(f"{label}: route target disagrees with ROUTING_INDEX.json for {route_id!r}")
            if pool == "HELD-OUT":
                methodology = record.get("methodology", {})
                forbidden_assessments = (
                    bool(record.get("technique_families")) or bool(record.get("existing_routes")) or
                    bool(record.get("validation_evidence")) or
                    (isinstance(methodology, dict) and any(methodology.get(key) is not None for key in ("missing", "reusable"))) or
                    record.get("priority") is not None
                )
                if forbidden_assessments:
                    errors.append(f"{label}: HELD-OUT cannot contain solution-derived assessments")
            for key_or_text in walk_strings(record):
                if key_or_text.lower() in ANSWER_KEYS:
                    errors.append(f"{label}: answer-bearing field name is forbidden")
                    break
                if ANSWER_TEXT.search(key_or_text):
                    errors.append(f"{label}: answer-like text is forbidden in intake records")
                    break
    return errors


def synthetic_record(pool: str = "DEVELOPMENT") -> dict:
    return {
        "schema_version": 1,
        "pool": pool,
        "challenge_id": "synthetic-crypto-001",
        "challenge_name": "Synthetic Reused Stream",
        "category": "crypto",
        "source": {"challenge_url": "https://example.invalid/challenge/synthetic-crypto-001", "writeup_urls": ["https://example.invalid/writeup/1"]},
        "pin": {"source_revision": "fixture-rev-1", "artifact_sha256": ["a" * 64]},
        "difficulty": {"rating": "medium", "evidence": "synthetic fixture label"},
        "technique_families": ["reused stream keystream recovery"],
        "exposure": {"status": EXPECTED_EXPOSURE[pool], "pool_integrity": "none-known", "evidence": "synthetic fixture only"},
        "existing_routes": [{"route_id": "crypto-keystream-reuse", "primary_skill": "ctf-crypto", "reference": "ctf-crypto/references/keystream-reuse.md"}],
        "methodology": {"missing": "none in fixture", "reusable": "validate paired plaintext constraints"},
        "validation_evidence": [{"description": "synthetic round-trip check", "command": "python fixture.py", "result": "pass", "reproducible": True}],
        "dependencies": ["Python 3 standard library"],
        "limitations": ["synthetic fixture; no target behavior claim"],
        "provenance": {"attribution": "synthetic", "license": "CC0 fixture", "retrieved_at": "2026-11-09"},
        "priority": {"novelty": 2, "capability_gap": 3, "generalizability": 3, "evidence_quality": 3, "estimated_cost": 1},
    }


def self_test(schema: dict, routes: dict[str, dict]) -> int:
    failures = 0
    cases = 0

    def expect(label: str, records: dict[str, list[dict]], should_pass: bool, expected_error: str | tuple[str, ...] | None = None) -> None:
        nonlocal failures, cases
        cases += 1
        errors = validate_pools(records, schema, routes)
        passed = not errors
        expected_errors = () if expected_error is None else (expected_error,) if isinstance(expected_error, str) else expected_error
        expected_error_found = all(any(fragment in error for error in errors) for fragment in expected_errors)
        if passed != should_pass or not expected_error_found:
            failures += 1
            print(f"FAIL synthetic {label}: {errors}; expected_error={expected_error!r}")
        else:
            print(f"PASS synthetic {label}")

    development = synthetic_record()
    expect("valid DEVELOPMENT record", {"DEVELOPMENT": [development], "REGRESSION": [], "HELD-OUT": []}, True)

    identity_duplicate = synthetic_record("REGRESSION")
    identity_duplicate["exposure"]["status"] = "previously-exposed"
    identity_duplicate["source"]["challenge_url"] += "/alternate-location"
    identity_duplicate["source"]["writeup_urls"] = []
    identity_duplicate["pin"]["artifact_sha256"] = ["b" * 64]
    identity_duplicate["priority"] = None
    expect("cross-pool duplicate identity rejection", {"DEVELOPMENT": [development], "REGRESSION": [identity_duplicate], "HELD-OUT": []}, False, "REGRESSION record 1: duplicate challenge id already recorded in DEVELOPMENT record 1")

    hash_duplicate = synthetic_record("REGRESSION")
    hash_duplicate["challenge_id"] = "synthetic-crypto-002"
    hash_duplicate["source"]["challenge_url"] = "https://example.invalid/challenge/synthetic-crypto-002"
    hash_duplicate["source"]["writeup_urls"] = []
    hash_duplicate["exposure"]["status"] = "previously-exposed"
    hash_duplicate["priority"] = None
    expect("cross-pool duplicate artifact hash rejection", {"DEVELOPMENT": [development], "REGRESSION": [hash_duplicate], "HELD-OUT": []}, False, "REGRESSION record 1: duplicate artifact hash already recorded in DEVELOPMENT record 1")

    incomplete = synthetic_record()
    incomplete["pin"] = {"source_revision": None, "artifact_sha256": []}
    incomplete.pop("difficulty")
    expect("incomplete metadata rejection", {"DEVELOPMENT": [incomplete], "REGRESSION": [], "HELD-OUT": []}, False, "$: missing required field 'difficulty'")

    null_hash = synthetic_record()
    null_hash["pin"]["artifact_sha256"] = None
    expect("null artifact hash rejection without crash", {"DEVELOPMENT": [null_hash], "REGRESSION": [], "HELD-OUT": []}, False, "$.pin.artifact_sha256: expected array, got null")

    malformed_nested = synthetic_record()
    malformed_nested["source"] = []
    malformed_nested["pin"] = "not-an-object"
    malformed_nested["exposure"] = ["untouched"]
    malformed_nested["existing_routes"] = None
    malformed_nested["methodology"] = 42
    expect("malformed nested containers return schema errors", {"DEVELOPMENT": [malformed_nested], "REGRESSION": [], "HELD-OUT": []}, False, (
        "$.source: expected object, got array", "$.pin: expected object, got string",
        "$.exposure: expected object, got array", "$.existing_routes: expected array, got null",
        "$.methodology: expected object, got integer",
    ))

    malformed_items = synthetic_record()
    malformed_items["pin"]["artifact_sha256"] = [{"digest": "x"}, "not-a-sha256"]
    malformed_items["existing_routes"] = [{"route_id": ["unhashable"], "primary_skill": "ctf-crypto", "reference": None}]
    expect("invalid hashes and route identifiers return errors without crash", {"DEVELOPMENT": [malformed_items], "REGRESSION": [], "HELD-OUT": []}, False, (
        "$.pin.artifact_sha256[0]: expected string, got object",
        "$.pin.artifact_sha256[1]: string does not match required pattern",
        "$.existing_routes[0].route_id: expected string, got array",
    ))

    contaminated = synthetic_record("HELD-OUT")
    contaminated["source"]["writeup_urls"] = ["https://example.invalid/leaked-writeup"]
    expect("HELD-OUT writeup/assessment contamination rejection", {"DEVELOPMENT": [], "REGRESSION": [], "HELD-OUT": [contaminated]}, False, "HELD-OUT record 1: HELD-OUT must not contain writeup sources")

    malformed_held_out = synthetic_record("HELD-OUT")
    malformed_held_out["methodology"] = []
    malformed_held_out["exposure"]["pool_integrity"] = "suspected-contamination"
    expect("malformed HELD-OUT data cannot bypass contamination checks", {"DEVELOPMENT": [], "REGRESSION": [], "HELD-OUT": [malformed_held_out]}, False, (
        "$.methodology: expected object, got array", "HELD-OUT requires no known contamination",
        "HELD-OUT cannot contain solution-derived assessments",
    ))

    answer_leak = synthetic_record()
    answer_leak["methodology"]["reusable"] = "Recovered flag{synthetic-only}"
    expect("answer-like record content rejection", {"DEVELOPMENT": [answer_leak], "REGRESSION": [], "HELD-OUT": []}, False, "DEVELOPMENT record 1: answer-like text is forbidden in intake records")

    secret_field = synthetic_record()
    secret_field["methodology"]["reusable"] = {"secret": "synthetic-only canary"}
    expect("secret-bearing field rejection", {"DEVELOPMENT": [secret_field], "REGRESSION": [], "HELD-OUT": []}, False, "DEVELOPMENT record 1: answer-bearing field name is forbidden")

    cli_fixture_ok = False
    cli_fixture_message = "DEVELOPMENT record 1: $.pin.artifact_sha256: expected array, got null"
    bad_cli_record = synthetic_record()
    bad_cli_record["pin"]["artifact_sha256"] = None
    try:
        with tempfile.TemporaryDirectory(prefix="skills-intake-cli-") as temporary:
            fixture_root = Path(temporary)
            fixture_scripts = fixture_root / "scripts"
            fixture_intake = fixture_root / "ctf-skill-upgrade" / "research-intake"
            fixture_scripts.mkdir()
            fixture_intake.mkdir(parents=True)
            shutil.copyfile(Path(__file__).resolve(), fixture_scripts / "validate_research_intake.py")
            shutil.copyfile(SCHEMA_PATH, fixture_intake / "intake.schema.json")
            shutil.copyfile(ROOT / "ROUTING_INDEX.json", fixture_root / "ROUTING_INDEX.json")
            (fixture_intake / "development.jsonl").write_text(json.dumps(bad_cli_record) + "\n", encoding="utf-8")
            (fixture_intake / "regression.jsonl").write_text("", encoding="utf-8")
            (fixture_intake / "held-out.jsonl").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(fixture_scripts / "validate_research_intake.py")],
                capture_output=True,
                text=True,
                check=False,
            )
            cli_fixture_ok = result.returncode == 1 and f"ERROR: {cli_fixture_message}" in result.stdout and "Traceback" not in result.stderr
    except OSError:
        cli_fixture_ok = False
    cases += 1
    if cli_fixture_ok:
        print("PASS synthetic malformed CLI record returns a stable error and exit status 1")
    else:
        failures += 1
        print("FAIL synthetic malformed CLI record did not return the expected structured error and exit status 1")

    print(f"Synthetic regressions: {cases}; failures: {failures}")
    return failures


def read_jsonl(file: Path) -> list[dict]:
    records = []
    for line_number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{file}:{line_number}: invalid JSON: {error.msg}") from error
        if not isinstance(value, dict):
            raise ValueError(f"{file}:{line_number}: each line must be a JSON object")
        records.append(value)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="also run benign validator regressions")
    args = parser.parse_args()
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        routes = {route["id"]: route for route in json.loads((ROOT / "ROUTING_INDEX.json").read_text(encoding="utf-8"))["routes"]}
        records = {pool: read_jsonl(file) for pool, file in POOL_FILES.items()}
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: cannot load research intake validation data: {error}")
        print("Intake errors: 1")
        return 1
    errors = validate_pools(records, schema, routes)
    if records["HELD-OUT"]:
        errors.append("tracked held-out.jsonl must remain empty; keep actual evaluation identities outside this repository")
    for error in errors:
        print(f"ERROR: {error}")
    print("Pool records: " + ", ".join(f"{pool}={len(items)}" for pool, items in records.items()))
    print(f"Intake errors: {len(errors)}")
    if args.self_test:
        failures = self_test(schema, routes)
        if failures:
            return 1
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
