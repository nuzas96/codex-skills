# Office Document Forensics: Encrypted OOXML and Static VBA Analysis

Use this reference when the primary artifact is a Microsoft Office document or Office-derived container and the task is to **recover, inspect, or reconstruct evidence without executing the document**.

Two recurring CTF patterns:

```text
encrypted Office wrapper
  -> recover password
  -> decrypt to normal OOXML
  -> inspect document.xml / embedded content
  -> decode extracted clue

DOCM / macro-enabled OOXML
  -> inspect container statically
  -> extract VBA
  -> separate decoy macro noise from intended data
  -> reconstruct hidden values/comments
  -> pivot to crypto/encoding only after artifact extraction is proven
```

## Recognition signals

- `.docx`, `.docm`, `.xlsx`, `.xlsm`, `.pptx`, `.pptm`;
- `file` reports `CDFV2 Encrypted` instead of a normal ZIP/OOXML document;
- `office2john.py` is needed to extract a password hash;
- `msoffcrypto` / `msoffcrypto-tool` is needed to decrypt the document;
- `word/document.xml`, `word/vbaProject.bin`, `xl/vbaProject.bin`, or similar OOXML members;
- macro-enabled Office files containing suspicious VBA, EICAR text, shellcode-like arrays, fake warnings, or noisy decoy code;
- useful ciphertext, fragments, comments, or encodings are hidden in document XML or VBA source rather than the rendered page.

## 1. Preserve and identify before opening

```bash
sha256sum artifact*
file artifact*
xxd -l 64 artifact
```

Do not trust the extension alone. A normal OOXML document is ZIP-based. An encrypted modern Office document may instead appear as an OLE/Compound File wrapper such as `CDFV2 Encrypted`.

Do not execute macros or enable active content merely to inspect the file. Prefer container inspection and static extraction first.

## 2. Branch A: encrypted Office document

### 2.1 Extract the password hash

```bash
office2john.py protected.docx > office.hash
head office.hash
```

### 2.2 Crack with the evidence-supported wordlist

```bash
john office.hash --wordlist=wordlist.txt
john --show office.hash
```

Record the hash file, wordlist source, recovered password, and whether the password is actually accepted. A cracking result is not the final proof; successful decryption is.

### 2.3 Decrypt to a separate output

```python
import msoffcrypto

password = "RECOVERED_PASSWORD"

with open("protected.docx", "rb") as src:
    office = msoffcrypto.OfficeFile(src)
    office.load_key(password=password)
    with open("decrypted.docx", "wb") as dst:
        office.decrypt(dst)
```

Then verify:

```bash
file decrypted.docx
sha256sum decrypted.docx
unzip -t decrypted.docx
```

A successfully decrypted DOCX should now behave like a normal OOXML ZIP container.

## 3. Inspect OOXML as a filesystem, not a rendered page

```bash
unzip -l decrypted.docx | less
zipinfo -1 decrypted.docx
```

Common high-value locations:

```text
word/document.xml
word/comments.xml
word/footnotes.xml
word/endnotes.xml
word/_rels/
word/media/
word/embeddings/
word/vbaProject.bin

xl/worksheets/
xl/sharedStrings.xml
xl/vbaProject.bin

ppt/slides/
ppt/notesSlides/
ppt/vbaProject.bin
```

Extract to a working directory:

```bash
mkdir -p office_extract
unzip -q decrypted.docx -d office_extract
```

Preserve the chain: original artifact -> decrypted artifact -> OOXML member -> extracted text/macro/object -> decoded clue.

## 4. Extract Word XML text

For Word, the main document text commonly resides in `word/document.xml`.

```python
from pathlib import Path
import xml.etree.ElementTree as ET

path = Path("office_extract/word/document.xml")
root = ET.fromstring(path.read_bytes())
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

parts = []
for node in root.findall(".//w:t", NS):
    if node.text:
        parts.append(node.text)

print("".join(parts))
```

Also inspect comments, headers/footers, alt text, embedded objects, relationship targets, custom XML, and unusual Unicode/symbol alphabets. Once text is extracted, treat the next transform as a separate encoding/crypto layer.

## 5. Branch B: macro-enabled Office document

A `.docm` or other macro-enabled OOXML document is still a ZIP container.

```bash
file sample.docm
sha256sum sample.docm
unzip -l sample.docm | less
```

