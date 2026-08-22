# CTF Reverse - Firmware Extraction with Binwalk

Companion to `patterns-ctf-3.md#esp32xtensa-firmware-reversing` (which covers architecture-level firmware RE) and `platforms-hardware.md` (architecture context). **This file is the extraction step** — when you have a firmware blob and need to find embedded filesystems, credentials, and configuration before doing any RE on the contents.

**Use this when:**
- A challenge gives you `firmware.bin`, `update.img`, `*.hex`, or a flash dump
- The blob is large (1-50MB) and you need to find what filesystem is inside
- You're looking for hardcoded credentials, API keys, certificates, or flag strings
- You need to mount an extracted filesystem to inspect its contents

## When NOT to Use

- Plain Linux ELF binary (not firmware) — use `tools.md` for normal binary RE
- Disk image of a full OS (`*.dmg`, `*.img` with partition table) — use `ctf-forensics/disk-and-memory.md`
- Memory dump — use `ctf-forensics/disk-and-memory.md` (Volatility)

## Prerequisites

```bash
# binwalk v3 (not v2 — many CTFs target v2 bugs)
pip install binwalk3
# or: apt install binwalk  # Usually v2 on Kali, but still works for most cases

# Filesystem extraction
apt install squashfs-tools  # unsquashfs for SquashFS
pip install jefferson       # JFFS2 extraction
# sasquatch — for non-standard vendor SquashFS variants (TP-Link, D-Link)
git clone https://github.com/nneonneo/sasquatch.git && cd sasquatch && make

# Standard tools
apt install binutils  # strings
```

## Workflow

### 1. Initial Signature Scan

```bash
# Identify embedded file types and their offsets
binwalk firmware.bin

# Verbose — shows confidence levels
binwalk -v firmware.bin

# Filter to specific types
binwalk -y "squashfs" firmware.bin
binwalk -y "gzip\|lzma\|xz\|zstd" firmware.bin

# Detect CPU architecture (look for ELF magic inside)
binwalk -A firmware.bin

# String scan for hints (version, URLs, credentials)
binwalk -R "password\|admin\|flag\|http" firmware.bin
```

Typical output looks like:
```
DECIMAL       HEXADECIMAL     DESCRIPTION
0             0x0             U-Boot bootloader header
512           0x200           LZMA compressed data
327680        0x50000         SquashFS filesystem v4.0, LZMA compressed
4194304       0x400000        JFFS2 filesystem
```

### 2. Entropy Analysis (Find Encrypted Regions)

```bash
# Generate entropy plot
binwalk -E firmware.bin

# Higher resolution — smaller blocks
binwalk -E -K 256 firmware.bin

# Combined entropy + signature
binwalk -BE firmware.bin
```

**Interpreting entropy:**
| Range | Meaning |
| ----- | ------- |
| 0.0 - 1.0 | Empty / padding (nulls or 0xFF) |
| 1.0 - 5.0 | Plaintext, code, ASCII strings, config |
| 5.0 - 7.0 | Compressed (gzip, LZMA, zlib) |
| 7.0 - 7.99 | Strongly compressed or encrypted |
| ~8.0 | Fully encrypted or random data |

**High entropy region in the middle of otherwise plaintext firmware = encrypted config block.** Look for the key elsewhere (bootloader, default password, hardware ID derivation).

### 3. Recursive Extraction (Matryoshka)

```bash
# Single-level extraction
binwalk -e firmware.bin
# Output: _firmware.bin.extracted/

# Recursive (extracts nested archives/filesystems)
binwalk -Me firmware.bin
# -d N limits depth
binwalk -Me -d 5 firmware.bin

# Extract specific type with custom handler (e.g. for vendor-modified SquashFS)
binwalk -D "squashfs filesystem:squashfs:unsquashfs %e" firmware.bin
```

### 4. Manual Extraction (When Auto Fails)

```bash
# Extract at known offset (from binwalk signature scan)
dd if=firmware.bin of=rootfs.squashfs bs=1 skip=327680 count=4194304

# Or carve a range based on entropy plot
dd if=firmware.bin of=blob.bin bs=1 skip=$((0x50000)) count=$((0x400000 - 0x50000))
```

### 5. Mount Extracted Filesystems

```bash
# SquashFS (most common in router/IoT firmware)
mkdir /tmp/rootfs
unsquashfs -d /tmp/rootfs rootfs.squashfs
# If "non-standard" error: try sasquatch instead
sasquash -d /tmp/rootfs rootfs.squashfs

# CramFS
mkdir /tmp/cramfs
mount -t cramfs -o loop rootfs.cramfs /tmp/cramfs

# JFFS2 (NOR/NAND flash)
mkdir /tmp/jffs2
jefferson rootfs.jffs2 -d /tmp/jffs2

# UBIFS (modern NAND)
apt install mtd-utils
ubireader_extract_images rootfs.ubi  # Extracts to .img files
```

