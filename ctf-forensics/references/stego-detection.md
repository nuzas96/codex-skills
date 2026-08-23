# Steganography Detection and Triage

Use when a media/document artifact may hide data in metadata, appended bytes, format structure, pixel/sample channels, frames, transforms or another covert representation.

## Layered Triage

Do the cheapest checks before assuming advanced steganography:

1. `file`, dimensions/duration, size sanity.
2. metadata with `exiftool`.
3. strings and known embedded magic/trailing data.
4. format-specific structure (`pngcheck`, JPEG markers, GIF/APNG frames, WAV chunks, etc.).
5. automated tools appropriate to the format.
6. only then custom bit/channel/signal analysis.

## Image Checks

### Appended / embedded data

Check bytes after logical end markers (for example JPEG `FFD9`) and nested archive/file magic. Validate extracted bytes by actual magic.

### PNG/BMP bit planes

`zsteg` is useful for common channel/bit-order patterns. Also inspect per-channel bit planes visually. Do not treat a near-50/50 LSB distribution as proof of stego; natural/compressed imagery can look random too.

### JPEG

JPEG stego may live in DCT coefficients, quantization tables, metadata, or trailing data rather than raw pixel LSBs. Use JPEG-specific tools when structure suggests it.

### Animated formats

GIF/APNG/WebP may encode data per frame through pixel/channel values, palette choices, timing or frame differences. Existing advanced stego references include one-byte-per-frame and APNG channel patterns.

## Audio / Signal

Check metadata/chunks first, then waveform/spectrogram, LSB/sample parity, DTMF/SSTV/modem-like tones, phase/frequency channels and timing. Use `signals-and-hardware.md` for UART, SSTV and more specialized signal reconstruction.

## Text / Document / Container Stego

Steganography is not limited to images. Existing references cover whitespace, Unicode/homoglyphs, SVG coordinates, PDF/object channels, spreadsheet structure, archives and terminal/control-code tricks.

## Passworded Stego Tools

If `steghide`/similar indicates embedded data but needs a password, derive candidate passwords from challenge evidence before brute force. Blank/common-word spraying should not replace clue analysis.

## Visualization and Extraction

When extracting bits manually, explicitly define:

- traversal order (row/column/frame);
- channel order;
- bit position;
- bit endianness;
- byte packing;
- expected marker/magic/flag prefix.

Change one dimension at a time so a successful configuration is explainable and reproducible.

## Common Failure Modes

- Running every stego tool against every format.
- Assuming image LSB is always the intended hiding method.
- Treating statistical randomness as positive evidence.
- Ignoring trailing bytes/metadata/container structure because the challenge says "stego".
- Losing track of channel/bit/endianness settings in custom scripts.
- Missing frame/timing channels in animated/video/audio artifacts.

## Provenance

Consolidated from the original `performing-steganography-detection` Apache-2.0 skill plus the repository's `steganography.md`, `stego-image.md`, `stego-advanced*.md` and signal references. Original source remains frozen on `archive/pre-restructure-20260823`.
