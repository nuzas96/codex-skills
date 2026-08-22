# Artifact and Reverse-Engineering Chains

## Contents

- Nested document and container artifacts
- USB HID coordinate reconstruction
- Animated-image frame channels
- Packed binaries and anti-symbolic-execution patching
- Browser PRNG reproduction

## Nested Document and Container Artifacts

Treat an unusually large document as a carrier rather than a final format.

1. Compare declared type, magic bytes, file size, object count, and entropy.
2. Run `strings`, `pdfid`, `pdf-parser`, and `binwalk`; inspect repeated delimiters and long encoded blocks.
3. Extract encoded chunks in index order and verify decoded magic bytes before choosing a tool.
4. Treat passwords displayed or hidden in the document as keys for the next layer.
5. For SIF/Apptainer images, list objects, dump the filesystem object, then extract the resulting SquashFS.
6. Search metadata, deleted entries, environment files, and nonstandard flag locations after extraction.

Always record the chain of formats. A `.pdf` may contain base64, then ZIP, then SIF, then SquashFS.

## USB HID Coordinate Reconstruction

Mouse reports generally contain button state plus signed relative X/Y deltas. Determine the report layout from the descriptor or repeated packet shape rather than assuming offsets.

1. Extract interrupt-transfer payloads with `tshark`.
2. Decode deltas as signed values and cumulatively sum positions.
3. Apply the device's Y-axis convention.
4. Plot only segments where the primary button is pressed.
5. Test reflections, rotations, and scale normalization if the drawing looks inverted.
6. Pass recovered text through lightweight encodings such as ROT13 only when indicated by structure.

## Animated-Image Frame Channels

For APNG, GIF, or animated WebP, iterate all frames and inspect stable pixel positions and individual channels. A single coordinate's alpha or color value may encode one byte per frame.

```python
from PIL import Image

im = Image.open("challenge.png")
values = []
for i in range(getattr(im, "n_frames", 1)):
    im.seek(i)
    values.append(im.convert("RGBA").getpixel((0, 0))[3])
print(bytes(values))
```

Also test frame delays, disposal modes, palette indices, and XOR differences between frames.

## Packed Binaries and Anti-Symbolic-Execution Patching

When a binary is UPX-packed, unpack before deep analysis and confirm the result with `file`, section layout, and strings. If an otherwise straightforward validator randomly exits or mutates control flow, patch the nuisance branch before using angr.

Workflow:

1. Identify the input length, success address, and failure addresses.
2. Locate random or environment-dependent early exits.
3. Patch only the branch that introduces nondeterminism, preserving validation logic.
4. Run symbolic execution with constrained printable input and known flag prefix/suffix.
5. Revalidate the recovered candidate against the original binary across repeated runs.

Do not encode the expected flag into symbolic constraints beyond public format information.

## Browser PRNG Reproduction

For timed browser games driven by a server-provided seed:

1. Trace from the start-button handler to the network response and rendering routine.
2. Identify the state update, bit masking, modulo operation, and number of draws per level.
3. Reimplement JavaScript arithmetic exactly, including signed 32-bit coercions and operation order.
4. Verify the first few rendered values against the browser before automating answers.
5. Derive per-level draw counts from loops and animation schedules rather than manual counting.

JavaScript `&`, shifts, and multiplication can coerce differently from Python; mask to the correct width after each state transition.

Source basis: reusable abstractions from the DalCTF 2026 organizer writeups, <https://github.com/DalCTF/DalCTF2026>.
