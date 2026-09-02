# RDP Persistent Bitmap Cache Reconstruction

Use this reference when a Windows forensic image belongs to an RDP **client** and the sought visual content was displayed from another host. The original file may never have existed on the examined machine, yet the client can retain fragments of the remote screen inside persistent bitmap-cache files.

This is a forensic reconstruction problem, not image steganography.

## Recognition signals

Strong signals include:

- Remote Desktop / RDP activity is part of the challenge narrative or evidence;
- the examined workstation is the **viewer/client**, not the machine that originally stored the secret image/document;
- `.rdp` configuration contains persistent bitmap caching, for example a setting equivalent to `bitmapcachepersistenable:i:1`;
- files named like `Cache0000.bin`, `Cache0001.bin`, or other RDP bitmap-cache containers are present;
- parser output produces many small bitmap tiles rather than one full screenshot;
- cleanup/deletion happened on the remote host, but the client still contains graphical residue;
- the missing data was visible on screen even though it was never saved locally.

Fast route:

```text
RDP client evidence
  -> confirm persistent bitmap caching
  -> locate Cache*.bin
  -> extract cached bitmap entries
  -> inventory dimensions/content
  -> build contact sheets
  -> cluster likely tiles
  -> reconstruct by edge/content continuity
  -> validate recovered visual/text evidence
```

## Core forensic insight

Do not assume that a file must have existed on the imaged system for its **visual representation** to survive there.

Remote-display protocols may cache rendered screen regions locally for performance. Therefore:

```text
remote file exists only on server
        |
        v
rendered over RDP
        |
        v
client caches bitmap regions
        |
        v
server file deleted / never copied locally
        |
        v
visual fragments still recoverable on client
```

This changes the first question from:

> Where is the deleted image on disk?

to:

> Which local application artifacts could have retained what the user saw?

## 1. Establish client/server roles first

Before carving anything, write down:

- which host was the RDP client;
- which host was the RDP server;
- which host originally stored the target file;
- which host the forensic image came from;
- whether the target was merely viewed, edited, copied, downloaded, or printed.

A client-side image can be decisive even when the target file belonged only to the remote server.

Record the inference in `PROGRESS.md`:

```text
Observed:
- target content was displayed through RDP
- forensic image is from the client workstation
- target file is absent locally

Hypothesis:
- rendered content may survive in persistent RDP bitmap cache

Smallest discriminating test:
- locate RDP cache settings and Cache*.bin files
```

## 2. Confirm persistent bitmap caching

Look for RDP configuration/session evidence showing that persistent bitmap caching was enabled.

A setting equivalent to:

```text
bitmapcachepersistenable:i:1
```

is high-value evidence because it directly supports the hypothesis that rendered screen fragments could remain on disk after the session.

Do not treat the setting alone as proof that the target image is recoverable. It proves only that this artifact family is worth inspecting.

Corroborate with other RDP evidence when available:

- saved `.rdp` files;
- recent RDP destination/history artifacts;
- event logs;
- Jump Lists/LNKs;
- Prefetch/application execution evidence;
- timestamps around the suspected session;
- cleanup activity after the session.

Keep provenance separate from visual reconstruction: one artifact may prove **the session happened**, while the bitmap cache proves **what appeared on screen**.

## 3. Locate cache containers

Search the extracted Windows profile/filesystem for likely cache files:

```bash
find . -type f \( -iname 'Cache*.bin' -o -iname '*bitmap*cache*' \) -print
```

If working from a mounted forensic image, preserve original paths and timestamps in notes before copying the cache files into a working directory.

Useful inventory:

```bash
mkdir -p work/rdp-cache
cp /path/to/Cache*.bin work/rdp-cache/ 2>/dev/null || true
sha256sum work/rdp-cache/*
file work/rdp-cache/*
ls -lh work/rdp-cache/
```

Multiple cache containers are normal. One file can be nearly useless while another contains the relevant visual fragments, so process **all plausible caches** before concluding nothing survived.

## 4. Parse with an RDP bitmap-cache aware tool

A generic strings/carving pass is not enough because the containers have application-specific record structure.

Use a parser designed for RDP persistent bitmap caches, such as ANSSI-FR `bmc-tools`, or another implementation that understands the exact cache format.

