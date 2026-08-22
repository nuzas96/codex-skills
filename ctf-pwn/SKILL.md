---
name: ctf-pwn
description: Solve CTF native binary exploitation challenges after a concrete low-level primitive is identified: stack/global overflows, format strings, ROP/ret2libc/SROP, shellcode, heap/tcache/UAF, FSOP, seccomp/sandbox escapes, kernel exploitation, partial overwrites, allocator abuse and related Linux/Windows memory-corruption chains. Use when the main task is converting native process corruption or a kernel primitive into flag access. Use ctf-reverse first when understanding program semantics is still the main blocker.
license: MIT
compatibility: Requires native-analysis tooling appropriate to the target architecture plus Python 3/pwntools for automation when needed.
metadata:
  user-invocable: "false"
---

# CTF Pwn — V2 Router

Use `ctf-solve` for lifecycle/progress behavior. This file only decides which exploitation reference to load.

## First pass

1. Identify architecture, ABI, loader/libc and protections from the **supplied target**.
2. Reproduce the crash/state corruption locally when possible.
3. Measure the primitive precisely: overwrite/read/write width, controlled bytes, lifetime, index, format-string position, syscall surface.
4. Load the smallest matching reference below.
5. Build a deterministic local proof before adding remote offsets, retry loops or brute force.
6. Derive constants from the target. Historical writeup addresses/offsets are examples only.

Useful baseline:

```bash
file ./chall
checksec --file=./chall
ldd ./chall 2>/dev/null || true
readelf -hW ./chall
readelf -lW ./chall | grep -E 'INTERP|GNU_STACK|GNU_RELRO'
```

## Technique router

| Primitive / signal | Load first | Add only if needed |
|---|---|---|
| simple stack/global overflow, ret2win, canary basics | `overflow-basics.md` | `rop-and-shellcode.md` |
| `%p/%s/%n`, arbitrary read/write through printf family | `format-string.md` | `advanced.md` |
| ROP, ret2libc, ret2csu, shellcode | `rop-and-shellcode.md` | `rop-advanced.md` |
| SROP, pivots, exotic gadgets, constrained ROP | `rop-advanced.md` | matching `advanced-exploits*.md` |
| tcache/fastbin/unsorted/UAF/double-free | `heap-techniques.md` | `heap-techniques-2.md`, `references/how2heap-patterns.md` |
| FILE structures / FSOP | `heap-fsop.md` | allocator reference matching exact glibc |
| general hard native chain | `advanced.md` | one matching `advanced-exploits*.md` |
| seccomp/sandbox syscall constraints | `sandbox-escape.md` | ROP/SROP reference as needed |
| kernel module/device primitive | `kernel.md` | `kernel-techniques.md` |
| mitigation/privilege boundary kernel bypass | `kernel-bypass.md` | `references/kernelpwn-patterns.md` |
| recent hard kernel patterns | `references/kernelpwn-patterns.md` | `references/sekaictf2025-hard-pwn-patterns.md` |
| allocator exploitation pattern lookup | `references/how2heap-patterns.md` | exact glibc source/version |
| path-hash / FUSE-style challenge | `references/fuse-path-hash-pwn-playbook.md` | `templates/path_hash_bruteforce.py` |
| DalCTF/Sekai-style modern chain | relevant file in `references/` | `ctf-solve/references/modern-chains.md` |
| unclear historical niche | `field-notes.md` | one `advanced-exploits*.md` selected by TOC |

Do **not** read all `advanced-exploits*.md` files by default. Select by primitive/TOC.

## Primitive-first decision tree

```text
crash / weird behavior
  -> exact offset / object / state transition
  -> what can be controlled?
       PC? pointer? length? index? format string? freed object? kernel object?
  -> what leak is needed?
  -> what mitigation blocks direct control?
  -> smallest target-derived chain
```

The exploit plan should name the primitive before naming a technique.

## Stack / ROP discipline

Before remote exploitation, derive:

- exact cyclic offset;
- canary location/value if required;
- PIE base leak source;
- libc identity/base from the supplied or remote-matched libc;
- gadget addresses from that binary/libc;
- stack alignment;
- bad bytes/input terminators;
- whether the process persists across stages.

A two-stage exploit must prove that leaks and later corruption happen in the same relevant process/state.

## Format-string discipline

1. Map positional arguments with bounded probes.
2. Identify pointer ownership and stack/libc/PIE candidates.
3. Establish read/write primitive separately.
4. Account for output byte count, field widths and target write size.
5. Prefer minimal `%hhn/%hn/%n` writes appropriate to the target.
6. Re-check indexes remotely if environment/layout differs.

## Heap discipline

Heap techniques are strongly version-dependent. Record:

- glibc version/build;
- allocation/free sequence;
- chunk sizes and bins;
- tcache count/state;
- safe-linking behavior;
- whether the target zeroes or edits freed data;
- object callback/vtable/function-pointer offsets.

Use `references/how2heap-patterns.md` as a pattern library, then verify against the exact allocator.

## FSOP discipline

Do not assume an old `_IO_FILE` layout/gadget survives a newer libc. Derive:

- relevant structure offsets;
- validation checks;
- vtable/wide-data behavior;
- writable target objects;
- trigger path.

When FILE exploitation is too version-fragile, reconsider simpler arbitrary-write targets before forcing FSOP.

## Kernel discipline

Capture exact kernel/config/environment facts before importing a technique:

```bash
uname -a
cat /proc/version
cat /proc/sys/kernel/kptr_restrict 2>/dev/null
cat /proc/sys/kernel/dmesg_restrict 2>/dev/null
```

If provided, inspect kernel config, module source, initramfs, QEMU command line and mitigation settings. Separate the bug primitive from the privilege-escalation primitive.

## Partial overwrite / brute force

Brute force is justified only after calculating the actual remaining entropy. Make attempts self-validating and bounded. Prefer a payload that directly reads the flag over a fragile interactive shell when repeated fresh processes are required.

## Cross-category pivots

- Need program semantics / deobfuscation before identifying a bug -> `ctf-reverse`.
- Exploit begins from HTTP but native memory corruption becomes the hard part -> stay `ctf-pwn`; keep `ctf-web` only for delivery details.
- Crypto check/signature is the blocker rather than memory corruption -> add `ctf-crypto`.
- Kernel/disk evidence extraction rather than exploitation becomes dominant -> `ctf-forensics`.

## Completion criteria

- primitive reproduced;
- target-specific offsets/versions derived;
- mitigations accounted for;
- exploit is scripted/reproducible when practical;
- final flag path is verified;
- `PROGRESS.md` contains leaks/bases/offsets and decisive state transitions.

## V1 migration rule

Standalone pwn technique packages should become internal references/scripts rather than additional top-level skills. Existing V1 knowledge remains available on `archive/pre-restructure-20260823` while V2 deduplication is validated.