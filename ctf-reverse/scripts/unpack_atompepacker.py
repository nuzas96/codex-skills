#!/usr/bin/env python3
"""Extract and LZMA-decompress an AtomPePacker .ATOM section.

Uses only the Python standard library. It fails loudly unless the input is a
valid PE, the requested section exists, the LZMA stream reaches EOF, and the
recovered output is another valid PE.
"""

import argparse
import lzma
import struct
import sys
from pathlib import Path


def u16(data: bytes, off: int) -> int:
    return struct.unpack_from("<H", data, off)[0]


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def validate_pe(data: bytes, label: str) -> int:
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ValueError(f"{label}: missing MZ header")
    pe_off = u32(data, 0x3C)
    if pe_off + 4 > len(data) or data[pe_off:pe_off + 4] != b"PE\0\0":
        raise ValueError(f"{label}: invalid PE signature/e_lfanew")
    return pe_off


def sections(data: bytes):
    pe_off = validate_pe(data, "input")
    file_header = pe_off + 4
    number_of_sections = u16(data, file_header + 2)
    size_of_optional_header = u16(data, file_header + 16)
    table = file_header + 20 + size_of_optional_header

    if number_of_sections == 0 or number_of_sections > 96:
        raise ValueError(f"input: suspicious section count {number_of_sections}")

    for i in range(number_of_sections):
        off = table + i * 40
        if off + 40 > len(data):
            raise ValueError("input: truncated PE section table")
        name = data[off:off + 8].split(b"\0", 1)[0].decode("ascii", "replace")
        raw_size = u32(data, off + 16)
        raw_ptr = u32(data, off + 20)
        if raw_ptr + raw_size > len(data):
            raise ValueError(f"input: section {name!r} extends past EOF")
        yield name, raw_ptr, raw_size


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Offline-unpack an AtomPePacker .ATOM LZMA section"
    )
    ap.add_argument("input", type=Path, help="packed PE")
    ap.add_argument("-o", "--output", type=Path, default=Path("unpacked.exe"))
    ap.add_argument("--section", default=".ATOM", help="section name (default: .ATOM)")
    args = ap.parse_args()

    data = args.input.read_bytes()
    match = None
    for name, raw_ptr, raw_size in sections(data):
        if name == args.section:
            match = (raw_ptr, raw_size)
            break

    if match is None:
        raise ValueError(f"input: section {args.section!r} not found")

    raw_ptr, raw_size = match
    packed = data[raw_ptr:raw_ptr + raw_size]
    if len(packed) < 13:
        raise ValueError(".ATOM: too small for an LZMA-alone header")

    dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
    try:
        recovered = dec.decompress(packed)
    except lzma.LZMAError as exc:
        raise ValueError(f".ATOM: LZMA-alone decompression failed: {exc}") from exc

    if not dec.eof:
        raise ValueError(".ATOM: LZMA stream did not reach end-of-stream")

    validate_pe(recovered, "recovered output")
    args.output.write_bytes(recovered)

    trailing = len(dec.unused_data)
    print(f"[+] section={args.section} raw_offset=0x{raw_ptr:x} raw_size={raw_size}")
    print(f"[+] recovered_size={len(recovered)} trailing_after_lzma={trailing}")
    print(f"[+] valid PE written to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, struct.error) as exc:
        print(f"[-] {exc}", file=sys.stderr)
        raise SystemExit(1)
