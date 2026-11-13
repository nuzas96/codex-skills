#!/usr/bin/env python3
"""Synthetic positive and adversarial tests for evidence_transform."""

from __future__ import annotations

import base64
import gzip
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("evidence_transform.py")
SPEC = importlib.util.spec_from_file_location("evidence_transform", SCRIPT)
evidence_transform = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(evidence_transform)


class EvidenceTransformTests(unittest.TestCase):
    def test_explicit_nested_base64_then_gzip_pipeline(self):
        expected = b"SYNTHETIC{supported_transform_chain}"
        encoded = base64.b64encode(gzip.compress(expected, mtime=0))
        result = evidence_transform.transform(encoded, ["base64", "gzip"], 4096)
        self.assertEqual(result, expected)

    def test_hex_and_bit_order_operations_are_exact(self):
        self.assertEqual(evidence_transform.transform(b"96", ["hex", "bit-reverse"], 16), b"i")

    def test_word_byte_order_is_explicit_and_hash_disambiguates(self):
        expected = b"CTF{bytes}"
        serialized = b"".join(expected[i:i + 2][::-1] for i in range(0, len(expected), 2))
        corrected = evidence_transform.transform(serialized, ["word-reverse:2"], 4096)
        self.assertEqual(corrected, expected)
        self.assertNotEqual(hashlib.sha256(serialized).digest(), hashlib.sha256(expected).digest())
        evidence_transform.verify_sha256(corrected, hashlib.sha256(expected).hexdigest())
        with self.assertRaises(evidence_transform.TransformError):
            evidence_transform.verify_sha256(serialized, hashlib.sha256(expected).hexdigest())

    def test_malformed_encoding_and_partial_word_are_rejected(self):
        for data, step in [(b"%%%", "base64"), (b"abc", "hex"), (b"abc", "word-reverse:2")]:
            with self.subTest(step=step), self.assertRaises(evidence_transform.TransformError):
                evidence_transform.transform(data, [step], 1024)

    def test_unjustified_or_unsupported_guess_is_not_attempted(self):
        with self.assertRaisesRegex(evidence_transform.TransformError, "unsupported step"):
            evidence_transform.transform(b"synthetic", ["try-every-encoding"], 1024)

    def test_incomplete_and_over_limit_compression_are_rejected(self):
        compressed = gzip.compress(b"A" * 100_000, mtime=0)
        with self.assertRaisesRegex(evidence_transform.TransformError, "incomplete"):
            evidence_transform.transform(compressed[:-2], ["gzip"], 200_000)
        with self.assertRaisesRegex(evidence_transform.TransformError, "exceeds limit"):
            evidence_transform.transform(compressed, ["gzip"], 1024)

    def test_hash_mismatch_does_not_create_candidate_output(self):
        with tempfile.TemporaryDirectory(prefix="evidence-transform-") as td:
            root = Path(td)
            output = root / "candidate.bin"
            data = evidence_transform.transform(b"U1lOVEhFVElD", ["base64"], 1024)
            with self.assertRaisesRegex(evidence_transform.TransformError, "does not match"):
                evidence_transform.verify_sha256(data, "0" * 64)
                evidence_transform.write_new_file(output, data)
            self.assertFalse(output.exists())

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="evidence-transform-") as td:
            output = Path(td) / "candidate.bin"
            output.write_bytes(b"existing")
            with self.assertRaisesRegex(evidence_transform.TransformError, "already exists"):
                evidence_transform.write_new_file(output, b"replacement")
            self.assertEqual(output.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
