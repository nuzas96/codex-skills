# ASCII-art and terminal-text recovery

Use this reference when a recovered text file, decrypted payload, terminal capture, or image contains monospaced glyph art rather than ordinary prose.

## Preserve and classify first

- Keep the original bytes unchanged. Record line endings, blank rows, leading/trailing spaces, tabs, control sequences, and non-ASCII bytes before rendering or normalization.
- Confirm the decoded payload is actually printable, line-oriented art. Do not infer that all readable-looking plaintext is the answer; inspect for another encoding, hidden channel, or nested object when structure or prompt evidence suggests one.
- Separate the verbatim transcript, a visual reading, and any proposed answer. Mark uncertain glyphs and delimiters explicitly.
- Ordinary `strings`, regex flag scans, and OCR are not reliable on FIGlet sub-glyph art. Tesseract is intended for raster text; a clean OCR exit status does not mean the recognized text is correct.

## Read a FIGlet-style banner

FIGlet glyphs are assembled from smaller screen characters and fonts can kern or smush adjacent characters. If the payload resembles a FIGfont banner, first read it in a fixed-width display and preserve every row. Test the proposed transcription by rendering it with a plausible font and comparing the result with the preserved artifact:

```bash
pyfiglet --list_fonts
pyfiglet -f <font> -w 1000 '<candidate text>' > /tmp/candidate-banner.txt
diff -u recovered-banner.txt /tmp/candidate-banner.txt
```

An exact row match validates that candidate under that font and renderer. A mismatch does not identify which character is wrong: check the font, layout/smushing mode, width, line endings, and transcription separately. Do not trim spaces from the source artifact; use any normalized comparison only as a second view and retain the byte-exact original.

For actual raster screenshots of rendered text, Tesseract can provide a separate transcription. Select page segmentation appropriate to the image (for example, a single text block or line), preserve its raw output, and compare against visual and structural evidence. Treat OCR as a hypothesis, especially for braces, underscores, punctuation, and low-resolution glyphs.

## Derive and verify the answer

- Use the challenge prompt, public format instructions, source behavior, and artifact bytes to determine delimiters and exact spelling.
- Do not add a familiar `prefix{...}` wrapper, replace spaces with underscores, change case, or append punctuation unless evidence specifies that transformation. A plausible wrapper is not evidence.
- When a verifier rejects a candidate, mark it disproven. Revisit the exact prefix, braces, separators, whitespace, and whether the artwork contains additional text; do not keep resubmitting normalization variants without new evidence.
- Submit only a candidate supported by the recovered representation and the challenge's stated format. Controller verification is authoritative; a visual reading or successful re-render is evidence about transcription, not independent flag verification.

## Tool notes and provenance

- `figlet` and the Python `pyfiglet` package render FIGfonts. Candidate re-render comparison was tested on three benign strings across the `small`, `slant`, and `standard` fonts with `pyfiglet` 1.0.3 and the system FIGlet CLI; exact text/font reconstructions matched, while deliberately wrong-font comparisons differed. The benign corpus also showed that OCR and literal flag scans can fail on rendered glyph art.
- Tesseract is useful for raster text with suitable segmentation, not as an oracle for FIGlet sub-glyph bytes. Its output must be checked against the image.
- A CTF Racer development Crypto run (2026-10-29) recovered and round-trip-validated a banner but had a candidate rejected after inventing a wrapper despite no supplied format. This supports the exact-format discipline above; the challenge, banner, and answer are intentionally omitted.
- A separate public VuwCTF 2026 Forensics write-up describes decoding a custom RLE stream to a FIGlet banner and confirming a transcription by re-rendering. It is a secondary write-up, not a format specification: [write-up](https://cybersecurityelite.com/ctf-writeups/vuwctf-2026-forensics-writeup/). Accessed 2026-10-29; no challenge code or answer copied.
- [FIGlet man page](https://manpages.debian.org/trixie/figlet/figlet.6.en.html) documents FIGfont behavior, fonts, and kerning/smushing. [pyfiglet](https://github.com/pwaller/pyfiglet) provides a Python and CLI renderer and is MIT-licensed. [Tesseract user manual](https://tesseract-ocr.github.io/tessdoc/) documents its OCR interface and Apache-2.0 license.
