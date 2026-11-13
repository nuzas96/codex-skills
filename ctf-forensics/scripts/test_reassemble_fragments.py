#!/usr/bin/env python3
"""Synthetic positive and adversarial tests for indexed fragment reassembly."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("reassemble_fragments.py")
SPEC = importlib.util.spec_from_file_location("reassemble_fragments", SCRIPT)
reassemble_fragments = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(reassemble_fragments)


class ReassembleFragmentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fragment-reassembly-")
        self.root = Path(self.temp.name)
        self.manifest_counter = 0

    def tearDown(self):
        self.temp.cleanup()

    def _manifest(self, chunks, total, digest=None):
        obj = {"total": total, "chunks": chunks}
        if digest is not None:
            obj["sha256"] = digest
        self.manifest_counter += 1
        path = self.root / f"manifest-{self.manifest_counter}.json"
        path.write_text(json.dumps(obj), encoding="utf-8")
        return path

    def test_reassembles_in_index_order_not_filename_order_and_checks_digest(self):
        (self.root / "z-last").write_bytes(b"answer}")
        (self.root / "a-first").write_bytes(b"SYNTHETIC{")
        expected = b"SYNTHETIC{answer}"
        manifest = self._manifest([
            {"index": 1, "path": "z-last", "sha256": hashlib.sha256(b"answer}").hexdigest()},
            {"index": 0, "path": "a-first", "sha256": hashlib.sha256(b"SYNTHETIC{").hexdigest()},
        ], 2, hashlib.sha256(expected).hexdigest())
        data, validated = reassemble_fragments.reassemble(manifest, 1024)
        self.assertEqual(data, expected)
        self.assertTrue(validated)

    def test_conflicting_order_fails_whole_object_hash_and_writes_nothing(self):
        (self.root / "one").write_bytes(b"A")
        (self.root / "two").write_bytes(b"B")
        manifest = self._manifest([{"index": 0, "path": "one"}, {"index": 1, "path": "two"}], 2,
                                  hashlib.sha256(b"BA").hexdigest())
        with self.assertRaisesRegex(reassemble_fragments.ReassemblyError, "assembled SHA-256 mismatch"):
            reassemble_fragments.reassemble(manifest, 10)

    def test_incomplete_manifest_bad_chunk_hash_and_size_limit_fail(self):
        (self.root / "one").write_bytes(b"1234")
        cases = [
            (self._manifest([{"index": 0, "path": "one"}], 2), "exactly total"),
            (self._manifest([{"index": 0, "path": "one", "sha256": "0" * 64}], 1), "chunk 0 SHA-256 mismatch"),
            (self._manifest([{"index": 0, "path": "one"}], 1), "exceeds limit"),
        ]
        for manifest, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(reassemble_fragments.ReassemblyError, message):
                reassemble_fragments.reassemble(manifest, 3 if message == "exceeds limit" else 1024)

    def test_path_escape_and_duplicate_indexes_are_rejected(self):
        scope = self.root / "manifest-scope"
        scope.mkdir()
        outside = self.root / "outside-canary"
        outside.write_bytes(b"synthetic")
        try:
            manifest = scope / "manifest.json"
            manifest.write_text(json.dumps({"total": 1, "chunks": [{"index": 0, "path": "../outside-canary"}]}))
            with self.assertRaisesRegex(reassemble_fragments.ReassemblyError, "escapes"):
                reassemble_fragments.reassemble(manifest, 1024)
        finally:
            outside.unlink(missing_ok=True)
        manifest = self._manifest([{"index": 0, "path": "one"}, {"index": 0, "path": "one"}], 2)
        with self.assertRaisesRegex(reassemble_fragments.ReassemblyError, "duplicate chunk index"):
            reassemble_fragments.reassemble(manifest, 1024)

    def test_no_hash_is_explicitly_unverified(self):
        (self.root / "one").write_bytes(b"synthetic")
        manifest = self._manifest([{"index": 0, "path": "one"}], 1)
        data, validated = reassemble_fragments.reassemble(manifest, 1024)
        self.assertEqual(data, b"synthetic")
        self.assertFalse(validated)

    def test_malformed_manifest_and_invalid_digest_fail_actionably(self):
        path = self.root / "manifest.json"
        path.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(reassemble_fragments.ReassemblyError, "cannot read JSON"):
            reassemble_fragments.reassemble(path, 1024)
        path.write_text(json.dumps({"total": 1, "chunks": [{"index": 0, "path": "x"}], "sha256": "not-a-hash"}), encoding="utf-8")
        with self.assertRaisesRegex(reassemble_fragments.ReassemblyError, "sha256 must be"):
            reassemble_fragments.reassemble(path, 1024)


if __name__ == "__main__":
    unittest.main()
