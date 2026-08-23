# Apple DMG / UDIF Forensic Recovery

Use this reference when a CTF artifact is a macOS disk image (`.dmg`) or raw UDIF container and the evidence must be recovered without executing its contents.

## Recognize

Strong signals:

- a downloaded `.dmg` is part of an infection or delivery chain;
- normal archive extraction does not expose the real filesystem;
- the image ends with an Apple UDIF `koly` trailer;
- embedded plist/resource metadata contains `blkx` tables;
- reconstructed data exposes HFS+, APFS, or a partition map;
- the filesystem contains a Mach-O, app bundle, script, plist, or other executable evidence.

The forensic primitive is **container reconstruction and filesystem-aware extraction**, not running the installer.

## Evidence-preserving workflow

1. Hash and identify the DMG before touching it.
2. Work on a copy and never execute recovered apps/scripts during forensic triage.
3. Try safe native tooling first when available (`hdiutil imageinfo`, `hdiutil attach -readonly -noautoopen`, `7z`, `dmg2img`).
4. If ordinary tools fail or are unavailable, inspect the UDIF trailer/resource metadata directly.
5. Reconstruct the logical disk from `blkx` block runs.
6. Identify the resulting partition/filesystem by magic rather than extension.
7. Extract suspicious files filesystem-aware where possible.
8. Verify extracted binaries/scripts by magic/hash/strings before any reverse or malware-analysis pivot.
9. Preserve the outside-in chain in `PROGRESS.md`.

Typical chain:

```text
network/download evidence
  -> DMG / UDIF
  -> blkx block map
  -> reconstructed logical disk
  -> HFS+ / APFS / partition
  -> Mach-O / script / app evidence
  -> reverse or malware analysis only if that becomes the hard primitive
```

## UDIF structure triage

Apple UDIF images commonly keep a fixed-size `koly` trailer near the end of the file. The trailer points to XML/resource metadata that can contain one or more `blkx` entries. Each `blkx` table describes runs that map compressed, raw, zero-filled, or other stored chunks into logical disk sectors.

Useful checks:

```bash
file suspect.dmg
sha256sum suspect.dmg
strings -a suspect.dmg | grep -E 'koly|blkx|mish|plist|HFS|APFS' | head
xxd -s -512 suspect.dmg | head -40
```

Do not assume the visible bytes before the trailer are already a mountable filesystem. UDIF is a block-mapped container and may need run-by-run reconstruction first.

## `blkx` reconstruction model

For each block table:

1. parse its `mish`/block-run metadata;
2. read every run in logical-sector order;
3. map source offsets relative to the image data fork correctly;
4. copy raw runs directly;
5. expand zero/ignore runs as logical zeroes where appropriate;
6. decompress compressed runs with the matching codec (commonly zlib; other DMGs may use different codecs);
7. write output at the run's logical sector offset rather than simply concatenating arbitrary stored chunks;
8. stop at the table terminator and validate reconstructed size/magic.

Treat run offsets, sector counts, compressed lengths, and codec identifiers as target-derived fields. A parser that ignores any one of them can produce an image that looks partly valid but corrupts file contents later.

## Filesystem handoff

After reconstruction, identify the next layer:

```bash
file reconstructed.img
fdisk -l reconstructed.img 2>/dev/null
mmls reconstructed.img 2>/dev/null
binwalk reconstructed.img 2>/dev/null
```

For Apple filesystems, common evidence includes:

- HFS+ / HFSX volume headers;
- APFS container/volume structures;
- GPT/partition maps surrounding the filesystem;
- app bundles, property lists, launch items, scripts, and Mach-O binaries.

Prefer filesystem-aware extraction over blind carving when metadata is intact. Use carving only when the filesystem cannot be parsed or when deleted/unallocated evidence is the actual target.

## Mach-O and script extraction

A DMG that delivers malware often contains an executable or script, but extracting it does **not** automatically make reversing the primary category.

First record:

```text
path in filesystem
file type / architecture
hash
signing/notarization metadata when available
interesting strings/imports
parent delivery artifact
```

Then pivot by primitive:

- binary semantics / embedded decryption routine -> `ctf-reverse`;
- malicious behavior, C2, stealer configuration, persistence, or command logic -> `ctf-malware`;
- recovered ciphertext/key relation -> `ctf-crypto`;
- keep `ctf-forensics` primary while the hard work is still extraction/correlation.

Do not execute an extracted Mach-O or AppleScript merely to learn what it does when static recovery is sufficient.

## Correlating with PCAP evidence

When the DMG came from a PCAP, preserve provenance across layers:

```text
email/web lure
  -> download host/URI
  -> exact DMG bytes/hash
  -> filesystem path of payload
  -> network callback/exfil stream
  -> recovered encrypted or archived artifact
```

A filename alone is weak evidence. Correlate timestamps, host/URI, hashes, HTTP objects, callback destinations, and extracted artifact behavior.

## Common failure modes

- Treating `.dmg` as an ordinary ZIP/tar archive.
- Mounting or opening a suspicious image read-write or allowing auto-launch behavior.
- Searching only for filesystem magic in the compressed DMG and concluding the filesystem is missing.
- Concatenating compressed blocks without respecting logical sector offsets.
- Assuming every `blkx` run uses zlib.
- Carving a Mach-O before checking whether filesystem metadata can recover the exact path and provenance.
- Pivoting to malware/reverse before the container and filesystem reconstruction is reproducible.
- Executing the recovered payload when static evidence is enough.

## Source / provenance

Reusable pattern harvested from **Equilibrium CTF 2025 — Famous AMOS** by `warlocksmurf` after solving a supplied PCAP-based macOS infection chain. The challenge required recovering a downloaded DMG, reconstructing Apple disk-image content, extracting executable evidence, and correlating it with later network/exfil artifacts.

Public challenge provenance:

- https://github.com/warlocksmurf/bluelobster-grimoire/tree/main/equilibrium-ctf-2025/forensics_famous-amos

Harvested: 2026-08-23.

The permanent lesson is the **safe UDIF/DMG reconstruction and evidence-preserving pivot workflow**. Do not store the challenge flag, victim-specific values, malware keys, or one-off hashes in this reference.