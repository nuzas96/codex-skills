# OpenZFS Encrypted Send-Stream Recovery

Use this reference when the artifact path converges on an **OpenZFS send stream that still contains native-encryption metadata and encrypted file blocks**, especially when the stream was first hidden inside a PCAP, media file, archive, QR fragments, compressed container, or other delivery layer.

This is a **forensics-first** workflow. The decisive job is usually to preserve and reconstruct the exact artifact chain, identify the ZFS records that carry key metadata and file data, and only then perform the minimum cryptographic work needed to validate a passphrase and decrypt the target block.

## Recognition signals

Load this reference when several of these appear together:

- `zfs send` / OpenZFS send stream / replay stream;
- dataset or snapshot names embedded in a binary stream;
- native encryption properties such as `encryption`, `keyformat`, `pbkdf2iters`;
- `AES-256-GCM` / `aes-256-gcm`;
- wrapped-key metadata with salt, IV, MAC/tag and encrypted key material;
- DMU object records such as `DMU_OT_PLAIN_FILE_CONTENTS`;
- encrypted write records or a small encrypted file block inside the stream;
- a PCAP or carrier that reconstructs into XZ/gzip/zstd data whose decompressed result is a ZFS stream;
- a candidate passphrase that can be checked by an AEAD authentication tag rather than by plaintext plausibility.

A representative artifact chain is:

```text
PCAP
  -> suspicious TCP stream
  -> concatenated carrier objects
  -> embedded archive / QR pieces
  -> ordered + hash-verified chunks
  -> compressed blob
  -> OpenZFS encrypted send stream
  -> key metadata + encrypted DMU object
  -> authenticated key unwrap
  -> per-block key derivation
  -> AES-GCM block decrypt
```

Do **not** jump directly to password guessing or raw AES attempts while earlier reconstruction layers are still uncertain.

## Core decision model

```text
carrier evidence
  -> exact reconstruction
  -> independent hash/magic validation
  -> identify OpenZFS stream + snapshot metadata
  -> locate encryption/keydata records
  -> locate target DMU object/write record
  -> test passphrase by authenticated key unwrap
  -> derive the exact block key used by that stream/version
  -> authenticated block decrypt
  -> validate recovered file content
```

The important distinction is:

```text
"passphrase looks plausible"
    !=
"passphrase is cryptographically correct"
```

For an AEAD-wrapped ZFS key, successful authentication is the oracle.

---

## 1. Preserve the outside-in extraction chain

When the stream is transported through a network capture or nested carrier, preserve every layer rather than extracting only the final bytes.

For a PCAP:

```bash
tshark -r capture.pcapng -q -z conv,tcp
tshark -r capture.pcapng -T fields \
  -e tcp.stream -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport \
  | sort -u
```

Follow only the suspicious stream first:

```bash
tshark -r capture.pcapng \
  -Y 'tcp.stream == N && tcp.len > 0' \
  -T fields -e tcp.payload \
  | tr -d '\n' | xxd -r -p > stream.bin
```

Then identify structural boundaries rather than carving by guess:

```bash
file stream.bin
xxd -l 128 stream.bin
binwalk stream.bin
```

If two formats are concatenated, prefer parsing the first format to its formal terminator. For example, for PNG, walk chunks until `IEND` rather than searching for a lucky ZIP signature in the middle of compressed image data.

### Why this matters

A challenge may intentionally use:

```text
PNG || ZIP
```

or another legal/near-legal concatenation. Signature-only carving can work, but a parser-aware boundary gives stronger evidence and avoids false offsets.

Record hashes after each reconstruction stage:

```bash
sha256sum stream.bin carrier.png payload.zip reconstructed.xz zfs_stream.bin
```

If the challenge provides a manifest hash, it is a **hard checkpoint**. Do not continue until your reconstructed artifact matches it.

---

## 2. Reassemble indexed chunks with local integrity checks

A common CTF transport pattern is:

```text
MAGIC | index | total | sha256(chunk) | base64(chunk)
```

The exact separators or field labels vary, but the recovery discipline is stable:

1. decode each payload independently;
2. validate that chunk against its own hash;
3. store by explicit index, not discovery order;
4. verify all indexes `0..total-1` are present exactly once;
5. concatenate in numeric order;
6. verify the full-object hash if available.

For extracted byte fragments, use the bounded standard-library helper after determining the fragment order from explicit indexes or evidence. Its JSON manifest has a `total`, `chunks` array (`index`, manifest-relative `path`, optional per-fragment `sha256`), and optional whole-object `sha256`. The helper rejects missing/duplicate indexes, conflicting hashes, path escapes, incomplete input, and oversized output. It reports unverified reconstruction when no digest is available; that output is not independently validated.

