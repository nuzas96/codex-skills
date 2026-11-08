#!/usr/bin/env python3
"""Extract a Free File Camouflage AES-CBC payload from an appended JPEG block.

The password file contains the raw UTF-8 password bytes (not a hex string).
Output is created exclusively and the embedded MD5 is checked before writing.
Requires PyCryptodome.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
import sys
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


MAX_INPUT_BYTES = 128 * 1024 * 1024
MAX_RECORDS = 1024
SENTINEL = b"\xff\xd9\xff\xd9"
METADATA = re.compile(rb"^#ffc\.(v[12])##ffc\.md5:([A-Za-z0-9+/]{22}==)##ffc\.file:([^/\\\x00]+)#$")


class FFCError(ValueError):
    """Malformed container, wrong password, or failed integrity validation."""


def _key_iv(password: bytes) -> tuple[bytes, bytes]:
    if not password or len(password) > 32:
        raise FFCError("password bytes must have a length from 1 through 32")
    return (password + b"=" * 32)[:32], (password + b"=" * 16)[:16]


def _decrypt_record(record: bytes, key: bytes, iv: bytes) -> bytes:
    try:
        ciphertext = base64.b64decode(record, validate=True)
    except Exception as exc:
        raise FFCError("record is not strict Base64") from exc
    if not ciphertext or len(ciphertext) % AES.block_size:
        raise FFCError("AES-CBC record has invalid ciphertext length")
    try:
        return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext), AES.block_size)
    except ValueError as exc:
        raise FFCError("record decryption or PKCS#7 padding validation failed") from exc


def extract_container(container: bytes, password: bytes) -> tuple[bytes, str]:
    if len(container) > MAX_INPUT_BYTES:
        raise FFCError(f"input exceeds {MAX_INPUT_BYTES} byte safety limit")
    marker_at = container.find(SENTINEL)
    if marker_at < 0:
        raise FFCError("duplicate JPEG EOI sentinel not found")
    encoded_tail = container[marker_at + len(SENTINEL) :]
    if not encoded_tail.endswith(b"\r\n"):
        raise FFCError("FFC records must end with CRLF")
    records = encoded_tail[:-2].split(b"\r\n")
    if not records or len(records) > MAX_RECORDS or any(not r for r in records):
        raise FFCError("empty or excessive FFC record list")

    key, iv = _key_iv(password)
    metadata = _decrypt_record(records[0], key, iv)
    match = METADATA.fullmatch(metadata)
    if not match:
        raise FFCError("decrypted first record is not supported FFC v1/v2 metadata")
    expected_md5 = base64.b64decode(match.group(2), validate=True)
    if len(expected_md5) != 16:
        raise FFCError("metadata MD5 field has invalid length")

    payload = b"".join(_decrypt_record(r, key, iv) for r in records[1:])
    if not payload:
        raise FFCError("container has no payload records")
    if hashlib.md5(payload).digest() != expected_md5:
        raise FFCError("decrypted payload MD5 does not match container metadata")
    filename = match.group(3).decode("utf-8", errors="strict")
    return payload, filename


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="JPEG carrier with FFC trailer")
    parser.add_argument("output", type=Path, help="new output file (must not already exist)")
    parser.add_argument("--password-file", type=Path, required=True, help="file containing raw password bytes")
    args = parser.parse_args(argv)
    try:
        raw = args.image.read_bytes()
        password = args.password_file.read_bytes()
        payload, _filename = extract_container(raw, password)
        with args.output.open("xb") as dst:
            dst.write(payload)
    except (OSError, FFCError, UnicodeError) as exc:
        print(f"ffc_extract: {exc}", file=sys.stderr)
        return 2
    print(f"extracted {len(payload)} bytes; embedded MD5 verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
