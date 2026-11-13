#!/usr/bin/env python3
"""Benign structural and transformation checks for cross-layer web guidance."""

from __future__ import annotations

import glob
import hashlib
import hmac
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "ctf-web/references/cross-layer-request-to-file.md"
WEB_ROUTER = ROOT / "ctf-web/SKILL.md"
CHAIN_ROUTER = ROOT / "ctf-solve/references/modern-chains.md"
STUCK = ROOT / "ctf-solve/references/stuck-recovery.md"


def chain_reaches_target(edges: list[tuple[str, str, str]], start: str, target: str) -> bool:
    """Only confirmed edges can establish a synthetic end-to-end capability."""
    reached = {start}
    changed = True
    while changed:
        changed = False
        for source, destination, status in edges:
            if status == "confirmed" and source in reached and destination not in reached:
                reached.add(destination)
                changed = True
    return target in reached


class CrossLayerWebGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = REFERENCE.read_text(encoding="utf-8")

    def test_guidance_routes_and_covers_layer_boundaries(self) -> None:
        self.assertIn("references/cross-layer-request-to-file.md", WEB_ROUTER.read_text())
        self.assertIn("cross-layer-request-to-file.md", CHAIN_ROUTER.read_text())
        self.assertIn("cross-layer-request-to-file.md", STUCK.read_text())
        for term in (
            "absolute-form",
            "PATH_INFO",
            "parse_url",
            "decode count",
            "signature layer",
            "SQL mode",
            "value vs identifier vs expression context",
            "MySQL backslash behavior",
            "stream wrapper",
            "path disclosure",
            "synthetic canary",
            "negative controls",
            "PHP-FPM",
        ):
            with self.subTest(term=term):
                self.assertIn(term.lower(), self.reference.lower())
        self.assertNotIn("PAYLOAD=", self.reference)

    def test_synthetic_decode_chain_requires_the_expected_count(self) -> None:
        # Model two generic decoding boundaries; this is not an nginx emulator.
        raw_path = "/v1/item/%252Fsegment"
        after_proxy = unquote(raw_path)
        app_canonical = unquote(after_proxy)
        signer_canonical = unquote(unquote(raw_path))

        self.assertEqual(after_proxy, "/v1/item/%2Fsegment")
        self.assertEqual(app_canonical, "/v1/item//segment")
        self.assertEqual(signer_canonical, app_canonical)
        self.assertNotEqual(unquote(raw_path), app_canonical)

    def test_synthetic_signature_binds_exact_canonical_path(self) -> None:
        secret = b"benign-test-key"
        canonical = "/v1/item/a/b"
        signature = hmac.new(secret, canonical.encode(), hashlib.sha256).hexdigest()

        self.assertTrue(hmac.compare_digest(
            signature,
            hmac.new(secret, canonical.encode(), hashlib.sha256).hexdigest(),
        ))
        changed_path_signature = hmac.new(secret, b"/v1/item/a%2Fb", hashlib.sha256).hexdigest()
        self.assertFalse(hmac.compare_digest(signature, changed_path_signature))
        wrong_secret_signature = hmac.new(b"other-test-key", canonical.encode(), hashlib.sha256).hexdigest()
        self.assertFalse(hmac.compare_digest(signature, wrong_secret_signature))

    def test_synthetic_file_listing_is_not_content_disclosure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cross-layer-guidance-") as temp:
            root = Path(temp)
            (root / "artifact-17.txt").write_text("synthetic contents", encoding="utf-8")
            listed = [Path(item).name for item in glob.glob(str(root / "artifact-*.txt"))]
            self.assertEqual(listed, ["artifact-17.txt"])
            self.assertNotIn("synthetic contents", listed)
            self.assertEqual(glob.glob(str(root / "missing-*.txt")), [])

    def test_synthetic_dependency_chain_and_missing_prerequisites(self) -> None:
        # Separate services: request control -> blind state mutation -> auth -> reflected constructor -> target data.
        complete = [
            ("request", "state-write", "confirmed"),
            ("state-write", "authorized-session", "confirmed"),
            ("authorized-session", "constructor-input", "confirmed"),
            ("constructor-input", "data-read", "confirmed"),
        ]
        self.assertTrue(chain_reaches_target(complete, "request", "data-read"))
        self.assertFalse(chain_reaches_target(complete, "request", "flag-output"))

        missing_state = complete.copy()
        missing_state[0] = ("request", "state-write", "rejected")
        self.assertFalse(chain_reaches_target(missing_state, "request", "data-read"))

        blocked_gadget = complete.copy()
        blocked_gadget[-1] = ("constructor-input", "data-read", "runtime-blocked")
        self.assertFalse(chain_reaches_target(blocked_gadget, "request", "data-read"))

        plausible_only = [("request", "state-write", "plausible")]
        self.assertFalse(chain_reaches_target(plausible_only, "request", "state-write"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