Because CLI flags can differ by tool/version, confirm the installed syntax rather than copying an old command blindly:

```bash
python3 bmc-tools.py --help
```

Then extract each cache independently into its own output directory and record the exact command in `PROGRESS.md`.

Conceptually:

```text
Cache0000.bin -> out/cache0/<bitmap tiles>
Cache0001.bin -> out/cache1/<bitmap tiles>
...
```

For each extraction, record:

- source cache filename and hash;
- parser/tool version or commit when practical;
- number of recovered entries;
- image dimensions;
- output format;
- parse warnings/errors.

If one cache produces hundreds of small images, that is expected behavior, not extraction failure.

## 5. Inventory the extracted tiles

Do not open hundreds of files one by one first.

Start with counts and dimensions:

```bash
find out -type f | wc -l
find out -type f | head
```

If ImageMagick is available:

```bash
identify out/**/* 2>/dev/null | head -100
```

Or summarize with Python/Pillow:

```python
from pathlib import Path
from collections import Counter
from PIL import Image

root = Path('out')
counts = Counter()
valid = 0

for p in root.rglob('*'):
    if not p.is_file():
        continue
    try:
        with Image.open(p) as im:
            counts[im.size] += 1
            valid += 1
    except Exception:
        pass

print('images:', valid)
for size, n in counts.most_common():
    print(size, n)
```

Repeated fixed-size tiles, commonly small rectangles/squares, are a strong sign that the screen must be reconstructed from fragments rather than recovered as one normal image.

## 6. Build contact sheets immediately

A contact sheet converts hundreds of isolated tiles into one searchable visual surface.

With ImageMagick, adapt the glob to the parser output:

```bash
montage out/cache1/* \
  -thumbnail 96x96 \
  -tile 12x \
  -geometry +2+2 \
  contact-cache1.png
```

Or use a small Pillow helper:

```python
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import math

paths = []
for p in Path('out/cache1').glob('*'):
    if not p.is_file():
        continue
    try:
        with Image.open(p) as im:
            im.verify()
        paths.append(p)
    except Exception:
        pass

thumb = 96
label_h = 18
cols = 10
rows = math.ceil(len(paths) / cols)
canvas = Image.new('RGB', (cols*thumb, rows*(thumb+label_h)), 'white')
d = ImageDraw.Draw(canvas)

for i, p in enumerate(paths):
    with Image.open(p).convert('RGB') as im:
        im.thumbnail((thumb, thumb))
        x = (i % cols) * thumb
        y = (i // cols) * (thumb + label_h)
        tile = Image.new('RGB', (thumb, thumb), 'black')
        tile.paste(im, ((thumb-im.width)//2, (thumb-im.height)//2))
        canvas.paste(tile, (x, y))
        d.text((x, y+thumb), p.stem[-12:], fill='black')

canvas.save('contact-cache1.png')
```

Label entries. A beautiful contact sheet without filenames/IDs makes later reconstruction harder because you cannot map interesting tiles back to the cache records.

## 7. Triage tiles by information value

Most cache entries can be irrelevant UI chrome, flat backgrounds, icons, window borders, or unrelated session content.

Prioritize tiles containing:

- text strokes;
- high-contrast document regions;
- distinctive borders;
- portions of logos/seals/forms;
- unusual colors/backgrounds matching the target;
- repeated baselines or line spacing;
- fragments that obviously continue into adjacent tiles.

A useful workflow:

```text
all tiles
 -> contact sheet
 -> shortlist visually relevant IDs
 -> copy shortlist to candidate/
 -> reconstruct only the candidate cluster
```

Example:

```bash
mkdir -p candidate
cp out/cache1/<interesting-ids> candidate/
```

Do not discard apparently blank tiles too early. A nearly uniform tile can contain the spacing/border needed to establish adjacency.

## 8. Understand what cache order does NOT guarantee

Persistent bitmap caches are optimization artifacts, not screenshot archives.

The cache entry index usually should **not** be treated as a guaranteed `(x,y)` position on the original screen.

Do not assume:

```text
entry 0 = top-left
entry 1 = next tile right
entry 2 = next tile right
...
```

The same region can be cached/reused at different times, and screen content can span multiple application states.

Use ordering/timestamps only as weak hints unless the exact cache implementation proves stronger semantics.

