#!/usr/bin/env python3
"""Independent benign fixtures and malformed-input checks for ffc_extract."""

from __future__ import annotations

import base64
import hashlib
import io
import random
import unittest

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PIL import Image, ImageDraw

from ffc_extract import FFCError, SENTINEL, extract_container


def jpeg_fixture(seed: int) -> bytes:
    image = Image.new("RGB", (83 + seed, 57 + seed), (225, 235, 245))
    draw = ImageDraw.Draw(image)
    draw.rectangle((5, 8, 30 + seed, 40), fill=(seed * 35 % 255, 40, 90))
    draw.line((0, seed, image.width - 1, image.height - 1), fill=(20, 110, 70), width=2)
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=87)
    return out.getvalue()


def encrypt_record(data: bytes, password: bytes) -> bytes:
    key = (password + b"=" * 32)[:32]
    iv = (password + b"=" * 16)[:16]
    return base64.b64encode(AES.new(key, AES.MODE_CBC, iv).encrypt(pad(data, 16)))


def make_container(image: bytes, name: str, payload: bytes, password: bytes) -> bytes:
    metadata = (
        b"#ffc.v2##ffc.md5:"
        + base64.b64encode(hashlib.md5(payload).digest())
        + b"##ffc.file:"
        + name.encode()
        + b"#"
    )
    records = [encrypt_record(metadata, password)]
    # Match FFC's chunked writer while varying chunk boundaries per fixture.
    rng = random.Random(len(payload))
    offset = 0
    while offset < len(payload):
        size = 2_000_000 + rng.randrange(1000)
        records.append(encrypt_record(payload[offset : offset + size], password))
        offset += size
    prefix = image[:-2] if image.endswith(b"\xff\xd9") else image
    return prefix + SENTINEL + b"\r\n".join(records) + b"\r\n"


class FFCExtractTests(unittest.TestCase):
    def test_two_independent_benign_images_and_payloads(self) -> None:
        cases = [
            (jpeg_fixture(1), b"short benign marker text\x00\xff", b"alpha.txt", b"test-pass-1"),
            (jpeg_fixture(9), bytes(range(256)) * 8193, b"large.bin", b"another-passphrase"),
        ]
        for image, expected, _name, password in cases:
            with self.subTest(payload_length=len(expected)):
                payload, name = extract_container(make_container(image, _name.decode(), expected, password), password)
                self.assertEqual(payload, expected)
                self.assertEqual(name.encode(), _name)

    def test_rejects_missing_sentinel_wrong_password_and_tamper(self) -> None:
        image = jpeg_fixture(3)
        payload = b"known benign expected data"
        password = b"fixture-secret"
        container = make_container(image, "expected.dat", payload, password)
        with self.assertRaises(FFCError):
            extract_container(image, password)
        with self.assertRaises(FFCError):
            extract_container(container, b"wrong-secret")
        damaged = bytearray(container)
        damaged[-8] ^= 1
        with self.assertRaises(FFCError):
            extract_container(bytes(damaged), password)


if __name__ == "__main__":
    unittest.main()
