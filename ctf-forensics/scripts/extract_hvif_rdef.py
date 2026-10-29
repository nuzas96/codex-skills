#!/usr/bin/env python3
"""Extract a binary Haiku Vector Icon from a Rez resource definition."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path


MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_ICON_BYTES = 16 * 1024 * 1024
RESOURCE_HEADER = re.compile(
    r"(?im)^\s*resource\s*\(\s*(\d+)\s*,\s*['\"]VECTOR:ICON['\"]\s*\)[^{\n]*\{"
)
HEX_LITERAL = re.compile(r'\$"([^"\\]*)"')


class ExtractionError(ValueError):
    pass


def _resource_end(text: str, open_brace: int) -> int:
    depth = 0
    quote = False
    escaped = False
    line_comment = False
    block_comment = False
    i = open_brace
    while i < len(text):
        char = text[i]
        next_char = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
        elif block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = False
        elif char == "/" and next_char == "/":
            line_comment = True
            i += 1
        elif char == "/" and next_char == "*":
            block_comment = True
            i += 1
        elif char == '"':
            quote = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ExtractionError("unterminated VECTOR:ICON resource block")


def extract_hvif(source: bytes, resource_id: int | None = None) -> tuple[int, bytes]:
    if len(source) > MAX_SOURCE_BYTES:
        raise ExtractionError(f"source exceeds {MAX_SOURCE_BYTES} byte safety limit")
    try:
        text = source.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ExtractionError("Rez source is not ASCII text") from exc

    resources: list[tuple[int, str]] = []
    for header in RESOURCE_HEADER.finditer(text):
        found_id = int(header.group(1))
        if resource_id is not None and found_id != resource_id:
            continue
        open_brace = text.find("{", header.start(), header.end())
        end = _resource_end(text, open_brace)
        resources.append((found_id, text[open_brace + 1 : end]))

    if not resources:
        suffix = f" with id {resource_id}" if resource_id is not None else ""
        raise ExtractionError(f"no VECTOR:ICON resource{suffix} found")
    if len(resources) != 1:
        raise ExtractionError("multiple VECTOR:ICON resources found; select one with --resource-id")

    found_id, body = resources[0]
    pieces = HEX_LITERAL.findall(body)
    if not pieces:
        raise ExtractionError("VECTOR:ICON contains no Rez hexadecimal string literals")
    compact: list[str] = []
    for piece in pieces:
        digits = re.sub(r"\s+", "", piece)
        if not digits or not re.fullmatch(r"[0-9A-Fa-f]+", digits):
            raise ExtractionError("VECTOR:ICON contains a malformed hexadecimal string literal")
        if len(digits) % 2:
            raise ExtractionError("VECTOR:ICON hexadecimal string has an odd number of digits")
        compact.append(digits)
        if sum(map(len, compact)) // 2 > MAX_ICON_BYTES:
            raise ExtractionError(f"icon exceeds {MAX_ICON_BYTES} byte safety limit")

    icon = bytes.fromhex("".join(compact))
    if len(icon) < 4 or icon[:4] != b"ncif":
        raise ExtractionError("extracted data does not begin with the HVIF ncif signature")
    return found_id, icon


def write_atomically(destination: Path, data: bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="ASCII Rez source containing a VECTOR:ICON resource")
    parser.add_argument("output", type=Path, help="path for the extracted binary HVIF data")
    parser.add_argument("--resource-id", type=int, help="select a resource id when the source contains several icons")
    args = parser.parse_args(argv)
    try:
        source = args.input.read_bytes()
        resource_id, icon = extract_hvif(source, args.resource_id)
        write_atomically(args.output, icon)
    except (OSError, ExtractionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"extracted VECTOR:ICON id={resource_id} bytes={len(icon)} signature=ncif output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