For Word macro documents, two especially important members are:

```text
word/document.xml
word/vbaProject.bin
```

## 6. Extract VBA statically

```bash
olevba sample.docm > vba.txt
less vba.txt
```

Programmatically:

```python
from oletools.olevba import VBA_Parser

parser = VBA_Parser("sample.docm")
try:
    source = "\n".join(
        macro_source
        for _, _, _, macro_source in parser.extract_macros()
    )
finally:
    parser.close()

print(source)
```

Optional supporting triage:

```bash
oleid sample.docm
strings -a office_extract/word/vbaProject.bin | less
```

Static extraction gives macro source without executing the document.

## 7. Do not assume the scariest macro is the intended path

Office CTFs may contain deliberate noise: fake antivirus/security warnings, EICAR strings, large byte arrays, shellcode-like VBA, suspicious API calls, dead code, or unused variables.

Trace references and data flow before deciding which content matters. A useful evidence question is: does this artifact participate in producing the challenge-relevant value?

## 8. VBA comments can carry the intended payload

If commented lines contain symbol assignments and expressions, do not discard them merely because they are inactive VBA.

```text
' A = 'X'
' B = 'Y'
' part1 = A+B+B
```

Generic parser shape:

```python
import re

symbols = dict(
    re.findall(r"(?m)^'\s*([A-Z])\s*=\s*'([^']+)'", source)
)

def resolve(expr: str) -> str:
    return "".join(symbols[name] for name in expr.split("+"))
```

Preserve source line -> symbol assignment -> expression -> reconstructed fragment -> combined ciphertext/clue. This is stronger than manually copying the final string.

## 9. Separate extraction from cryptanalysis

Examples:

```text
VBA comments -> ciphertext -> Vigenere
document.xml -> symbol alphabet -> substitution decode
embedded blob -> PE/ELF -> reverse engineering
```

Routing:

- simple alphabet/Base-N/Unicode encoding -> `ctf-misc/encodings*.md`;
- Vigenere/classical cipher -> `ctf-crypto/classic-ciphers.md`;
- recovered native binary -> `ctf-reverse`;
- malicious macro behavior/C2 becomes the objective -> `ctf-malware`.

Keep this reference responsible for Office artifact recovery and provenance, not every downstream transform.

## 10. Reusable workflow

```text
hash + file
  -> encrypted OLE/CDFV2 or normal OOXML?
     -> encrypted:
          office2john
          -> evidence-supported wordlist
          -> verify password by decrypting
          -> normal OOXML
     -> normal OOXML/DOCM:
          list ZIP members
          -> document.xml / comments / media / embeddings
          -> vbaProject.bin if present
          -> olevba static extraction
          -> trace active and commented data
  -> reconstruct intended clue
  -> validate
  -> pivot category only if the hard primitive changes
```

## 11. Validation checklist

- [ ] original artifact hash recorded;
- [ ] actual container type identified;
- [ ] password crack validated by successful decryption;
- [ ] decrypted artifact saved separately;
- [ ] decrypted/OOXML artifact passes `file` and ZIP validation;
- [ ] relevant XML/VBA member path recorded;
- [ ] macros inspected statically before execution;
- [ ] decoy-looking macro content separated from proven data flow;
- [ ] commented VBA content considered as evidence;
- [ ] reconstruction reproducible from source lines;
- [ ] downstream cipher/encoding routed separately;
- [ ] final value traced back to a specific Office member.

## 12. Common failure modes

- Trusting the Office extension instead of actual magic/container type.
- Trying to unzip an encrypted Office wrapper before decrypting it.
- Treating the cracked password as proof without verifying decryption.
- Opening a macro document interactively before static extraction.
- Reading only the rendered page and ignoring OOXML members.
- Ignoring comments because they are not executable VBA.
- Chasing EICAR/shellcode-like decoys without proving they affect intended data flow.
- Copying ciphertext manually instead of preserving symbol/expression reconstruction.
- Mixing Office extraction and downstream cryptanalysis into one opaque solver.
- Forgetting to hash decrypted/extracted artifacts.

## Provenance

Generalized from the user-supplied P4KT4M Bahtera Siber writeups for **Risalah Istana Anak Bukit** and **Surat Pertabalan**, studied 2026-09-05. Challenge-specific URLs, passwords, ciphertexts, keys and flags are intentionally excluded.