# Deterministic ELF tool readiness

Use this before disassembly/decompilation when a target is ELF, foreign-architecture, or the host has previously failed to execute an ELF ABI. It inspects metadata and tool availability; it does not execute the challenge binary.

    python3 "$HOME/.codex/skills/ctf-reverse/scripts/reverse_readiness.py" ./chall

The JSON report includes ELF class/machine/type, PT_INTERP and whether that loader exists locally, checksec output when installed, QEMU matching the ELF machine, debugger/disassembler presence, Java, and Ghidra headless launcher discovery. An architecture match is only a candidate: seccomp, kernel support, dynamic libraries and loader versions can still prevent execution. Validate actual execution separately with a benign same-ABI fixture or use the matching QEMU user emulator. The report marks the challenge binary as not executed.

Only when Ghidra is likely to be useful, explicitly check that its launcher reaches usage output without creating a project or importing the challenge:

    python3 "$HOME/.codex/skills/ctf-reverse/scripts/reverse_readiness.py" ./chall --probe-ghidra --timeout 15

The optional probe starts Java/Ghidra and may take around a second; the default check only locates the headless launcher and Java. Optional --versions adds separate version-command startups. All subprocesses have per-tool timeouts. Pwntools checksec runs with its update check disabled in an isolated temporary config/cache, so a first readiness check does not make network requests or change user config.

## Output interpretation

- Missing architecture tools: use existing static inspection tools before installing packages; do not start Ghidra just because it is installed.
- Foreign ELF with matching qemu-*: use that emulator only when execution materially helps; confirm dynamic loader/library needs from PT_INTERP and challenge documentation.
- Native architecture candidate but runtime failure: inspect the actual error and kernel/ABI constraints rather than assuming QEMU is unnecessary.
- Ghidra launcher not found or its help probe times out: use disassembly/debugger tools already present; bound any later project import separately.

The helper depends only on Python's standard library. file, readelf, checksec, QEMU, GDB, objdump and Ghidra are optional system tools. Missing tools are reported rather than treated as fatal.
