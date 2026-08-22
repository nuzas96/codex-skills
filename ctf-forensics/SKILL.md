---
name: ctf-forensics
description: Solve CTF digital-forensics challenges involving disk/filesystem images, memory dumps/coredumps, Windows/Linux/browser/container artifacts, network/PCAP and peripheral captures, steganography/media, PDFs/documents, deleted-file recovery, signals/hardware traces, cryptocurrency evidence and unusual forensic containers. Use when extracting, reconstructing or correlating evidence from artifacts is the primary path to the flag.
license: MIT
compatibility: Requires artifact-specific forensic tooling only when selected by the evidence; Python 3 and common CLI inspection tools are sufficient for first-pass triage.
metadata:
  user-invocable: "false"
---

# CTF Forensics — V2 Router

Use `ctf-solve` for lifecycle/progress handling. This skill owns evidence extraction and reconstruction; load only the reference matching the artifact.

## First pass: preserve before transforming

1. Identify every supplied artifact with `file`, magic bytes, size and hashes when useful.
2. Work on copies when a tool mutates/rebuilds the artifact.
3. Compare extension vs actual format; mismatches are often intentional.
4. Search cheap metadata/strings/embedded signatures before carving everything.
5. Identify whether the task is filesystem-aware recovery, raw carving, timeline analysis, protocol reconstruction, hidden media data or nested-container extraction.
6. Keep an outside-in chain of every extracted layer.

Example:

```bash
file -- *
sha256sum * 2>/dev/null
strings -a suspect | head -100
xxd -l 128 suspect
binwalk suspect 2>/dev/null
```

## Artifact router

| Artifact / evidence | Load first | Add only if needed |
|---|---|---|
| RAM dump / hiber/coredump / process memory | `disk-and-memory.md` | `disk-advanced.md` |
| disk/E01/dd/VMDK/filesystem | `disk-and-memory.md` | `disk-recovery.md`, `disk-advanced.md` |
| deleted/corrupt/nested filesystem/file | `disk-recovery.md` | `disk-advanced.md` |
| Linux logs/process/app artifacts | `linux-forensics.md` | disk/memory ref |
| Windows registry/event/artifacts | `windows.md` | disk/memory ref |
| PCAP/PCAPNG/basic protocol | `network.md` | `network-advanced.md` |
| timing/covert/SMB/DNS/advanced network | `network-advanced.md` | protocol-specific extraction |
| USB/HID/Bluetooth/peripheral capture | `peripheral-capture.md` | `network-advanced.md` |
| image/text/archive/general stego | `steganography.md` | `stego-image.md` |
| image-specific pixel/palette/JPEG/BMP/PNG stego | `stego-image.md` | `stego-advanced.md` |
| audio/video/SSTV/FFT/advanced media | `stego-advanced.md` | `stego-advanced-2.md` |
| exotic/multi-layer stego | `stego-advanced-2.md` | general stego reference |
| logic analyzer/power/UART/VGA/hardware signal | `signals-and-hardware.md` | network/peripheral ref if transport capture |
| 3D/CAD/G-code | `3d-printing.md` | general artifact triage |
| known DalCTF stacked artifact pattern | `references/dalctf2026-patterns.md` | matching canonical artifact ref |

Specialist V1 packages for Volatility, Hindsight, Wireshark, Foremost, SQLite, Docker, Zimmerman, peepdf and stego are being merged into these canonical families and their scripts preserved under this category.

## Memory decision tree

```text
memory artifact
  -> identify OS/profile/build/architecture
  -> process/module/network overview
  -> suspicious process/object/file
  -> focused extraction
  -> correlate with disk/network/config evidence
```

For Windows memory, prefer Volatility 3-compatible plugins and verify plugin names against installed version. Do not blindly copy Volatility 2 commands.

Capture useful facts:

- OS/build and architecture;
- suspicious processes/parents/cmdline;
- network sockets;
- mapped/dumped files;
- environment/credentials/keys only as challenge evidence;
- MFT/file objects when deleted data is involved.

