#!/usr/bin/env python3
"""
Path-hash filename brute-force template for FUSE/custom filesystem pwn.
Edit coord() and ok() for the challenge.
"""
from __future__ import annotations
import hashlib
import itertools
import string

ALPHABET = string.ascii_letters + string.digits + '_-'
PREFIX = b'/fixed/parent/'
MIN_LEN = 1
MAX_LEN = 8


def coord(path: bytes) -> int:
    h = hashlib.sha256(path).digest()
    # TODO: replace with challenge-specific byte order/bit slicing.
    return int.from_bytes(h[:2], 'little')


def ok(c: int) -> bool:
    # TODO: replace with target condition.
    return (c & 0xfff0) == 0x1000


def main() -> None:
    for n in range(MIN_LEN, MAX_LEN + 1):
        for tup in itertools.product(ALPHABET, repeat=n):
            name = ''.join(tup).encode()
            path = PREFIX + name
            c = coord(path)
            if ok(c):
                print(name.decode(), hex(c), path.decode(errors='replace'))
                return
    raise SystemExit('no match')


if __name__ == '__main__':
    main()