The reconstruction problem is therefore often closer to a jigsaw puzzle than a raw framebuffer dump.

## 9. Manual adjacency criteria

When the relevant set is small, manual reconstruction is often faster and more reliable than building a sophisticated optimizer.

Compare candidate neighbors using:

### Character/text continuity

- letter strokes crossing tile boundaries;
- aligned text baselines;
- matching font weight/anti-aliasing;
- word fragments that form plausible strings.

### Background continuity

- same flat background color;
- same gradient direction;
- same texture/noise;
- same document/window region.

### Horizontal/vertical edge continuity

- line/border continues exactly;
- anti-aliased pixels line up;
- shapes continue at the same height/column.

### Neighboring pixel boundaries

For two tiles `A` and `B`, compare:

```text
A right edge <-> B left edge
A bottom edge <-> B top edge
```

Low pixel difference is a useful ranking signal, but it is not proof. Flat-color UI tiles can create many false matches.

## 10. Edge-distance scoring

For a larger candidate set, rank potential neighbors programmatically.

```python
from PIL import Image
import numpy as np

def arr(path):
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.int16)

def right_left(a, b):
    A, B = arr(a), arr(b)
    h = min(A.shape[0], B.shape[0])
    return np.abs(A[:h, -1, :] - B[:h, 0, :]).mean()

def bottom_top(a, b):
    A, B = arr(a), arr(b)
    w = min(A.shape[1], B.shape[1])
    return np.abs(A[-1, :w, :] - B[0, :w, :]).mean()
```

Rank every plausible pair, then inspect the best candidates visually.

Improve the score when needed by comparing a strip several pixels wide rather than a single edge:

```python
k = 4
score = np.abs(A[:h, -k:, :] - B[:h, :k, :]).mean()
```

### Why pure edge score can fail

- large uniform backgrounds all look compatible;
- compression/codec effects can alter boundary pixels;
- overlapping/repeated UI elements produce duplicate candidates;
- cached regions need not form a perfect fixed grid;
- the target can have been moved, resized, scrolled, or partially obscured.

Use automated scoring to **reduce search**, not to replace evidence-based visual validation.

## 11. Cluster before global assembly

Do not try to solve a 500-tile global jigsaw when the answer uses only 20 tiles.

First group by:

- dominant color/background;
- image dimensions;
- text density;
- perceptual similarity;
- likely document/window family;
- common edge/border features.

Then solve the relevant cluster.

This is a major efficiency rule:

> Reduce the tile universe before optimizing adjacency.

## 12. Text fragments as constraints

Text is unusually valuable because language imposes strong structural constraints.

If recovered tiles reveal fragments such as:

```text
PREFIX...
..._MIDDLE_...
...SUFFIX}
```

use them only after confirming their pixel adjacency or shared document context.

Do not concatenate strings merely because they form a plausible flag. The proof is the recovered visual structure.

For flag-like text, record which tile IDs support each segment.

## 13. Reconstruct the canvas reproducibly

Once tile positions are known, create a small reconstruction script instead of relying only on a manually edited image.

```python
from PIL import Image

T = 64
positions = {
    # 'tile_001.bmp': (0, 0),
    # 'tile_142.bmp': (1, 0),
    # 'tile_087.bmp': (2, 0),
}

max_x = max(x for x, y in positions.values())
max_y = max(y for x, y in positions.values())
canvas = Image.new('RGB', ((max_x+1)*T, (max_y+1)*T), 'black')

for name, (x, y) in positions.items():
    with Image.open('candidate/' + name).convert('RGB') as im:
        canvas.paste(im, (x*T, y*T))

canvas.save('reconstructed.png')
```

If tile dimensions vary, store absolute pixel coordinates and paste using each image's real size rather than assuming a fixed `T`.

The script becomes part of the evidence trail:

```text
cache hash
 -> parser output
 -> selected tile IDs
 -> position mapping
 -> reconstructed image
 -> interpreted text
```

## 14. Validate the reconstruction

A valid result should satisfy more than one condition:

- multiple neighboring edges align naturally;
- fonts/baselines/backgrounds remain continuous;
- text is readable without inventing missing pixels;
- reconstructed content matches the challenge's stated remote-view context;
- the selected tiles come from the relevant RDP cache artifacts;
- any recovered answer/flag is visibly supported by the reconstruction.

