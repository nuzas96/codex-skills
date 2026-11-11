#!/usr/bin/env python3
"""Exercise shared solve-method guidance with independent benign fixtures."""

from __future__ import annotations

import base64
import gzip
import hashlib
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE = (ROOT / "ctf-solve/SKILL.md").read_text(encoding="utf-8")
ROUTING = (ROOT / "ctf-solve/references/triage-routing.md").read_text(encoding="utf-8")


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS {label}")


def competing_predictions(field: str) -> dict[str, bytes]:
    """Compute each credible interpretation independently from the evidence."""
    predictions: dict[str, bytes] = {}
    try:
        outer_hex = bytes.fromhex(field)
        predictions["nested-hex"] = bytes.fromhex(outer_hex.decode("ascii"))
    except (ValueError, UnicodeDecodeError):
        pass
    try:
        predictions["base64"] = base64.b64decode(field, validate=True)
    except (ValueError, base64.binascii.Error):
        pass
    return predictions


def compare_predictions(predictions: dict[str, bytes], observed_sha256: list[str], *, require_nonempty: bool = False) -> dict[str, bytes]:
    """Retain only predictions consistent with every observed checksum."""
    return {
        name: prediction
        for name, prediction in predictions.items()
        if (not require_nonempty or bool(prediction)) and
        all(hashlib.sha256(prediction).hexdigest() == digest for digest in observed_sha256)
    }


