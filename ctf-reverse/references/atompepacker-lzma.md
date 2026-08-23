# AtomPePacker `.ATOM` / LZMA Unpacking

Use this reference when a Windows PE appears to be a loader/stub and the real program is stored in an `.ATOM` section created by AtomPePacker.

## Recognize

Strong signals:

- PE32+ / x86-64 stub with a section named `.ATOM`;
- strings, symbols, PDB paths, or export metadata mention `PP64Stub.exe`, `H_PP64Stub.exe`, AtomPePacker, or EasyLZMA;
- `.ATOM` has high entropy and begins with a plausible LZMA-alone header;
- static analysis of the visible entry point mostly shows loader/decompression behavior instead of challenge semantics.

Do not assume every high-entropy PE section is AtomPePacker. Require a combination of section naming, stub metadata, and decompression validation.

## Primitive

AtomPePacker's x64 packer compresses the input PE with EasyLZMA using LZMA format and writes the compressed bytes into a newly created `.ATOM` PE section. The useful reverse-engineering move is therefore:

```text
packed PE
  -> identify `.ATOM`
  -> extract section raw bytes
  -> LZMA-alone decompress
  -> verify recovered `MZ` / `PE\0\0`
  -> restart normal reverse engineering on the recovered PE
```

This is usually cheaper and cleaner than instrumenting the loader or dumping memory at runtime.

## Fast workflow

```bash
file suspect.exe
objdump -h suspect.exe 2>/dev/null | grep -i ATOM
strings -a suspect.exe | grep -Ei 'PP64Stub|AtomPePacker|EasyLZMA|\.ATOM' | head
python3 ctf-reverse/scripts/unpack_atompepacker.py suspect.exe -o unpacked.exe
file unpacked.exe
```

After recovery, re-run strings/imports/symbols/decompiler analysis on `unpacked.exe`; do not keep reversing the packer stub unless loader behavior itself is the target.

## LZMA validation

LZMA-alone streams have a 13-byte header: properties, dictionary size, and uncompressed-size field. A common first byte such as `0x5d` is only a clue, not proof.

Validate by behavior:

1. decompression reaches end-of-stream;
2. recovered bytes start with `MZ`;
3. `e_lfanew` points inside the output;
4. the pointed signature is `PE\0\0`;
5. recovered imports/strings/control flow look like a coherent new program.

The PE section's `SizeOfRawData` can include alignment padding; use an LZMA decompressor that stops at the stream end and tolerates unused trailing bytes.

## Pitfalls

- Reversing only `PP64Stub.exe` and mistaking loader code for challenge logic.
- Carving from a guessed file offset instead of parsing the PE section table.
- Treating `0x5d` as a unique packer signature.
- Using generic raw-LZMA parameters when the section is an LZMA-alone stream.
- Forgetting to verify that decompressed output is actually a valid PE.
- Continuing dynamic instrumentation after a stable original PE has already been recovered offline.

## Source / provenance

General packer behavior verified against `killvxk/AtomPePacker-NUL0x4C`, especially `PePacker64/PePacker.c` and `PePacker64/easylzma.c` (Apache-2.0 repository), retrieved 2026-08-23. The packer calls `simpleCompress(ELZMA_lzma, ...)` and creates `.ATOM` containing the packed input PE.

Pattern independently confirmed while solving picoCTF 2026 `Binary Instrumentation 4` from the supplied artifact. Permanent knowledge intentionally excludes the challenge flag, validation key, network destination, hashes, and other one-off constants.