```json
{
  "total": 2,
  "chunks": [
    {"index": 1, "path": "part-b.bin", "sha256": "<64 hex characters>"},
    {"index": 0, "path": "part-a.bin", "sha256": "<64 hex characters>"}
  ],
  "sha256": "<optional whole-object SHA-256>"
}
```

Run it with `python3 "$HOME/.codex/skills/ctf-forensics/scripts/reassemble_fragments.py" manifest.json reconstructed.bin`. Entries may appear in any manifest order; output follows `index`, never filename or discovery order. Decode transport encodings per fragment before listing the resulting files. The helper does not infer missing bytes or order.

### Negative knowledge

Do not:

- concatenate QR payloads in filename order unless index fields prove it;
- trust OCR/QR output without the embedded chunk hash;
- discard duplicates before checking whether they conflict;
- move into crypto because a decompressor produces *some* output.

The artifact boundary must be deterministic first.

---

## 3. Decompress and fingerprint the send stream

After a verified compressed blob is recovered:

```bash
xz -dc reconstructed.xz > zfs_stream.bin
file zfs_stream.bin
strings -a zfs_stream.bin | head -100
```

Do not assume `file` knows every OpenZFS send-stream variant. Look for structured metadata and record-level evidence.

Useful concepts to identify:

- begin/snapshot records;
- dataset/snapshot name;
- feature flags;
- nvlist / property metadata;
- encryption algorithm;
- key format;
- PBKDF2 iteration count;
- wrapped key material;
- object records;
- write records and their logical/object identifiers.

A raw encrypted stream can still reveal enough metadata to determine:

```text
dataset identity
snapshot identity
encryption algorithm
passphrase KDF parameters
wrapped-key parameters
object types and sizes
which object contains file data
```

This is frequently enough to decrypt one target object without importing the whole pool or rebuilding a full ZFS filesystem.

---

## 4. Find the target DMU object before decrypting bytes

The stream may contain many records, but only a small number correspond to file contents.

Prioritize object records whose type indicates ordinary file contents, for example:

```text
DMU_OT_PLAIN_FILE_CONTENTS
```

Then correlate subsequent encrypted write records with:

- object number;
- logical offset;
- logical size;
- compressed/encrypted payload length;
- block salt;
- IV/nonce;
- authentication tag/MAC.

If the challenge has only one small encrypted file-content object, that is a much stronger target than attempting to decrypt every opaque block.

### Evidence table

Keep a compact table in `PROGRESS.md`:

```text
object  type                       size    encrypted writes   relevance
2       DMU_OT_PLAIN_FILE_CONTENTS 512     1                  target
...
```

Also record exact byte offsets if you are extracting a record manually.

---

## 5. Model the OpenZFS key hierarchy

Do not treat the passphrase as the direct data-encryption key.

A useful mental model for native-encryption challenge artifacts is:

```text
passphrase
  -> password KDF (metadata supplies salt + iteration count)
  -> wrapping/key-encryption key
  -> AEAD unwrap of stored key material
  -> dataset/master key material
  -> block/data key derivation
  -> AEAD decrypt of encrypted write block
```

The exact serialization, AAD fields, labels, HKDF inputs, endianness and record fields are **implementation/version dependent**. Derive them from:

1. the stream metadata/record parser;
2. the supplied implementation/source if present;
3. the exact OpenZFS version/format being reproduced.

Do not cargo-cult constants from an unrelated writeup.

---

## 6. Use AEAD authentication as the password oracle

When the key metadata provides all of:

- password-KDF salt;
- iteration count;
- wrapped ciphertext;
- IV/nonce;
- authentication tag;
- required AAD/context;

a candidate passphrase can be tested decisively.

Representative pattern:

```python
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

wrapping_key = hashlib.pbkdf2_hmac(
    "sha1",           # use the algorithm proven by the target format
    candidate,
    kdf_salt,
    iterations,
    32,
)

try:
    unwrapped = AESGCM(wrapping_key).decrypt(
        wrap_iv,
        wrapped_ciphertext + wrap_tag,
        wrap_aad,
    )
except Exception:
    # wrong candidate OR wrong metadata/AAD reconstruction
    pass
else:
    # authentication succeeded: candidate + metadata interpretation are consistent
    master_key = unwrapped[:32]
```

### Important interpretation

AEAD failure does **not** distinguish between:

- wrong password;
- wrong IV;
- wrong tag;
- wrong AAD;
- wrong byte order;
- wrong wrapped-key boundary;
- wrong KDF parameters.

So before brute-forcing a large password space, first validate your metadata extraction using known-good structural invariants.

