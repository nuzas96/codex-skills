# Firmware Extraction and Reverse Triage

Use when a CTF supplies a firmware/blob/flash image whose embedded filesystem, kernel, bootloader, resources or executable components must be extracted before deeper reversing.

## Outside-In Workflow

1. Identify outer header/magic and size.
2. Run signature scan (`binwalk`) and inspect entropy only as a locator clue.
3. Extract recognized archives/filesystems.
4. Verify extracted magic independently.
5. Recurse only into meaningful nested components.
6. Once a root filesystem is available, map startup scripts, services, configs and target binaries.

## Binwalk

`binwalk` is a triage/extraction accelerator, not proof that every signature hit is real. False positives occur in compressed/high-entropy data. Validate offsets and extracted formats.

Useful modes include signature scanning, entropy visualization and recursive extraction. Avoid uncontrolled recursive extraction on a huge blob until you understand its main layout.

## Filesystem Families

Common embedded filesystems include SquashFS, CramFS, JFFS2 and UBIFS. Use their format-specific extractors (`unsquashfs`, Jefferson, etc.) and vendor-patched tools only when standard parsing proves incompatible.

## Manual Extraction

When auto-extraction fails but an offset/length is known, carve the region precisely and validate magic. Firmware headers, checksums or vendor wrappers may need to be separated from the embedded filesystem.

## What to Inspect After Extraction

For CTFs prioritize:

- `/etc` configs/startup scripts;
- web application/source;
- passwd/shadow only if relevant;
- certificates/keys/challenge secrets;
- service binaries and versions;
- custom daemons/binaries referenced by init scripts;
- device-specific config partitions.

If a native binary becomes the hard part, route it to `ghidra-native.md` or architecture-specific reverse notes.

## Entropy

High entropy can indicate compression or encryption; it does not distinguish them reliably. Combine entropy boundaries with magic, headers and code references.

## Common Failure Modes

- Treating every binwalk hit as valid.
- Running deep recursive extraction before understanding the outer layout.
- Assuming high entropy means encrypted firmware.
- Searching only raw firmware strings after a filesystem can be extracted cleanly.
- Missing vendor wrapper/header offsets around a standard filesystem.

## Provenance

Consolidated from the original Apache-2.0 `performing-firmware-extraction-with-binwalk` skill and existing `ctf-reverse/firmware-extraction.md` material. Original source remains on `archive/pre-restructure-20260823`.