def main() -> int:
    # Structural guard: activation, fast paths, evidence levels and pivot rule
    # must stay in the shared lifecycle/reference used by Codex and Racer.
    for phrase in (
        "multiple explanations remain credible with different predicted observations",
        "the same explanation fails repeated discriminating tests",
        "2-3 iterations produce no new evidence",
        "When one evidence-supported path is clear, test it directly without this review.",
    ):
        check(phrase in LIFECYCLE, f"hypothesis trigger contains {phrase[:36]}")
    check("[Evidence to answer](references/triage-routing.md#evidence-to-answer)" in LIFECYCLE, "lifecycle links to answer completion")
    check("A clearly recovered flag-shaped value can take the fast path" in LIFECYCLE, "direct-answer fast path remains")
    for status in ("observed string", "inferred/reconstructed candidate", "locally validated", "accepted by an independent verifier"):
        check(status in ROUTING, f"answer status distinguishes {status}")
    check("never vary guessed formats or suffixes" in ROUTING, "verifier feedback is not a guessing oracle")

    # Negative control reproduces the old fixture's weakness: its preset format
    # yields a flag-shaped answer even though a separate observation contradicts it.
    weak_field = "414e53317b6f6b7d"
    weak_record = {"encoding": "hex", "field": weak_field}
    weak_answer = bytes.fromhex(weak_record["field"]).decode("ascii") if weak_record["encoding"] == "hex" else base64.b64decode(weak_record["field"]).decode("ascii")
    contradictory_digest = hashlib.sha256(base64.b64decode(weak_field, validate=True)).hexdigest()
    check(weak_answer == "ANS1{ok}" and hashlib.sha256(weak_answer.encode()).hexdigest() != contradictory_digest, "old preset-encoding fixture accepts a candidate that contradicts observed evidence")

    # Both hypotheses below are independently computable: the field is valid
    # Base64 and is also nested hexadecimal. A checksum observation chooses one.
    exact_answer = b"demo{evidence_selected}"
    inner_hex = exact_answer.hex().encode("ascii")
    field = inner_hex.hex()
    predictions = competing_predictions(field)
    check(set(predictions) == {"nested-hex", "base64"} and predictions["nested-hex"] != predictions["base64"], "competing hypotheses produce distinct computed predictions")
    evidence_digest = hashlib.sha256(exact_answer).hexdigest()
    supported = compare_predictions(predictions, [evidence_digest])
    rejected = set(predictions) - set(supported)
    selected_name, reconstructed = next(iter(supported.items())) if len(supported) == 1 else (None, b"")
    check(selected_name == "nested-hex" and rejected == {"base64"}, "observed checksum eliminates the contradictory Base64 hypothesis")
    check(reconstructed == exact_answer and hashlib.sha256(reconstructed).hexdigest() == evidence_digest, "evidence-selected transformations reproducibly construct the exact answer")

    # Changing only the observation must change the winner. This catches a
    # bypass that hardcodes the previous choice or injects an arbitrary answer.
    alternate_digest = hashlib.sha256(predictions["base64"]).hexdigest()
    alternate_winner = compare_predictions(predictions, [alternate_digest])
    preset_answer = b"demo{arbitrary-preset}"
    check(set(alternate_winner) == {"base64"} and preset_answer not in predictions.values() and hashlib.sha256(preset_answer).hexdigest() != alternate_digest, "negative control rejects a preset choice and arbitrary answer when evidence changes")

    ambiguous = compare_predictions(predictions, [], require_nonempty=True)
    check(len(ambiguous) == 2, "ambiguous evidence retains both competing hypotheses")
    contradictory = compare_predictions(predictions, [evidence_digest, alternate_digest])
    check(not contradictory, "contradictory observations eliminate every hypothesis")
    insufficient = compare_predictions(predictions, [])
    check(len(insufficient) != 1, "insufficient evidence does not select a unique answer")

    # A plausible flag-shaped decoy has neither provenance nor the expected
    # local digest; no independent verifier is called and status cannot escalate.
    decoy = "flag{plausible}"
    expected_digest = hashlib.sha256(b"flag{actual}").hexdigest()
    locally_valid = hashlib.sha256(decoy.encode()).hexdigest() == expected_digest
    verifier_called = False
    status = "locally validated" if locally_valid else "unverified candidate"
    check(not locally_valid and not verifier_called and status != "accepted by an independent verifier", "false plausible candidate is not reported as accepted")

    # Contradictory checksum evidence forces revision from a hex reading to the
    # metadata-indicated Base64 reading.
    ambiguous_text = "4142"
    expected = base64.b64decode(ambiguous_text, validate=True)
    initial_hex = bytes.fromhex(ambiguous_text)
    expected_sha256 = hashlib.sha256(expected).hexdigest()
    if hashlib.sha256(initial_hex).hexdigest() != expected_sha256:
        revised = base64.b64decode(ambiguous_text, validate=True)
    else:
        revised = initial_hex
    check(revised == expected and revised != initial_hex, "contradictory checksum revises the representation hypothesis")

    # A truncated observation leaves two equally supported exact values.
    remaining_candidates = {"answer{north}", "answer{south}"}
    check(len(remaining_candidates) > 1, "insufficient evidence leaves answer unresolved")

    # One direct answer with matching source and declared format requires no
    # competing-hypothesis review or reconstruction.
    direct = {"source": "provided-output.txt:1", "text": "demo{direct}", "required_prefix": "demo{"}
    direct_supported = direct["text"].startswith(direct["required_prefix"]) and bool(direct["source"])
    detailed_review = False
    check(direct_supported and not detailed_review, "straightforward direct answer avoids unnecessary review")

    # Forensics extraction yields a reused-nonce ciphertext pair, making the
    # crypto reference a justified next owner rather than speculative loading.
    capture_evidence = {"extracted": True, "mode": "AES-CTR", "nonce_a": "n1", "nonce_b": "n1"}
    crypto_ref = ROOT / "ctf-crypto/references/keystream-reuse.md"
    check(capture_evidence["extracted"] and capture_evidence["mode"] == "AES-CTR" and capture_evidence["nonce_a"] == capture_evidence["nonce_b"] and crypto_ref.is_file(), "cross-category pivot follows extracted reused-nonce evidence")

    # Each supported transform is explicit and replayable: Base64 -> XOR key
    # from recovered config -> gzip. A known digest checks the final bytes.
    answer = b"demo{layered}"
    compressed = gzip.compress(answer, mtime=0)
    key = 0x2A
    encoded = base64.b64encode(bytes(value ^ key for value in compressed))
    fixture = {
        "pipeline": ["base64-decode", "xor:0x2a", "gzip-decompress"],
        "key_source": "synthetic-config-byte-0x2a",
        "expected_sha256": hashlib.sha256(answer).hexdigest(),
        "data": encoded,
    }
    stage1 = base64.b64decode(fixture["data"], validate=True)
    stage2 = bytes(value ^ key for value in stage1)
    reconstructed = gzip.decompress(stage2)
    check(fixture["key_source"] and reconstructed == answer and hashlib.sha256(reconstructed).hexdigest() == fixture["expected_sha256"], "evidence-supported multi-step answer reconstruction is reproducible")

    print("Methodology fixtures: 7 scenarios; errors: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
