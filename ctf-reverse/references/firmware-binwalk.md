# Firmware Extraction and Reverse Triage

Use when a CTF supplies a firmware/blob/flash image whose embedded filesystem, kernel, bootloader, resources or executable components must be extracted before deeper reversing.

## Ownership boundary

Use this reference for **firmware-container extraction and triage**.

Do not use it as the primary workflow for:

- a normal standalone ELF/PE -> route to native reverse references;
- a full disk image/partitioned OS image -> route to `ctf-forensics`;
- a memory dump -> route to memory forensics;
- an already-extracted architecture-specific firmware binary -> route to the appropriate reverse/platform reference.

Once extraction produces a suspicious native binary, the hard primitive has changed: preserve the extraction provenance and pivot to ordinary reverse engineering.

## Outside-In Workflow

1. Hash and identify the outer artifact.
2. Inspect outer magic/header and approximate layout.
3. Run a signature scan with `binwalk`.
4. Use entropy only as a locator clue, not as proof of encryption.
5. Extract recognized archives/filesystems.
6. Verify every extracted component independently with `file`/magic.
7. Recurse only into meaningful nested components.
8. Once a root filesystem exists, map startup scripts, services, configs and target binaries.
9. Pivot to deeper reverse/crypto only after the extracted component is identified.

Start with:

```bash
sha256sum firmware.bin
file firmware.bin
xxd -l 128 firmware.bin
strings -n 8 firmware.bin | head
```

## Binwalk triage

`binwalk` is an accelerator, not proof that every hit is real. False positives occur inside compressed or high-entropy data.

Typical first pass:

```bash
binwalk firmware.bin
binwalk -v firmware.bin
```

Useful operations commonly include:

```bash
# signature filtering
binwalk -y "squashfs" firmware.bin
binwalk -y "gzip\|lzma\|xz\|zstd" firmware.bin

# architecture/signature hints
binwalk -A firmware.bin

# entropy visualization
binwalk -E firmware.bin

# extraction
binwalk -e firmware.bin

# recursive extraction
binwalk -Me firmware.bin
```

Exact option behavior differs across binwalk generations, so confirm the installed version and `binwalk --help` before relying on version-specific flags.

For recursive extraction, avoid an uncontrolled "Matryoshka" loop on a large blob. If supported by the installed version, limit recursion depth while you learn the outer layout.

## Filesystem families and practical tools

Common firmware filesystems:

| Family | Typical tool / action |
| --- | --- |
| SquashFS | `unsquashfs`; vendor-modified variants may require `sasquatch` |
| CramFS | format-aware extraction or loop mount where appropriate |
| JFFS2 | `jefferson` |
| UBI / UBIFS | UBI reader / `mtd-utils` tooling |
| gzip / xz / LZMA | carve exact region, then decompress with the matching tool |
| embedded ELF | extract and hand off to normal reverse workflow |

Examples:

```bash
# SquashFS
unsquashfs -d rootfs rootfs.squashfs

# JFFS2
jefferson rootfs.jffs2 -d rootfs_jffs2

# UBI/UBIFS-style images
ubireader_extract_images rootfs.ubi
```

If the standard parser rejects a filesystem that clearly has the expected magic/header, consider a vendor-modified format before assuming the offset is wrong.

## Manual extraction when auto-extraction fails

When a signature offset is credible but extraction fails, carve the candidate region precisely.

```bash
# decimal offset/length
dd if=firmware.bin of=component.bin bs=1 skip=327680 count=4194304

# hexadecimal arithmetic
dd if=firmware.bin of=component.bin bs=1 \
  skip=$((0x50000)) count=$((0x400000 - 0x50000))
```

Then validate independently:

```bash
file component.bin
xxd -l 64 component.bin
binwalk component.bin
```

A vendor wrapper, checksum header, alignment padding or a few prepended bytes can prevent a standard extractor from recognizing an otherwise-valid filesystem.

Do not carve huge ranges only because entropy changes. Prefer a boundary supported by magic/header structure or neighboring signature evidence.

## Entropy

Entropy is useful for locating boundaries, not classifying the exact transform.

General interpretation:

```text
very low entropy     -> padding / repetitive data
moderate entropy     -> plaintext / code / structured data
high entropy         -> compressed OR encrypted OR already-random material
```

A high-entropy region inside otherwise structured firmware is a candidate for compressed/encrypted content, but distinguish these using headers, magic, decompressor behavior and code references.

If the entire firmware is near-random, search for the decrypt/unwrap path in:

- bootloader code;
- update verification/decryption routines;
- device-specific key derivation;
- public recovery/update tooling supplied with the challenge.

## What to inspect after extraction

Prioritize structure before blind grep.

Map:

- `/etc` configuration;
- init/system startup scripts;
- web application/source;
- custom daemons;
- service binaries and versions;
- device-specific configuration partitions;
- certificates/keys;
- passwd/shadow only when relevant;
- binaries referenced by startup scripts.

Useful triage:

```bash
find rootfs -maxdepth 3 -type f | sort | less

grep -RniE 'password|passwd|secret|api[_-]?key|token' rootfs/etc rootfs/www 2>/dev/null
grep -Rni 'BEGIN.*PRIVATE KEY' rootfs 2>/dev/null

find rootfs -type f \( -name '*.pem' -o -name '*.crt' -o -name '*.key' -o -name '*.p12' \)
find rootfs -type f \( -name '*.html' -o -name '*.cgi' -o -name '*.php' -o -name '*.js' \)

strings -a rootfs/bin/busybox 2>/dev/null | grep -i 'BusyBox v'
```

For a CTF, plain challenge secrets may exist in configs or web content, but do not stop at the first suspicious string if the challenge requires a derived answer.

## Service-to-binary handoff

Once startup/config analysis identifies a custom service:

```bash
file rootfs/usr/sbin/suspicious
readelf -h rootfs/usr/sbin/suspicious 2>/dev/null
strings -a rootfs/usr/sbin/suspicious | head
```

Record the path and how the service is launched, then pivot:

- native ELF/PE -> native reverse workflow;
- custom VM/bytecode -> VM reference;
- encrypted config -> crypto if the transform becomes the hard part;
- web service/source -> `ctf-web`.

The extraction chain should remain reproducible:

```text
firmware.bin
  -> offset/component
  -> filesystem
  -> extracted path
  -> target binary/config
  -> downstream technique
```

## Common magic-byte triage

Useful signatures from the legacy firmware handbook:

| Magic | Likely type |
| --- | --- |
| `hsqs` | SquashFS |
| `19 85 20 03` | JFFS2 little-endian node magic |
| `1f 8b 08` | gzip |
| `fd 37 7a 58 5a` | xz |
| `7f 45 4c 46` | ELF |
| `UBI#` | UBI container |

Treat a magic hit as a hypothesis until the carved object parses correctly.

## Common Failure Modes

- Treating every binwalk hit as valid.
- Running deep recursive extraction before understanding the outer layout.
- Assuming high entropy means encrypted firmware.
- Searching only raw firmware strings after a filesystem can be extracted cleanly.
- Missing vendor wrapper/header bytes around a standard filesystem.
- Using the wrong filesystem extractor for a vendor-modified image.
- Forgetting that exact binwalk flags differ across versions.
- Recursing indefinitely through nested/circular extraction output.
- Jumping straight to a suspicious binary without preserving which firmware offset/filesystem/path produced it.
- Treating a full disk image or memory dump as firmware just because the extension is `.bin` or `.img`.

## Provenance

Canonical V2 consolidation of the original Apache-2.0 `performing-firmware-extraction-with-binwalk` skill and the former `ctf-reverse/firmware-extraction.md` handbook.

A 2026-09-05 duplicate audit preserved the legacy handbook's reusable practical depth here: ownership boundaries, version-aware binwalk usage, nested extraction discipline, manual carving, SquashFS/JFFS2/UBIFS tooling, post-extraction secret/service triage, magic-byte checks, and the extraction-to-native-RE handoff.

Challenge-specific "find the flag" shortcuts and redundant command variants were intentionally not copied. The untouched V1 source remains recoverable from `archive/pre-restructure-20260823` and Git history.