When challenge lore suggests a small set of candidate words, authenticated unwrap is ideal for testing them without subjective plaintext scoring.

---

## 7. Derive the data/block key exactly

Once the wrapped key material is authenticated and unwrapped, the encrypted file block may still use a derived key rather than the raw master key.

A challenge may expose per-block salt/context and use an HKDF step such as:

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

block_key = HKDF(
    algorithm=hashes.SHA512(),
    length=32,
    salt=None,
    info=block_context,
).derive(master_key)
```

Treat that as a **pattern**, not a universal OpenZFS constant. Confirm the exact derivation used by the target stream/version.

Then decrypt the block with the record's IV and authentication tag:

```python
plaintext = AESGCM(block_key).decrypt(
    block_iv,
    encrypted_block + block_tag,
    block_aad,          # may be None or structured, depending on the target
)
```

Only after the tag verifies should you interpret the plaintext.

---

## 8. Validation ladder

A robust solve should have several independent checkpoints:

```text
1. suspicious network stream identified
2. carrier split at structural boundary
3. archive members extracted
4. every indexed fragment passes its own SHA-256
5. reconstructed compressed object matches manifest hash
6. decompressed object parses as expected ZFS send stream
7. encryption/KDF metadata is internally consistent
8. candidate passphrase passes AEAD key-unwrapping authentication
9. target block passes AEAD authentication
10. recovered plaintext matches expected file/flag grammar
```

Do not replace cryptographic checks with "the text looks right" when an authentication tag is available.

---

## 9. Common dead ends and better pivots

### Dead end: mount/import ZFS immediately

A send stream is not automatically a mountable pool image. If the challenge only needs one encrypted object, full pool reconstruction may be unnecessary and can add tooling/version friction.

**Better:** parse enough of the replay stream to recover metadata and the relevant object/write record.

### Dead end: brute-force passphrases before reconstruction

If one QR piece or stream byte is wrong, every candidate fails authentication.

**Better:** finish chunk hashes and full manifest validation first.

### Dead end: direct AES with the passphrase

Native encryption generally has a key hierarchy.

**Better:** recover KDF parameters -> wrapping key -> authenticated key unwrap -> block-key derivation.

### Dead end: assume all opaque bytes are encrypted file contents

Replay streams contain structural metadata, object descriptions and multiple record types.

**Better:** map object IDs/types and target file-content writes.

### Dead end: copy AAD/endianness from another challenge

AEAD is extremely sensitive to exact associated data and serialization.

**Better:** derive AAD and field ordering from the exact implementation/stream version.

### Dead end: trust historical/lore passphrase clues as proof

A thematic clue only proposes a candidate.

**Better:** use AES-GCM authentication to prove or reject it.

---

## 10. Cross-category boundary

Keep `ctf-forensics` primary while the dominant work is:

```text
PCAP -> carrier -> fragment reconstruction -> compression -> ZFS record parsing
```

Add `ctf-crypto` only if the challenge pivots into genuine cryptanalysis such as:

- breaking the KDF rather than testing candidate passphrases;
- attacking AES-GCM nonce reuse;
- recovering a key from mathematical weakness;
- solving a nontrivial custom key schedule.

Using standard PBKDF2/HKDF/AES-GCM correctly to unlock forensic evidence is still primarily forensic artifact recovery.

---

## 11. Minimal reporting checklist

Record:

```text
original artifact hashes
suspicious TCP stream/endpoints
carrier boundary and carved offsets
archive member list
fragment protocol and per-chunk hashes
reconstructed-object hash
compression format
ZFS dataset/snapshot name
encryption + keyformat + KDF iteration metadata
target DMU object number/type/size
wrapped-key IV/tag/AAD interpretation
candidate passphrase verification result
master/data-key derivation method
encrypted block offset/IV/tag
final AEAD verification
recovered file/flag
```

This makes the solve reproducible even when the original chain crosses several unrelated-looking artifact formats.

## Provenance

Harvested from the Bahtera Siber challenge **Warkah Dari Si Hulu Balang** in the user's P4KT4M writeup. Generalized lessons retained here are:

- parser-aware carving of concatenated network-delivered artifacts;
- hash-verified reconstruction of indexed QR chunks;
- compressed OpenZFS send-stream identification;
- encrypted DMU object targeting;
- passphrase -> PBKDF2 wrapping key -> authenticated AES-GCM key unwrap;
- derived block key -> authenticated AES-GCM file-block recovery;
- AEAD tags as deterministic password/metadata validation.

Challenge-specific flag values, fixed hashes, offsets, historical answer words and key bytes are intentionally omitted.
