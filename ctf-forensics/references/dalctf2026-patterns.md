# DalCTF2026 — Forensics Patterns

Source: https://github.com/DalCTF/DalCTF2026

---

## 1. USB HID mouse packet capture → drawing → flag (forensics/wierd-movements)

**Pattern:** pcap captures USB traffic from a mouse drawing the flag character-by-character. Each interrupt transfer sends 3 bytes: `[buttons, dx, dy]`. Plot dx/dy cumulatively from (0,0) to reconstruct the drawing — the path spells out the flag.

**Extract with tshark:**
```bash
tshark -r capture.pcap -Y 'usb.transfer_type == 0x01 && usb.capdata' \
       -T fields -e usb.capdata > mouse_data.txt
```

**Parse the bytes (Python):**
```python
import struct
x = y = 0
with open("mouse_data.txt") as f:
    for line in f:
        raw = bytes.fromhex(line.replace(":", ""))
        buttons, dx, dy = raw[0], struct.unpack("b", raw[1:2])[0], struct.unpack("b", raw[2:3])[0]
        x += dx; y += dy
        # plot (x, y) — the path spells the flag
```

**Caveat:** byte order (little vs big endian) varies per mouse. If the picture looks mirrored or wildly off, swap byte order.

**Final step:** the drawn text is often wrapped in ROT13 / Base64 — apply after visual recovery.

---

## 2. PDF → base64 → zip → .sif → squashfs (forensics/warmerer_up)

**Pattern:** stacked-format challenge. PDF is the outermost container; inside its whitespace/comments is base64 wrapped in `@@N:<b64>@@`. Decodes to a password-protected zip → `.sif` (Singularity Image Format) container → squashfs filesystem with the flag.

**Detection:**
```bash
ls -lh rules.pdf            # unusually large for a "rules" PDF
strings rules.pdf | less    # big base64 blocks in @@N:...@@ pattern
```

**Extraction chain:**
```bash
# 1. Extract b64 chunks (regex on @@N:...@@), base64-decode → inside.zip
python3 - <<'PY'
import re, base64
data = open("rules.pdf","rb").read()
chunks = re.findall(rb"@@\d+:(.*?)@@", data, re.DOTALL)
open("inside.zip","wb").write(base64.b64decode(b"".join(chunks)))
PY

# 2. Crack / find zip password (often hidden in the PDF: last page, metadata, hidden text)
unzip -P 'teapot_2026' inside.zip

# 3. Work with .sif (Singularity/Apptainer)
apptainer sif list image.sif              # enumerate parts
apptainer sif dump 4 image.sif > out_fs   # id 4 is usually the squashfs
unsquashfs out_fs                          # extract files

# 4. Find the flag
find squashfs-root -name 'flag*'
```

**Stacked-format rule:** start outside-in. Watch for unusual file size, unusual content (`strings` shows big b64 blobs), unusual structure (`PK` magic or long uniform b64 alphabet blocks inside a "wrong format" file).

**Tools to have in toolbox:** `apptainer`/`singularity` for `.sif`, `unsquashfs` (from `squashfs-tools`), `7z`/`binwalk`/`foremost` for nested-format detection.
