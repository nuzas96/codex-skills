---
name: ctf-reverse
description: "Solve CTF reverse-engineering challenges involving compiled, obfuscated, packed, virtualized, or platform-specific programs: ELF/PE, APK/iOS, WASM, firmware, bytecode/custom VMs, game clients, Go/Rust/.NET/Swift/Kotlin, and anti-analysis logic. Use when program semantics are the primary blocker."
---

# CTF Reverse — V2 Router

Use `ctf-solve` for lifecycle/progress. This skill owns program/platform semantics and routes to the smallest relevant reference.

## First pass

1. Identify format/container, architecture, language/runtime and packing/obfuscation signals.
2. Run cheap static triage before heavyweight tools.
3. Locate input, validation, success/failure, encoding/crypto and anti-analysis boundaries.
4. Pick static, dynamic, emulation or symbolic analysis based on the blocker.
5. Patch only nuisance behavior needed to expose semantics.
6. Automate recovered transformations after understanding them.

For ELF ABI, available emulator/debugger/disassembler, protections, dynamic-loader and Ghidra availability, use the deterministic report in [references/tool-readiness.md](references/tool-readiness.md) before starting heavyweight analysis.

```bash
file ./chall
strings -a -n 5 ./chall | head -200
readelf -hSW ./chall 2>/dev/null || true
objdump -d ./chall 2>/dev/null | head
```

## Reference router

| Evidence / blocker | Load first | Add only if needed |
|---|---|---|
| ELF architecture / local tool or emulator readiness | `references/tool-readiness.md` | generic native / decompiler ref |
| generic native / decompiler | `references/ghidra-native.md` | `tools.md`, `patterns.md` |
| AtomPePacker / `.ATOM` / `PP64Stub` / EasyLZMA | `references/atompepacker-lzma.md` | `tools-dynamic.md` only if offline recovery fails |
| debugger/runtime tracing | `tools-dynamic.md` | `patterns-runtime.md` |
| emulation / Unicorn / Qiling | `tools-emulation.md` | `references/unicorn-pe-emulation.md` |
| symbolic execution | `tools-advanced.md` | `tools-advanced-2.md` |
| anti-debug / anti-VM | `anti-analysis.md` | `anti-analysis-ctf.md` |
| common validator/transformation | `patterns.md` | `patterns-ctf*.md` selected by TOC |
| Android APK / Java/Kotlin / resources | `references/android-apk-jadx.md` | `references/mobile-app-security.md`, native ref for JNI |
| .NET managed assembly | `references/dotnet-dnspy.md` | `languages.md` |
| iOS runtime / Objective-C / Swift tracing | `references/ios-frida.md` | `references/ghidra-native.md` |
| Rust binary | `references/rust-binaries.md` | `languages-compiled.md` |
| Go binary | `languages-compiled.md` | `golang-malware-rev.md` |
| firmware / embedded filesystem | `references/firmware-binwalk.md` | `platforms-hardware.md`, `ctf-forensics` if recovery dominates |
| AVR firmware with repeated GPIO/LED writes or serial-like pin output | `references/avr-gpio-static-recovery.md` | MCU-specific datasheet; bounded emulation only when static control flow cannot resolve timing/polarity |
| Android IPC / mobile TLS runtime checks | `references/mobile-app-security.md` | Android/iOS platform ref |
| WASM/game/platform target | `platforms.md` | `platforms-hardware.md` |
| custom VM validator with straight-line add/XOR/rotate/odd-multiply transforms and known compare constants | `references/algebraic-vm-validator-inversion.md` | `patterns-ctf.md`; emulation/symbolic refs only if a lossy core remains |
| VMProtect/custom VM where only p-code/tape operands may change and execution trace must stay identical | `references/vmprotect-trace-preserving-pcode.md` | `tools-emulation.md`, `tools-advanced.md` |
| custom VM/bytecode | `patterns-ctf.md` | emulation/symbolic refs |
| recent hard patterns | `references/sekaictf2025-reverse-patterns.md` | matching focused ref |
| uncertain niche | `field-notes.md` | only after normal refs fail |

Do not preload every platform/tool reference.

## Strategy

### Static first
Use when strings/imports/resources/control flow are readable. Trace the smallest flag-relevant path and improve types/xrefs only there.

### Dynamic first
Use when runtime decryption/unpacking/environment/time behavior hides a specific value. Instrument one boundary and return to offline analysis.

### Emulation
Use for bounded routines or inconvenient architectures when dependencies can be stubbed.

### Symbolic execution
Use only after success/failure semantics are known and state explosion/nondeterminism can be controlled.

## Packed / self-modifying

```text
identify loader/packer
 -> locate unpack/decrypt boundary
 -> recover stable stage
 -> re-run format/import/string analysis
 -> reverse recovered code
```

## Custom VM / bytecode

Recover instruction width/format, opcode dispatch, VM state, operands, branch/call semantics and validation flow. Build a disassembler/emulator once semantics stabilize rather than manually tracing hundreds of instructions.

Before implementing a full emulator, slice from the compare/failure path back to input loads and write the validator as equations. If the flag-relevant path is straight-line and composed of bijections over a fixed-width word — especially add/subtract, XOR, rotates, and multiplication by an odd constant modulo `2^w` — route to `references/algebraic-vm-validator-inversion.md` and invert the expected constants directly. Forward-verify every recovered round in the original semantics. Use emulation/SMT only for branches or lossy operations that remain after pushing constants backward through invertible layers.

If a challenge constrains patches to the VM tape while requiring identical handler/control-flow traces, prefer the focused trace-preserving operand workflow instead of full devirtualization.

## Platform ownership

- Android static/decompile -> `android-apk-jadx.md`.
- .NET metadata/IL -> `dotnet-dnspy.md`.
- iOS runtime -> `ios-frida.md`.
- native assembly/decompiler -> `ghidra-native.md`.
- Rust-specific layouts/runtime noise -> `rust-binaries.md`.
- firmware extraction -> `firmware-binwalk.md`.
- mobile IPC/pinning behavior -> `mobile-app-security.md`.

If the recovered sample is malicious, generic platform mechanics stay here; behavior/config/C2 interpretation goes to `ctf-malware`.

## Patch discipline

Patch only anti-debug/random/sleep/environment gates needed to expose deterministic behavior. Revalidate the recovered candidate against the original unpatched target.

## Cross-category pivots

- exploit construction after a known memory-corruption bug -> `ctf-pwn`;
- mathematically hard crypto -> `ctf-crypto`;
- disk/memory/container extraction -> `ctf-forensics`;
- malware behavior/config/C2 -> `ctf-malware`;
- browser/API trust boundary -> `ctf-web`.

## V2 ownership rule

Reverse tool/platform knowledge is internal to `ctf-reverse/references/` or existing category notes. Do not create a new top-level skill for Ghidra, JADX, dnSpy, Frida, Rust, firmware or mobile IPC/TLS.

The complete V1 sources remain recoverable from `archive/pre-restructure-20260823`.

Load [references/legacy-evidence-lessons.md](references/legacy-evidence-lessons.md) only when preserved validator, APK, VM, flattened-control-flow, or protocol lessons match the evidence.