### 6. Find Credentials and Secrets

```bash
# All printable strings
strings -a firmware.bin > all_strings.txt
strings -n 12 firmware.bin | sort -u > long_strings.txt

# In extracted filesystem
grep -rni "password\|passwd\|secret\|api_key\|token" /tmp/rootfs/etc/
grep -rni "BEGIN.*PRIVATE KEY" /tmp/rootfs/

# Hardcoded URLs / endpoints
grep -rnoE "https?://[a-zA-Z0-9./?=_-]+" /tmp/rootfs/

# Certificates and keys
find /tmp/rootfs -name "*.pem" -o -name "*.crt" -o -name "*.key" -o -name "*.p12"

# Default credentials — common files
cat /tmp/rootfs/etc/passwd
cat /tmp/rootfs/etc/shadow        # If extracted
cat /tmp/rootfs/etc/httpd.conf    # Web admin default creds often here

# Service versions (for CVE lookup)
strings /tmp/rootfs/bin/busybox | grep "BusyBox v"
strings /tmp/rootfs/usr/sbin/dropbear | grep -i version
```

### 7. Find the Flag

CTF-specific tactics:

```bash
# 1. Plaintext flag in config
strings -a firmware.bin | grep -iE 'flag\{|ctf\{|FLAG|HTB\{'

# 2. Web admin panel — flag in /etc/ or hidden admin page
find /tmp/rootfs -name "*.html" -o -name "*.cgi" -o -name "*.php"
grep -rni "flag\|admin" /tmp/rootfs/www/ 2>/dev/null

# 3. Build info / version banners
strings firmware.bin | grep -iE "version\|build\|copyright"
cat /tmp/rootfs/etc/banner 2>/dev/null

# 4. Hidden files / odd permissions
find /tmp/rootfs -perm -4000     # SUID binaries
find /tmp/rootfs -name ".*"      # Hidden files
find /tmp/rootfs -size +1M       # Large files (could be encrypted blobs)

# 5. Decompile the interesting binary
# Once you find the suspicious binary in /tmp/rootfs/bin or /usr/sbin, 
# copy it out and use normal ctf-reverse workflow:
file /tmp/rootfs/usr/bin/suspicious
# (goes through ctf-reverse/SKILL.md from here)
```

## Common CTF Scenarios

1. **Find flag in extracted config** — Plaintext `flag{...}` in `/etc/config/wireless` or `/etc/shadow`
2. **Decompile extracted binary** — `binwalk -e` gives you the firmware, mount gives you `/usr/bin/flagcheck`, reverse that
3. **Crack extracted hash** — `/etc/shadow` has a hash, use hashcat with the right mode
4. **Decrypt extracted config** — High-entropy region contains encrypted config, key is in bootloader (also extracted)
5. **Chained** — `binwalk -e` → `unsquashfs` → `find . -name "flag*"` → cat the file

## Pitfalls

- **Wrong SquashFS tool** — Vendor firmware often uses non-standard compression. Try `sasquatch` if `unsquashfs` fails.
- **Encrypted firmware** — If the whole thing has entropy ~8, you need a decryption key from elsewhere (bootloader, public CVE exploit, default password derivation).
- **Magic offset is wrong** — If the embedded filesystem has a custom header, binwalk may miss it. Try `binwalk -y` for a specific type, or manually scan for known magic bytes with `xxd | head`.
- **Recursive extraction loops** — If you have circular embedded data, limit depth with `-d 5`.
- **Obfuscated credentials** — Plain `grep password` won't find XOR'd or Base64'd strings. Use entropy analysis to find data blobs, then try common decodings.

## Quick Reference: Common Magic Bytes

| Magic | File type | Tool to extract |
| ----- | --------- | --------------- |
| `hsqs` | SquashFS | `unsquashfs` / `sasquash` |
| `0x28 0xCD 0x3D 0x45` | CramFS | `mount -t cramfs` |
| `0x19 0x85 0x20 0x03` | JFFS2 (LE) | `jefferson` |
| `0x1F 0x8B 0x08` | gzip | `gunzip` |
| `0x5D 0x00 0x00` | LZMA | `xz -d` or `lzma -d` |
| `0xFD 0x37 0x7A 0x58 0x5A` | xz | `xz -d` |
| `UBI#` | UBIFS | `ubireader_extract_images` |
| `0x7F ELF` | ELF binary | Normal RE workflow |
| `CrAU` | Android update | `imgpatch` (different workflow) |

## See Also

- `ctf-forensics/disk-and-memory.md` — disk image forensics (different from firmware blob)
- `ctf-forensics/disk-recovery.md` — has `binwalk -e` examples for stego chains
- `patterns-ctf-3.md#esp32xtensa-firmware-reversing` — once you've extracted and need to RE the contents
- `tools-advanced.md` — Ghidra for the extracted binaries
