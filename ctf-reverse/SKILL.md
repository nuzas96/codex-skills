---
name: ctf-reverse
description: Solve CTF reverse-engineering challenges where the main task is understanding a compiled, obfuscated, packed, virtualized or platform-specific program: ELF/PE/native binaries, APK/iOS apps, WASM, firmware, bytecode/custom VMs, game clients, Go/Rust/.NET/Swift/Kotlin and anti-debug/anti-analysis logic. Use when program semantics are the blocker. Pivot to ctf-pwn once the vulnerability is understood and memory-corruption exploitation becomes the main task.
license: MIT
compatibility: Requires target-appropriate static/dynamic analysis tools plus Python 3 for automation/emulation when needed.
metadata:
  user-invocable: "false"
---

# CTF Reverse — V2 Router

Use `ctf-solve` for lifecycle/progress handling. This skill routes reverse-engineering work to the smallest relevant reference.

## First pass

1. Identify file/container, architecture, language/runtime and packing/obfuscation signals.
2. Run cheap static triage before opening a heavyweight decompiler.
3. Locate input, validation, success/failure, crypto/encoding and anti-analysis boundaries.
4. Choose static, dynamic, emulation or symbolic analysis based on the blocker.
5. Patch only nuisance behavior needed to expose semantics; keep validation logic intact.
6. Automate recovered transformations after understanding them.

Baseline:

```bash
file ./chall
strings -a -n 5 ./chall | head -200
readelf -hSW ./chall 2>/dev/null || true
objdump -d ./chall 2>/dev/null | head
```

Use language/platform-specific signatures when `file` and strings indicate managed/runtime code.

## Reference router

| Evidence / blocker | Load first | Add only if needed |
|---|---|---|
| generic native static analysis | `tools.md` | `patterns.md` |
| debugger/runtime tracing | `tools-dynamic.md` | `patterns-runtime.md` |
| emulation / Unicorn / Qiling-style analysis | `tools-emulation.md` | `references/unicorn-pe-emulation.md` |
| symbolic execution / advanced frameworks | `tools-advanced.md` | `tools-advanced-2.md` |
| anti-debug / anti-VM / environment checks | `anti-analysis.md` | `anti-analysis-ctf.md` |
| common CTF validator/transformation patterns | `patterns.md` | `patterns-ctf.md` |
| additional CTF hard patterns | `patterns-ctf-2.md` / `patterns-ctf-3.md` | select by TOC |
| runtime/self-modifying behavior | `patterns-runtime.md` | dynamic/emulation refs |
| Python/JS/Java/.NET/managed languages | `languages.md` | `languages-platforms.md` |
| Go/Rust/Swift/Kotlin/C++ compiled languages | `languages-compiled.md` | language-specific specialist migration ref |
| APK/mobile/platform packaging | `languages-platforms.md` | mobile specialist refs during migration |
| game engines/WASM/platform targets | `platforms.md` | `platforms-hardware.md` |
| ARM/RISC-V/hardware/embedded | `platforms-hardware.md` | firmware reference |
| firmware filesystem/extraction | `firmware-extraction.md` | `ctf-forensics` if artifact recovery dominates |
| Go malware-like binary | `golang-malware-rev.md` | `ctf-malware` if behavior/C2 becomes primary |
| recent Sekai reverse patterns | `references/sekaictf2025-reverse-patterns.md` | one matching core reference |
| uncertain niche | `field-notes.md` | only after normal category references fail |

Do not read all pattern/tool files by default. Select based on the current blocker.

## Analysis strategy

### Static first when

- strings/imports expose obvious validation structure;
- control flow is readable;
- constants/tables/embedded resources matter;
- the binary is not heavily packed/self-modifying.

### Dynamic first when

- values are decrypted/unpacked at runtime;
- environment/time/randomness changes behavior;
- anti-debug or self-modifying code hides the real path;
- a short breakpoint/watchpoint reveals the compared value directly.

### Emulation when

- executing the full target is inconvenient/unsafe;
- only a bounded function/routine matters;
- platform dependencies can be stubbed;
- instruction-level visibility is more useful than full OS behavior.

### Symbolic execution when

- input constraints are narrow but path conditions are tedious;
- success/failure addresses are identifiable;
- state explosion can be controlled;
- nondeterministic nuisance branches can be safely patched/stubbed.

Do not start angr/Manticore/Triton before identifying success/failure semantics and major blockers.

## Packed / obfuscated targets

1. Determine whether the packer/loader can be unpacked generically.
2. If not, identify where original code/data appears in memory.
3. Dump after unpack/decrypt boundary.
4. Re-run file/import/string analysis on the recovered image.
5. Only then spend time on function-level reversing.

## Custom VM / bytecode

Recover, in order:

1. bytecode format/instruction width;
2. opcode dispatch;
3. VM state/register/stack model;
4. operand decoding/endian rules;
5. branch/call semantics;
6. validation/data-flow logic.

Build a disassembler/emulator once instruction semantics are stable. Do not manually trace hundreds of instructions if a small emulator can make state observable.

## Language/runtime discipline

Recognizing the implementation language changes the analysis strategy:

- Go: large statically linked binaries, pclntab/runtime metadata;
- Rust: monomorphization, panic strings, trait/vtable patterns;
- .NET: metadata/IL usually beats native-style disassembly;
- Java/Kotlin Android: decompile bytecode/resources first, then dynamic hooks as needed;
- Swift/iOS: symbol/runtime metadata and Frida/native debugging can complement static analysis.

Canonical language tooling should live here, while malware workflows link to it rather than duplicating generic reversing instructions.

## Patch discipline

Patch only what is needed to reveal deterministic behavior:

- anti-debug check;
- random early exit;
- sleep/timing delay;
- environment gate.

Preserve the actual validator/decoder/crypto path. Revalidate recovered input against the **original unpatched** program.

## Cross-category pivots

- memory-corruption primitive is understood and exploit construction is now the blocker -> `ctf-pwn`;
- recovered algorithm is cryptographically hard rather than implementation-hard -> `ctf-crypto`;
- artifact/container recovery dominates -> `ctf-forensics`;
- malicious behavior/config/C2 is the investigation goal -> `ctf-malware`;
- browser/API delivery becomes the main trust boundary -> `ctf-web`.

## Completion criteria

- important program semantics are explained;
- transformations/VM logic are reproducible in a script when practical;
- anti-analysis bypass does not alter the true solution logic;
- candidate flag/input validates against the original target;
- `PROGRESS.md` contains decisive offsets/functions/algorithms and artifact paths.

## V1 migration rule

Tool-specific reversing skills (Ghidra, JADX, dnSpy, Frida, Rust, etc.) are being consolidated as internal Reverse references/scripts. Generic reversing knowledge has one canonical owner here; malware-specific workflow notes stay in `ctf-malware`.