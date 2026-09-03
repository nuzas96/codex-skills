---
name: ctf-forensics
description: "Solve CTF digital-forensics challenges involving disk/filesystem images, memory dumps, Windows/Linux/browser/container artifacts, PCAP and peripheral captures, steganography/media, PDFs, deleted-file recovery, signals/hardware traces, SQLite history, and unusual containers. Use when extracting, reconstructing, or correlating artifact evidence is primary."
---

# CTF Forensics — V2 Router

Use `ctf-solve` for workspace/progress/stuck recovery. This skill owns artifact extraction and correlation. Load only the reference matching the artifact and current primitive.

## First pass: preserve before transforming

1. Identify every artifact with `file`, magic, size and hashes when useful.
2. Work on copies when a tool can mutate/checkpoint/rebuild evidence.
3. Compare extension vs actual format.
4. Search cheap metadata/strings/embedded signatures before carving everything.
5. Decide whether the problem is filesystem-aware recovery, raw carving, timeline analysis, protocol reconstruction, application artifact analysis, hidden media data or nested-container extraction.
6. Record the outside-in extraction chain in `PROGRESS.md`.

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
| RAM / raw memory / LiME / crash dump | `references/memory-volatility.md` | `disk-and-memory.md`, `disk-advanced.md` |
| disk/E01/dd/VMDK/filesystem | `disk-and-memory.md` | `disk-recovery.md`, `disk-advanced.md` |
| Apple DMG/UDIF, `koly`/`blkx`, HFS+/APFS delivery image | `references/apple-dmg-udif.md` | `disk-advanced.md` |
| encrypted OpenZFS send/replay stream, native ZFS encryption metadata, encrypted DMU file block | `references/openzfs-encrypted-send-stream.md` | `references/network-pcap.md` when recovered from traffic; `ctf-crypto` only for actual cryptanalysis |
| deleted/unallocated/corrupt file | `references/file-carving.md` | `disk-recovery.md` |
| Linux logs/process/app artifacts | `linux-forensics.md` | disk/memory reference |
| Windows disk/registry/MFT/Prefetch/EVTX/LNK/Jump Lists | `references/windows-artifacts.md` | `windows.md`, disk refs |
| RDP persistent bitmap cache, `Cache*.bin`, remote-only visual reconstruction | `references/rdp-persistent-bitmap-cache.md` | `references/windows-artifacts.md` for session corroboration |
| Chromium browser profile/history/cookies/storage | `references/browser-artifacts.md` | `references/sqlite-forensics.md` |
| SQLite DB/WAL/freelist/edit history | `references/sqlite-forensics.md` | application-specific artifact ref |
| Docker image/save/export/overlay/container evidence | `references/docker-containers.md` | `disk-and-memory.md` |
| PDF object/stream/attachment/incremental revision | `references/pdf-analysis.md` | nested-container / malware ref if extracted payload dominates |
| Active Directory intrusion PCAP: LDAP/Kerberos/WinRM/SMB/PowerShell attack-chain reconstruction | `references/ad-intrusion-pcap.md` | `references/network-pcap.md`; `ctf-misc/references/active-directory.md` only when active AD exploitation/pathing becomes primary |
| PCAP/PCAPNG/general protocol | `references/network-pcap.md` | `network-advanced.md` |
| timing/covert/SMB/DNS/advanced network | `network-advanced.md` | `references/network-pcap.md` |
| USB/HID/Bluetooth/peripheral capture | `peripheral-capture.md` | network ref |
| general stego / hidden media data | `references/stego-detection.md` | `steganography.md`, `stego-image.md` |
| image-specific JPEG/PNG/BMP/palette/bit-plane | `stego-image.md` | `stego-advanced.md` |
| audio/video/SSTV/FFT/advanced media | `stego-advanced.md` | `stego-advanced-2.md`, signals ref |
| logic analyzer/power/UART/VGA/hardware | `signals-and-hardware.md` | peripheral/network ref |
| 3D/CAD/G-code | `3d-printing.md` | general artifact triage |
| stacked/nested CTF artifact chain | `references/dalctf2026-patterns.md` | focused reference for each layer |

## Memory

```text
identify OS/build/arch
  -> process tree + cmdline/env + network overview
  -> suspicious process/file/object
  -> targeted dump/extraction
  -> correlate with disk/network/config
```

Use Volatility 3 plugin names for a Volatility 3 environment; do not blindly copy Volatility 2 profiles/plugins. If symbols fail, solve the symbol problem or use simpler artifact/string/application analysis rather than treating the absence of plugin output as evidence.

## Disk / filesystem

Prefer filesystem-aware recovery:

```text
partition -> filesystem metadata -> allocated/deleted entry -> exact extraction
```

Then use raw carving when metadata is unavailable/corrupt. Check journals, WAL, snapshots, alternate/resource streams, slack/unallocated space and nested containers as evidence demands.

