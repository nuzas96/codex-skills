# File Carving and Raw Recovery

Use when filesystem metadata is missing/corrupt, the challenge gives raw unallocated space, or deleted/embedded files must be recovered by signatures rather than directory entries.

## First Decide: Filesystem Recovery or Carving?

Prefer filesystem-aware tools (`fls`, `icat`, filesystem-specific recovery) when metadata still exists because they preserve exact extents, names and fragmentation. Use carving when metadata is unavailable or as a complementary pass.

## Foremost / Scalpel Workflow

1. Identify the image/container and partition offsets.
2. If useful, extract unallocated space with a filesystem-aware tool such as `blkls`.
3. Carve only likely file types first; `-t all` can create huge noisy output.
4. Review Foremost's `audit.txt` for offsets/sizes.
5. Validate carved results by magic/type and parse them with format-aware tools.
6. Record the source offset for any flag-bearing artifact.

## Signature Caveats

Header/footer carving assumes enough contiguous data and recognizable boundaries. It can fail or create false positives when:

- files are fragmented;
- common signatures occur inside unrelated data;
- the format lacks a strong footer/length;
- archives share magic (`PK`) but represent many application formats;
- challenge intentionally corrupts headers.

For custom signatures, derive the **actual** format header/footer and realistic maximum size. Do not label every ZIP as DOCX/XLSX/PPTX from magic alone.

## Beyond Foremost

Use `binwalk`, `scalpel`, raw `grep`/Python, archive-header parsers, or format-specific repair when the standard carver misses the artifact. Existing `disk-recovery.md` covers corrupted ZIP local-header extraction, anti-carving, nested filesystems and similar CTF cases.

## CTF Pattern: Known Header Damaged

If `file` reports `data` but challenge context suggests a known format, compare the first bytes with expected magic. XOR/byte corruption or shifted headers may need repair **before** carving tools can recognize the content.

## Validate, Don't Trust Extensions

For every carved file:

- run `file`/magic check;
- inspect header/trailer;
- use parser validation (`pngcheck`, archive tools, PDF tools, etc.);
- deduplicate hashes when a carver emits repeated overlapping files.

## Common Failure Modes

- Running `foremost -t all` first and drowning in thousands of false positives.
- Carving a deleted file that filesystem metadata could recover exactly.
- Assuming contiguous carving works on fragmented files.
- Trusting the output extension instead of magic/parser validation.
- Losing the source offset, making later reconstruction harder.

## Provenance

Consolidated from the original `performing-file-carving-with-foremost` Apache-2.0 skill and `ctf-forensics/disk-recovery.md`. Original source remains frozen on `archive/pre-restructure-20260823`.
