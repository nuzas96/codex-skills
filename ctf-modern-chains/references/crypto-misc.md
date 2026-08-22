# Crypto and Miscellaneous Chains

## Contents

- Huffman-tree ambiguity
- LCG reversal
- RSA fault leakage
- Representation punning
- State-race underflow
- PostgreSQL file-write to preload execution

## Huffman-Tree Ambiguity

Huffman coding is not encryption, but reconstruction can fail when the encoder's tie-breaking rules are unknown.

1. Rebuild the tree from supplied frequencies.
2. Test both left/right bit assignments.
3. Enumerate stable orderings only among equal-frequency nodes.
4. Use a known flag prefix as a scoring constraint, not as plaintext replacement.
5. Prefer bounded enumeration of tie groups over manual character substitution.

Replicate the source language's stable sort and insertion behavior when encoder code or runtime is known.

## LCG Reversal

For `x[n+1] = (a*x[n] + c) mod m`, recover prior state with:

```text
x[n] = a^(-1) * (x[n+1] - c) mod m
```

when `gcd(a, m) = 1`. If the exposed value is a transformed or squared seed, enumerate modular square roots or use factorization/CRT as appropriate, then validate candidates against multiple outputs. Mirror truncation and bit masking exactly.

## RSA Fault Leakage

A faulty CRT-RSA signature can reveal a prime factor. Given a correct/faulty pair or a faulty signature and message relation, test GCD constructions such as:

```text
gcd(s_correct - s_faulty, n)
gcd(s_faulty^e - m, n)
```

A nontrivial GCD yields `p` or `q`; reconstruct the private key and reverse any outer XOR or encoding layer only after RSA decryption is verified.

## Representation Punning

If integers and floats are cast through pointers or unions, distinguish numeric conversion from bit reinterpretation. Reproduce with `struct.pack`/`unpack` using the target width and endianness:

```python
import struct
u = struct.unpack("<I", struct.pack("<f", value))[0]
f = struct.unpack("<f", struct.pack("<I", u))[0]
```

Preserve NaNs, signed zero, and rounding behavior by operating on raw bytes rather than decimal strings.

## State-Race Underflow

For a purchase or game action split into check and commit stages, open two sessions on the same account:

1. Drive both to the confirmation boundary.
2. Commit one action so shared state changes.
3. Commit the stale action.
4. Observe double-spend, unsigned underflow, or duplicate reward behavior.

Synchronize at the server-side check/commit boundary, not merely at UI button presses. Automate parallel requests if the window is narrow.

## PostgreSQL File-Write to Preload Execution

An over-privileged PostgreSQL role may lack `COPY ... PROGRAM` yet retain large-object export and configuration access. Investigate this chain only in an isolated CTF database:

1. Read configuration and enumerate server version, data directory, writable paths, and helper-function privileges.
2. Compile a compatible PostgreSQL shared library with a minimal initialization hook.
3. Upload bytes through large-object functions and export the object to a writable library path.
4. Modify a writable configuration copy to include the library through a preload setting and controlled search path.
5. Reload configuration and trigger a new backend session.
6. Read deterministic output through database file functions.

Version-match server headers and derive all paths from SQL. Keep a copy of the original configuration and avoid using this technique outside an authorized disposable target.

Source basis: reusable abstractions from the DalCTF 2026 organizer writeups, <https://github.com/DalCTF/DalCTF2026>.