For encrypted OpenZFS send streams, do not assume the artifact is a mountable pool image. Preserve the full reconstruction chain, parse enough replay-stream metadata to identify key properties and DMU object/write records, and use AEAD authentication as the proof for candidate passphrases and recovered blocks. Load `references/openzfs-encrypted-send-stream.md` before attempting ad-hoc AES decryption.

## Browser / SQLite

Preserve browser SQLite DBs with WAL/SHM. Decode application-specific timestamps correctly. Hindsight is a fast normalizer for Chromium artifacts but raw DB/storage/cache inspection remains authoritative when the answer is missing from the generated timeline.

SQLite challenge data may survive in WAL frames, freelists, page freeblocks or edit-history tables after logical deletion.

## Docker

Distinguish `docker save` layer history from `docker export` merged filesystem. Search image config/history, earlier layers, runtime changes, volumes and environment. A file deleted in a later Docker layer can still exist in the earlier layer tar.

## Network

1. Summarize protocol hierarchy/endpoints/conversations.
2. Follow relevant streams before mass extraction.
3. Export objects only for protocols that actually carry them.
4. Inspect timing/order/flags/DNS labels when payloads look normal.
5. Reconstruct exact ciphertext/framing before pivoting to crypto.

Use tshark for reproducible extraction and Wireshark for visual exploration.

When a PCAP contains coordinated LDAP, Kerberos, WinRM/WSMan, SMB and HTTP/PowerShell evidence from an Active Directory environment, do not analyze each protocol in isolation. Route to `references/ad-intrusion-pcap.md`, establish host roles and chronology first, decode account-control flags bitwise, and distinguish observed transfer/authentication evidence from inferred attack steps. In particular, encrypted WinRM can prove remote-management use without revealing the exact command body.

When a PCAP reconstructs into a nested carrier, keep artifact provenance across every layer. If indexed fragments carry per-chunk hashes, validate each fragment before concatenation and verify any whole-object manifest hash before decompressing or parsing the next layer.

## Windows artifacts

Choose the parser based on the artifact/question: MFTECmd for NTFS metadata, PECmd for Prefetch, RECmd for registry, EvtxECmd for EVTX, LECmd/JLECmd for links/jump lists, SBECmd for shellbags. KAPE is orchestration, not the analysis itself.

If the sought content was visible through Remote Desktop but the original file never existed on the examined client, do not stop at deleted-file carving. Check whether persistent bitmap caching was enabled, locate every plausible `Cache*.bin`, and route to `references/rdp-persistent-bitmap-cache.md`. Treat extracted bitmap-cache entries as presentation-layer residue: contact-sheet and cluster them first, then reconstruct from text/background/edge continuity rather than assuming cache index equals screen position.

## Steganography

Start structural:

1. metadata and format validity;
2. chunks/segments/trailing data/embedded magic;
3. channels/bitplanes/palettes/frames;
4. only then statistical/FFT/signal analysis.

Do not run every stego tool against every file. For custom bit extraction, explicitly record traversal order, channel, bit position and byte endianness.

## PDF / nested containers

Treat an unusually large/odd document as a possible carrier. Enumerate PDF objects/streams/attachments and incremental revisions before relying on visual rendering. At every extracted layer verify magic before choosing the next parser.

Example chain:

```text
PDF -> encoded stream -> ZIP -> SIF -> SquashFS -> flag file
```

## Cross-category pivots

Add a category only when the hard primitive changes:

- extracted ciphertext -> `ctf-crypto`;
- recovered binary/client logic -> `ctf-reverse`;
- memory corruption/exploit path -> `ctf-pwn`;
- real-world identity/geolocation -> `ctf-osint`;
- malware behavior/config/C2 -> `ctf-malware`.

Preserve the extraction chain before pivoting. Standard PBKDF2/HKDF/AES-GCM operations used only to unlock a reconstructed encrypted forensic artifact remain `ctf-forensics`; pivot to `ctf-crypto` only when breaking the cryptography becomes the dominant primitive.

AD packet-capture reconstruction remains `ctf-forensics` while the primary task is evidence correlation. Pivot to `ctf-misc/references/active-directory.md` only when the task becomes active authorized AD path exploitation such as BloodHound pathing, live Kerberoasting, ACL abuse or AD CS.

## V2 ownership rule

Forensic tools and artifact families are internal techniques, **not top-level skills**. New knowledge for Volatility, Hindsight, Wireshark, Foremost, SQLite, Docker, stego, Windows tooling, RDP bitmap caches, AD intrusion PCAP reconstruction, OpenZFS encrypted streams or PDF analysis belongs in the focused `ctf-forensics/references/` files above. Update this router only when a genuinely new artifact family appears.

The complete V1 source remains recoverable from `archive/pre-restructure-20260823`.

Load [references/legacy-evidence-lessons.md](references/legacy-evidence-lessons.md) only when preserved damaged-database, filesystem, media-path, mobile-backup, or HID lessons match the evidence.
