# PDF Forensics and Embedded Content

Use when a CTF provides a PDF whose structure, objects, scripts, attachments, metadata, incremental revisions, or nested content may hide the answer.

## Triage

Start with structure before rendering:

- `file`, hash, size, `pdfinfo`;
- `pdfid.py` for suspicious/interesting keywords;
- `pdf-parser.py` or peepdf for objects/streams;
- `strings` and `binwalk` when the file is unusually large or clearly a carrier.

High-signal PDF names include `/JS`, `/JavaScript`, `/OpenAction`, `/AA`, `/Launch`, `/EmbeddedFile`, `/Filespec`, `/ObjStm`, `/AcroForm`, `/XFA`, and unusual filters/streams. In a CTF these are clues, not automatically malicious.

## Object Workflow

1. Enumerate objects and object tree.
2. Locate suspicious actions, streams, embedded files and annotations.
3. Decode filters rather than reading encoded stream bytes directly.
4. Extract JavaScript/attachments/large streams to separate files.
5. Identify magic bytes after decoding.
6. Recurse into nested formats.

peepdf interactive commands such as `tree`, `object`, `stream`, `rawstream`, and JS analysis are useful for targeted exploration.

## Incremental Revisions

PDFs can preserve earlier versions through incremental updates. If visible content looks clean but challenge wording suggests deletion/editing, inspect xref/trailer history and old object revisions rather than only the latest object value.

## Embedded / Nested Artifacts

Treat an unexpectedly large PDF as a possible container. Reusable chain pattern:

```text
PDF object/stream
 -> encoded blob
 -> archive/document/container
 -> filesystem/image
 -> flag artifact
```

Verify each decoded layer by magic bytes before choosing the next tool. Existing modern-chain artifact notes cover PDF -> base64 -> ZIP -> SIF -> SquashFS-style chains.

## JavaScript

Extract JS statically first. Deobfuscate in an isolated environment when needed. For a CTF, determine what the script computes/decodes/loads instead of assuming the goal is exploit-document malware analysis.

## Embedded Files

Follow `/EmbeddedFile` and `/Filespec` references; compare advertised filename/type with actual extracted magic. Attachments may be compressed or intentionally mislabeled.

## Common Failure Modes

- Opening the PDF visually and ignoring its object graph.
- Treating every `/JS` occurrence as the flag path.
- Forgetting incremental revisions/older objects.
- Running `binwalk` only and missing PDF-native embedded objects.
- Decoding a stream but not checking its true file type.
- Performing malware-style IOC reporting when the challenge simply needs nested artifact extraction.

## Provenance

Consolidated from the original `analyzing-malicious-pdf-with-peepdf` Apache-2.0 skill plus existing `ctf-forensics` PDF/container patterns. Original source remains frozen on `archive/pre-restructure-20260823`.
