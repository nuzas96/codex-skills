# Native Binary Reverse Engineering with Ghidra

Use when a native ELF/PE/Mach-O/firmware executable must be understood at assembly/decompiler level and the main task is program semantics rather than exploitation.

## First Pass

1. Confirm format, architecture, endianness and load/base assumptions.
2. Run auto-analysis, then verify entry point/imports/strings before trusting decompilation.
3. Find the smallest flag-relevant function through strings, imports, xrefs, call tree or input/output behavior.
4. Rename/retype only along that path.
5. Cross-check key operations in assembly when decompiler types/control flow look suspicious.

## Navigation Strategy

High-value anchors:

- input/read/parse functions;
- compare/success/failure strings;
- crypto/checksum constants;
- file/network/environment APIs;
- switch/jump tables and VM dispatch loops;
- JNI/native exports or managed/native boundaries.

Use xrefs aggressively. Large functions are clues, not automatically core logic.

## Improve Decompiler Quality

Correct function signatures, parameter/return types, structure fields and calling conventions. Type propagation often turns opaque pseudo-C into readable logic. Rename variables/functions after evidence, not guesses.

## Algorithms / Constants

Crypto constants can identify candidate primitives but must be validated by control/data flow. An AES S-box, CRC table or Base64 alphabet inside a large statically-linked program may be unrelated to the flag path.

## Headless / Scripts

Use headless Ghidra or scripts when you need repeatable extraction across many functions/binaries: strings/xrefs, decompilation exports, function hashes or call relationships. Automation should narrow analysis, not dump every function into context.

## Packed / Self-Modifying Targets

If entry point is an unpacker stub or executable memory is produced at runtime, unpack/dump/patch first, then re-import the stable stage. Route anti-analysis/emulation specifics to existing reverse references.

## Malware Context

Ghidra mechanics stay here. Once a malicious routine is understood, C2/config/staging interpretation belongs to `ctf-malware`.

## Pwn Boundary

If reversing has already identified a memory-corruption primitive and the remaining problem is control-flow/data exploitation, pivot to `ctf-pwn`; do not keep extending the reverse skill into exploit development.

## Common Failure Modes

- Treating decompiled pseudo-C as source truth.
- Renaming the entire binary before finding the flag path.
- Copying base addresses/offsets from another build.
- Identifying crypto from constants without tracing usage.
- Missing packed/runtime-generated code.
- Using generic malware analysis content when the task is simply native program logic.

## Provenance

Consolidated from the original Apache-2.0 `reverse-engineering-malware-with-ghidra` skill and existing `ctf-reverse` Ghidra/tooling notes. Original source remains on `archive/pre-restructure-20260823`.
