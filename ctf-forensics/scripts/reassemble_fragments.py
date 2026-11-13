#!/usr/bin/env python3
"""Reassemble explicitly indexed local fragments with optional SHA-256 checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path


DEFAULT_MAX_BYTES = 128 * 1024 * 1024
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


class ReassemblyError(ValueError):
    pass


def _safe_relative(base: Path, raw: object, label: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ReassemblyError(f"{label} must be a non-empty relative path")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ReassemblyError(f"{label} must be relative to the manifest")
    resolved = (base / candidate).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise ReassemblyError(f"{label} escapes the manifest directory") from exc
    return resolved


def _parse_manifest(path: Path) -> tuple[list[tuple[Path, str | None]], str | None]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReassemblyError(f"cannot read JSON manifest: {exc}") from exc
    if not isinstance(obj, dict):
        raise ReassemblyError("manifest root must be an object")
    total = obj.get("total")
    chunks = obj.get("chunks")
    if not isinstance(total, int) or isinstance(total, bool) or total <= 0 or total > 100_000:
        raise ReassemblyError("total must be an integer from 1 to 100000")
    if not isinstance(chunks, list) or len(chunks) != total:
        raise ReassemblyError("chunks must contain exactly total entries")
    if "sha256" in obj and (not isinstance(obj["sha256"], str) or not SHA256_RE.fullmatch(obj["sha256"])):
        raise ReassemblyError("sha256 must be 64 hexadecimal characters")
    entries: dict[int, tuple[Path, str | None]] = {}
    for item in chunks:
        if not isinstance(item, dict):
            raise ReassemblyError("each chunk must be an object")
        index = item.get("index")
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < total:
            raise ReassemblyError("chunk index is outside 0..total-1")
        if index in entries:
            raise ReassemblyError(f"duplicate chunk index {index}")
        digest = item.get("sha256")
        if digest is not None and (not isinstance(digest, str) or not SHA256_RE.fullmatch(digest)):
            raise ReassemblyError(f"chunk {index} sha256 must be 64 hexadecimal characters")
        source = _safe_relative(path.parent, item.get("path"), f"chunk {index} path")
        entries[index] = (source, digest.lower() if digest else None)
    missing = sorted(set(range(total)) - entries.keys())
    if missing:
        raise ReassemblyError(f"missing chunk indexes: {missing}")
    return [entries[i] for i in range(total)], obj.get("sha256", None).lower() if obj.get("sha256") else None


def reassemble(manifest: Path, max_bytes: int) -> tuple[bytes, bool]:
    if max_bytes <= 0:
        raise ReassemblyError("maximum output size must be positive")
    entries, expected_total = _parse_manifest(manifest.resolve())
    output = bytearray()
    for index, (path, expected) in enumerate(entries):
        try:
            size = path.stat().st_size
            if len(output) + size > max_bytes:
                raise ReassemblyError(f"reassembled output exceeds limit ({max_bytes} bytes)")
            chunk = path.read_bytes()
        except OSError as exc:
            raise ReassemblyError(f"cannot read chunk {index}: {exc}") from exc
        digest = hashlib.sha256(chunk).hexdigest()
        if expected and digest != expected:
            raise ReassemblyError(f"chunk {index} SHA-256 mismatch")
        output.extend(chunk)
    assembled = bytes(output)
    digest = hashlib.sha256(assembled).hexdigest()
    if expected_total and digest != expected_total:
        raise ReassemblyError("assembled SHA-256 mismatch")
    validated = expected_total is not None or all(digest for _, digest in entries)
    return assembled, validated


def write_new_file(path: Path, data: bytes) -> None:
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
        raise ReassemblyError(f"output already exists: {path}") from exc
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--max-output-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = parser.parse_args()
    try:
        data, validated = reassemble(args.manifest, args.max_output_bytes)
        write_new_file(args.output, data)
    except (OSError, ReassemblyError) as exc:
        parser.exit(2, f"error: {exc}\n")
    status = "integrity-checked" if validated else "order-reproduced-unverified"
    print(f"bytes={len(data)} sha256={hashlib.sha256(data).hexdigest()} status={status} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
