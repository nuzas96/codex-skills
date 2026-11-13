#!/usr/bin/env python3
"""Apply an explicitly declared, size-bounded byte transformation pipeline."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import os
import re
import tempfile
import zlib
from pathlib import Path


DEFAULT_INPUT_LIMIT = 16 * 1024 * 1024
DEFAULT_OUTPUT_LIMIT = 64 * 1024 * 1024
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


class TransformError(ValueError):
    pass


def _decompress_bounded(data: bytes, wbits: int, limit: int) -> bytes:
    decoder = zlib.decompressobj(wbits)
    output = bytearray()
    offset = 0
    while offset < len(data):
        pending = data[offset : offset + 64 * 1024]
        offset += len(pending)
        while pending:
            room = limit + 1 - len(output)
            if room <= 0:
                raise TransformError(f"decompressed output exceeds limit ({limit} bytes)")
            try:
                piece = decoder.decompress(pending, room)
            except zlib.error as exc:
                raise TransformError(f"invalid compressed stream: {exc}") from exc
            output.extend(piece)
            if len(output) > limit:
                raise TransformError(f"decompressed output exceeds limit ({limit} bytes)")
            pending = decoder.unconsumed_tail
    if not decoder.eof:
        raise TransformError("incomplete compressed stream")
    if decoder.unused_data:
        raise TransformError("trailing bytes after compressed stream")
    try:
        output.extend(decoder.flush(limit + 1 - len(output)))
    except zlib.error as exc:
        raise TransformError(f"invalid compressed stream: {exc}") from exc
    if len(output) > limit:
        raise TransformError(f"decompressed output exceeds limit ({limit} bytes)")
    return bytes(output)


def apply_step(data: bytes, step: str, output_limit: int) -> bytes:
    if step == "base64":
        try:
            result = base64.b64decode(b"".join(data.split()), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise TransformError(f"invalid Base64 input: {exc}") from exc
    elif step == "hex":
        try:
            result = bytes.fromhex(data.decode("ascii"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise TransformError(f"invalid hexadecimal input: {exc}") from exc
    elif step == "reverse":
        result = data[::-1]
    elif step == "bit-reverse":
        table = bytes(int(f"{value:08b}"[::-1], 2) for value in range(256))
        result = data.translate(table)
    elif step.startswith("word-reverse:"):
        raw_size = step.split(":", 1)[1]
        if not raw_size.isdecimal() or int(raw_size) < 2:
            raise TransformError("word-reverse size must be an integer >= 2")
        size = int(raw_size)
        if len(data) % size:
            raise TransformError(f"input length {len(data)} is not divisible by word size {size}")
        result = b"".join(data[i : i + size][::-1] for i in range(0, len(data), size))
    elif step == "gzip":
        result = _decompress_bounded(data, 16 + zlib.MAX_WBITS, output_limit)
    elif step == "zlib":
        result = _decompress_bounded(data, zlib.MAX_WBITS, output_limit)
    else:
        raise TransformError(f"unsupported step: {step}")
    if len(result) > output_limit:
        raise TransformError(f"step output exceeds limit ({output_limit} bytes)")
    return result


def transform(data: bytes, steps: list[str], output_limit: int) -> bytes:
    if not steps:
        raise TransformError("at least one explicit --step is required")
    if output_limit <= 0:
        raise TransformError("output limit must be positive")
    for step in steps:
        data = apply_step(data, step, output_limit)
    return data


def verify_sha256(data: bytes, expected: str | None) -> str:
    digest = hashlib.sha256(data).hexdigest()
    if expected and digest.lower() != expected.lower():
        raise TransformError("final SHA-256 does not match the supplied expected digest")
    return digest


def write_new_file(path: Path, data: bytes) -> None:
    """Atomically create a new file without replacing an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as temp:
            temp_name = temp.name
            temp.write(data)
            temp.flush()
            os.fsync(temp.fileno())
        os.link(temp_name, path)
    except FileExistsError as exc:
        raise TransformError(f"output already exists: {path}") from exc
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--step", action="append", required=True,
                        help="explicit ordered operation: base64, hex, gzip, zlib, reverse, bit-reverse, word-reverse:N")
    parser.add_argument("--expect-sha256", help="optional evidence-provided digest for the final bytes")
    parser.add_argument("--max-input-bytes", type=int, default=DEFAULT_INPUT_LIMIT)
    parser.add_argument("--max-output-bytes", type=int, default=DEFAULT_OUTPUT_LIMIT)
    args = parser.parse_args()

    if args.max_input_bytes <= 0 or args.max_output_bytes <= 0:
        parser.error("size limits must be positive")
    if args.expect_sha256 and not SHA256_RE.fullmatch(args.expect_sha256):
        parser.error("--expect-sha256 must contain exactly 64 hexadecimal characters")
    try:
        size = args.input.stat().st_size
        if size > args.max_input_bytes:
            raise TransformError(f"input exceeds limit ({args.max_input_bytes} bytes)")
        raw = args.input.read_bytes()
        result = transform(raw, args.step, args.max_output_bytes)
        digest = verify_sha256(result, args.expect_sha256)
        write_new_file(args.output, result)
    except (OSError, TransformError) as exc:
        parser.exit(2, f"error: {exc}\n")
    status = "sha256-matched" if args.expect_sha256 else "unverified"
    print(f"bytes={len(result)} sha256={digest} status={status} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
