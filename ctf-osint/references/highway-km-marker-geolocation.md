# Highway / Toll Road Geolocation via Kilometer Markers

When a CTF image shows a road with a small white kilometer post on the shoulder, that's almost always the solve — the number narrows the location to within ~1 km, often exactly at an interchange or notable point.

## Step 1 — Read the km post (vision)

Crop the right shoulder / guardrail area:
```python
from PIL import Image
img = Image.open('highway.jpg')           # don't trust the extension, file may be JPEG with .png name
w, h = img.size
img.crop((w*0.55, h*0.30, w*0.90, h*0.65)).save('crop_km_marker.jpg')
```

Indonesian / Malaysian / Vietnamese km posts:
- White rectangle ~40 cm tall, black digits, mounted on a short metal post
- Indonesian style: usually 3-digit format with one decimal (e.g. `188.0`)
- Vietnamese style: similar but with smaller "Km" prefix
- Malaysian: green-on-white, often with state highway code prefix (e.g. `FT002`)

## Step 2 — Identify the country first (before searching the number)

Reading the post alone wastes search budget. Establish country/region first from:
- **License plate**: Indonesia uses single-letter prefix (B=Jakarta, D=Bandung, L=Surabaya, etc.). Plate prefix is your fastest country ID.
- **Guardrail type**: W-beam + grass embankment = Indonesia/Java toll road (Jalan Tol)
- **Vegetation**: tropical evergreen + palm trees = equatorial (Indonesia, Malaysia, southern Vietnam)
- **Overcast + lush green** = Java during rainy season (most of the year)

## Step 3 — Identify the road network (cumulative km arithmetic)

Most CTF "highway km X" challenges hit **Indonesian Trans-Java toll road** (Jalan Tol Trans-Jawa). The km markers are **cumulative from Jakarta (Cawang)** — they do NOT reset per segment. So if you see "188.0", you have to add up segment lengths:

| Segment | Length | Cumulative km from Jakarta |
|---|---|---|
| Jakarta–Cikampek (Jakpek) | 72 km | 0 → 72 |
| Cikopo–Palimanan (Cipali) | 116 km | 72 → 188 |
| Palimanan–Kanci | 26 km | 188 → 214 |
| Kanci–Pejagan | 35 km | 214 → 249 |
| Pejagan–Pemalang | 57 km | 249 → 306 |
| Pemalang–Batang | 39 km | 306 → 345 |
| Batang–Semarang | 75 km | 345 → 420 |
| Semarang–Solo | ~92 km | 420 → 512 |
| Solo–Ngawi–Kertosono–Mojokerto–Surabaya | continues east | 512 → ~730 |

Wikipedia tables for each segment show the cumulative km in the "Exit" column. Pattern: just look up the first segment whose cumulative km matches your number.

**Pitfall**: Some local regency roads reset km 0 at their own start. If Wikipedia cumulative-km doesn't match your image, the road may be a local one (e.g. a provincial road in West Java), not Trans-Java. Cross-check with road style — local roads don't have W-beam guardrails and gantry signs.

## Step 4 — Pinpoint to interchange via OSM

Once you know "km 188 = X interchange", get exact coordinates:

```bash
# Use OSM Nominatim — search for the interchange name (Indonesian: "Simpang Susun X")
curl -sL "https://nominatim.openstreetmap.org/search?q=Simpang+Susun+Palimanan&format=json&limit=5" \
  -A "highway-i-osint/1.0"
```

If the interchange name doesn't return a hit, search by adjacent village + toll name:
```bash
curl -sL "https://nominatim.openstreetmap.org/search?q=Palimanan+toll+Cirebon&format=json&limit=10" \
  -A "highway-i-osint/1.0"
```

Filter the result to `class=highway, type=motorway_junction` — that's the OSM node for an interchange.

Reverse-geocode to confirm:
```bash
curl -sL "https://nominatim.openstreetmap.org/reverse?lat=-6.6897930&lon=108.4243420&format=json&zoom=18" \
  -A "highway-i-osint/1.0"
```

The display_name should mention both the toll road name and a village — that confirms you're at the right interchange.

**Pitfall**: Nominatim returns `Access denied` if you hit it too fast or without a User-Agent. Always set `-A "<purpose>/<version>"` and add `sleep 1` between consecutive queries. After ~5 rapid hits you get blocked for hours.

**Pitfall**: The OSM `motorway_junction` node is where ramps meet the mainline — it's typically within 50-200m of the actual km post on the mainline. For 3-decimal precision that's fine (~11m at the equator). If the CTF author demands sub-100m accuracy, cross-check the km-post exact lat/lon from Google Street View panoramas near the interchange.

## Step 5 — Cross-verify before submitting

Always confirm the coordinates via a second source:
- Google Maps URL: `https://www.google.com/maps/@<lat>,<lon>,16z` — check the Place card shows the expected village/district
- OSM embed: `https://www.openstreetmap.org/?mlat=<lat>&mlon=<lon>#map=16/<lat>/<lon>` — visually confirm road layout matches image

If Google Maps and OSM both place you at the same interchange with matching village name, submit.

## Worked example: "Highway I" (HNYX CTF)

- Image: Indonesian toll road, km post `188.0`, plate prefix `B` (Jakarta), tropical vegetation
- Math: 72 (Jakpek) + 116 (Cipali) = **188** → Palimanan Interchange (East terminus of Cipali)
- OSM: `motorway_junction` "Palimanan" on Jalan Tol Cikopo–Palimanan → **-6.6897930, 108.4243420** (Kempek, Kabupaten Cirebon, Jawa Barat)
- Google Maps place card: "Pegagan, Cirebon, West Java" — same location
- Submit (3 dp): `HNYX{-6.690,108.424}`

## When this pattern fails (pivots)

- **Image shows an exit ramp sign with city names instead of a km post**: pivot to Road sign OCR + driving side logic. Don't try the km arithmetic.
- **No km post visible, just road scenery**: use Street View panorama matching (see main geolocation reference).
- **Km post is non-numeric** (e.g. shows a route number like "1" with a shield): switch to highway-route-shield OSINT (route numbering systems, road atlases).
- **Not Indonesia**: same pattern works for Vietnam (cumulative from Hanoi via expressway numbers), Malaysia (state route numbers, not cumulative km). Build the segment-length table per country on first encounter.