## Disk/filesystem decision tree

Prefer filesystem-aware recovery before raw carving:

```text
partition/table -> filesystem metadata -> allocated/deleted entry -> exact file extraction
```

Use carving when metadata is missing/corrupt or the file is unreferenced.

Check:

- partitions and offsets;
- deleted directory/MFT/inode entries;
- journal/WAL/snapshots;
- alternate/resource streams;
- filesystem-specific slack/unallocated space;
- nested archives/images/containers.

A deleted file may still have metadata that gives cleaner boundaries than `foremost`/`scalpel`.

## Network decision tree

1. Summarize protocols/endpoints/conversations.
2. Follow likely streams before mass extraction.
3. Export transferred objects/credentials/files only when protocol supports it.
4. Inspect timing, ordering, flags, DNS labels and retransmission anomalies when payload is empty/normal-looking.
5. For encrypted traffic, look for supplied keys/session secrets or endpoint artifacts before attempting cryptanalysis.

Use `tshark` filters for reproducible extraction and Wireshark for visual exploration when useful.

## Peripheral capture discipline

For HID/mouse/keyboard/USB:

- derive report layout from descriptor/packet shape;
- handle signed deltas and endianness correctly;
- reconstruct cumulative coordinates/state;
- separate button-down strokes from movement;
- test orientation/reflection only after the raw reconstruction is correct.

Do not assume a standard report offset when descriptor evidence exists.

## Steganography discipline

Start with structure, not random steg tools:

1. validate file/container structure;
2. inspect metadata/chunks/segments/trailing data;
3. compare channels/bitplanes/palettes/frames;
4. inspect dimensions, alpha, frame timing and disposal modes;
5. move to FFT/spectrogram/statistical methods only when simpler structural channels fail.

For animated images, inspect each frame independently and differences between frames.

## Signals / hardware

Identify sampling model first:

- clock/data edges;
- baud/symbol rate;
- channel mapping;
- amplitude/frequency encoding;
- synchronous vs asynchronous framing.

Plot/histogram before hard-coding thresholds. Validate decoded bytes against expected framing/magic/text.

## Nested container rule

Treat suspiciously large or structurally odd documents as possible carriers.

Record every transformation, for example:

```text
PDF -> embedded base64 -> ZIP -> SIF -> SquashFS -> file
```

At every layer verify magic bytes before choosing the next extractor. A password/hint from one layer may unlock the next.

## Database/browser/container artifacts

During V2 consolidation, canonical ownership is:

- browser history/cookies/downloads -> Forensics browser reference;
- SQLite/WAL/freelist/edit history -> Forensics SQLite reference;
- Docker image/layers/runtime evidence -> Forensics container reference;
- Windows artifact tooling/KAPE/Zimmerman -> Forensics Windows reference;
- malicious PDF structure/extraction -> Forensics PDF reference, then `ctf-malware` if executable payload behavior becomes primary.

These should not remain separate top-level skills after migration.

## Cross-category pivots

- extracted ciphertext requires cryptanalysis -> `ctf-crypto`;
- recovered binary must be understood -> `ctf-reverse`;
- recovered exploit/memory-corruption path becomes primary -> `ctf-pwn`;
- artifact identifies a real-world person/location that must be traced -> `ctf-osint`;
- malicious executable/script behavior/C2 becomes the goal -> `ctf-malware`.

Preserve the extraction chain in progress before pivoting.

## Completion criteria

- evidence chain from original artifact to final data is reproducible;
- every format/offset/transformation is recorded;
- filesystem/protocol-aware extraction was preferred when possible;
- recovered candidate is validated against challenge context/flag format;
- `PROGRESS.md` identifies original and generated artifact paths.

## V1 migration rule

Forensic tools are techniques, not top-level skills. Hindsight, Volatility, Wireshark, Foremost, SQLite, Docker, stego, Zimmerman, peepdf and similar specialist packages will become focused `ctf-forensics/references/` and `scripts/` while their V1 originals remain frozen on `archive/pre-restructure-20260823` during validation.