Avoid using only a final guessed string as evidence.

## 15. Correlate with session chronology

When multiple RDP sessions or unrelated windows exist, use timestamps and other host artifacts to narrow the candidate cache set.

Ask:

- When was the target supposedly viewed/edited?
- Which remote host was connected at that time?
- Which user account launched the RDP client?
- Were the cache files updated around that period?
- Was cleanup performed after the target session?

Chronology can explain why a later client-side cache still contains fragments even after the original remote file disappeared.

## 16. Preserve negative evidence correctly

If the original target file is absent from the client filesystem, that does **not** refute the challenge narrative.

In an RDP-view scenario:

```text
no local target file
+ confirmed RDP session
+ persistent bitmap caching enabled
+ matching cached visual fragments
```

is a coherent evidence chain.

Do not waste hours on deleted-file carving solely because the target filename is missing locally when the screen-cache hypothesis is already stronger.

## 17. Common dead ends

### Carving the client disk for the original remote filename

Why it fails: the file may never have been copied to the client.

Pivot: recover **rendered residue** from application cache.

### Processing only one `Cache*.bin`

Why it fails: different cache containers can hold different tile classes/entries.

Pivot: extract every plausible cache and compare output counts/content.

### Opening hundreds of tiles individually

Why it fails: slow and destroys visual context.

Pivot: contact sheet first.

### Assuming cache index equals screen position

Why it fails: bitmap cache semantics are not a framebuffer layout.

Pivot: reconstruct from visual/edge constraints.

### Using OCR as the first reconstruction method

Why it fails: isolated character fragments often have too little context.

Pivot: assemble visually first; OCR is optional validation afterward.

### Pure nearest-edge auto-jigsaw

Why it fails: flat colors and repeated UI regions create false low-distance matches.

Pivot: combine edge score with text/background/semantic constraints.

### Treating every tile as part of one screenshot

Why it fails: persistent caches can accumulate content across application states/session activity.

Pivot: cluster relevant tiles before assembly.

## 18. Efficient decision tree

```text
Remote visual content is missing
        |
        v
Was content viewed through RDP?
   | no -> normal filesystem/application route
   | yes
        v
Is forensic image from the RDP client?
   | no -> inspect appropriate server/session artifacts
   | yes
        v
Persistent bitmap caching evidence?
   | no -> other RDP/client artifacts; do not force bitmap-cache route
   | yes
        v
Locate all Cache*.bin
        |
        v
Parse every cache with RDP-aware tool
        |
        v
Many bitmap fragments recovered?
   | no -> revisit cache format/version/path
   | yes
        v
Contact sheet -> shortlist -> cluster
        |
        v
Manual + edge-assisted adjacency
        |
        v
Reproducible canvas reconstruction
        |
        v
Validate text/image against provenance + session evidence
```

## 19. Evidence checklist

Before declaring success, retain:

```text
[ ] forensic source host role identified as client/server
[ ] RDP session evidence recorded
[ ] persistent bitmap-cache setting/evidence recorded
[ ] Cache*.bin original paths and hashes recorded
[ ] parser/tool version and exact extraction command recorded
[ ] extracted tile counts/dimensions recorded
[ ] contact sheet preserved
[ ] relevant tile IDs listed
[ ] adjacency/position mapping preserved
[ ] reconstruction script or exact placement notes preserved
[ ] reconstructed image saved
[ ] recovered answer visibly supported by reconstruction
```

## 20. Reusable lesson

The broader forensic pattern is:

> If a secret was **displayed** on a machine but not stored there as a normal file, investigate application rendering caches, thumbnails, GPU/display residues, remote-session caches, and other presentation-layer artifacts before assuming the evidence is gone.

For Windows RDP specifically, persistent bitmap caches can turn a remote-only document/image into locally recoverable visual fragments.

## Provenance

This reference was generalized from a Bahtera Siber forensic challenge in which the examined Windows workstation was the RDP client, persistent bitmap caching was enabled, `Cache0000.bin`/`Cache0001.bin` were parsed, and the useful cache yielded many small bitmap tiles that were manually reconstructed by visual continuity.

Challenge-specific hostnames, recovered text, flag values, exact cache-entry IDs, and final tile placement are intentionally omitted.