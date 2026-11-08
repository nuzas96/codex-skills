# Free File Camouflage JPEG payloads

Use this reference when a JPEG is valid but has bytes after its end marker, especially when the tail is line-oriented Base64 or the artifact/hint names Free File Camouflage (FFC).

## Recognition and recovery

1. Preserve the original file and hash it. Locate JPEG EOI (`FF D9`) and inventory every byte afterward; do not assume image viewers expose the tail.
2. FFC 1.25 appends a second EOI marker, then CRLF-delimited Base64 records. The first record decrypts to version, MD5, and embedded filename metadata; following records are encrypted file chunks. The embedded name is untrusted metadata: choose a safe output path yourself.
3. Prefer the original FFC de-camouflage operation when available. For offline analysis, inspect the exact tool version and recover the format parameters from the binary; the version 1.25 default password is compiled into the application. Do not assume a custom-password container uses that default.
4. FFC 1.25 uses AES-CBC with PKCS#7 padding; its password bytes are padded with `=` to form a 32-byte AES key and a 16-byte IV. Each Base64 line is a separately encrypted record. Decrypt metadata first, then payload records, and validate the embedded MD5 to detect corruption. This unauthenticated MD5 does not establish provenance or authenticity.
5. Inspect the recovered object's magic and format. Treat executable payloads as untrusted code: static analysis first, then execute only in an offline resource-constrained sandbox with a minimal filesystem view.

The helper `../scripts/ffc_extract.py` parses this framing, accepts raw password bytes from a file, verifies metadata integrity, and writes only to a new explicit output path. It requires PyCryptodome. Run its tests with:

```sh
python3 ctf-forensics/scripts/test_ffc_extract.py
```

## Limits and false positives

- A duplicated EOI marker or Base64 tail alone does not prove FFC; confirm decrypted metadata structure and payload MD5.
- Version 1.25 details may not match later releases, custom password layouts, truncated files, or files transformed after camouflage.
- An organizer hint may be necessary: a technically correct workflow cannot infer every proprietary utility from ciphertext alone. Continue parallel structural analysis and clue checking rather than blindly guessing tool names.
- This is a format-specific forensic technique, not a general cipher break. Do not run an extracted executable merely because the writeup did.

## Provenance

- Challenge/writeup: CSAW Finals 2015 FOR300 Mandiant, https://github.com/hoppersroppers/ctfWriteups/blob/main/CSAW15/FOR300-Mandiant/readme.md (writeup states an organizer chat hint named Free File Camouflage).
- Software format/version: Free File Camouflage 1.25; https://www.myportablesoftware.com/freefilecamouflage.aspx (publisher URL currently unavailable), https://www.afterdawn.com/software/security/encryption/free_file_camouflage.cfm, and https://www.snapfiles.com/get/filecamo.html.
- Recovery behavior was confirmed by static inspection of the downloaded 1.25 .NET assembly and by two independent benign synthetic JPEG fixtures; the Mandiant outcome remains exposed postmortem evidence, not a fresh benchmark.
- No third-party source code or challenge-specific answer is included here.
