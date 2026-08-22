# Insecure Deserialization

Canonical V2 reference for CTF web/application deserialization bugs. Use when attacker-controlled bytes/strings are reconstructed into objects by a runtime/framework and object creation or magic methods can change state, trigger callbacks or execute code.

## Recognition

Common signals:

- Java serialization magic `ac ed 00 05` or Base64 `rO0AB`;
- PHP serialized `O:`, `a:`, `s:` structures and calls to `unserialize()`;
- Python `pickle` / `yaml.load` / object hooks;
- .NET `BinaryFormatter`, `ObjectStateFormatter`, ViewState or related formatters;
- serialized objects in cookies, hidden fields, API bodies, queues, Redis/cache entries or WebSocket frames;
- source calls a generic object deserializer on user-controlled data.

First determine **format + library + integrity protection + available classes/gadgets**. Do not fire generic gadget chains before identifying those facts.

## Triage workflow

```text
serialized value
  -> identify encoding/compression wrapper
  -> identify serialization format/runtime
  -> determine integrity/signature/MAC
  -> inspect decoded object/class metadata
  -> identify application-controlled vs attacker-controlled fields
  -> determine reachable gadgets/magic methods
  -> minimal harmless proof
  -> intended CTF impact
```

Useful inspection examples:

```bash
# Base64 Java stream
echo "$VALUE" | base64 -d | xxd | head

# Python pickle disassembly
python3 - <<'PY'
import pickletools, sys
pickletools.dis(open(sys.argv[1], 'rb').read())
PY sample.pkl
```

## Java

Confirm classpath/dependencies before selecting a ysoserial chain. For blind detection, a DNS-only gadget such as URLDNS can establish deserialization without immediately requiring command execution.

Conceptual flow:

```text
serialized Java object accepted
 -> classpath contains usable gadget graph
 -> deserialization invokes gadget callbacks
 -> controlled side effect
```

`ysoserial` payload families are version/dependency-sensitive. A gadget name working in another challenge does not prove availability here.

## PHP object injection

Inspect classes for magic methods and gadget composition:

- `__wakeup`
- `__unserialize`
- `__destruct`
- `__toString`
- framework/library callbacks.

In source-available CTFs, manually trace a short POP chain before reaching for PHPGGC. If a supported framework version matches PHPGGC, use it as an accelerator and verify generated class/property layout.

Also distinguish direct **data-only manipulation** from RCE: changing serialized role/id fields may be sufficient if the application trusts them and no integrity check exists.

## Python

`pickle` is code-capable by design. The central question is whether untrusted data reaches `pickle.loads()` or equivalent. `__reduce__` / reconstruction callables can invoke behavior during loading.

Do not confuse safe JSON/YAML loaders with unsafe object loaders. Identify the exact function and library version.

For YAML, check whether constructors such as Python object/apply tags are enabled by the selected loader.

## .NET / ViewState

Determine:

- formatter type;
- ViewState MAC state;
- machine key/key disclosure if MAC is enabled;
- framework/runtime version;
- available gadget types.

A ViewState-looking Base64 blob alone is not evidence that attacker-controlled object graphs are accepted. First establish whether integrity validation can be bypassed or reproduced.

## Integrity layers

Serialization may be wrapped in:

```text
serialize -> compress -> encrypt -> MAC -> encode
```

or another order. Recover the order exactly.

A strong MAC checked before deserialization can turn the main problem into key recovery/forgery rather than gadget exploitation. A checksum such as CRC is not a cryptographic MAC; analyze whether it can simply be recomputed.

## Minimal proof strategy

Prefer one deterministic side effect appropriate to the challenge:

- controlled object field change;
- DNS/OOB callback in an isolated CTF;
- predictable error showing a class/gadget executed;
- timing side effect when no cleaner oracle exists.

Only build the full command/file-read chain once deserialization and gadget reachability are proven.

## Tools

Depending on runtime:

- Java: `ysoserial`, `marshalsec`;
- PHP: `PHPGGC`;
- .NET: `ysoserial.net`;
- Python: `pickletools`, direct source inspection;
- Burp extensions can help identify formats but are not a substitute for dependency/source verification.

## Common failure modes

- gadget dependency absent or patched;
- serialization bytes modified by URL/Base64/form decoding;
- MAC/signature fails before deserialization;
- class allowlist/filter (for example Java deserialization filters) blocks gadget type;
- object is decoded but not used in the privileged path;
- framework serializes a custom safe schema rather than arbitrary objects.

Preserve exact exception text; class-resolution and MAC errors often reveal which stage was reached.

## Cross-category pivots

- Java/PHP framework chain remains the web primitive -> stay `ctf-web`.
- a native deserializer bug becomes memory corruption -> `ctf-pwn`.
- serialized artifact must be reverse engineered independent of web delivery -> `ctf-reverse`.
- cryptographic wrapper/key recovery becomes the hard problem -> add `ctf-crypto`.

## Provenance

Consolidates V1 `exploiting-insecure-deserialization/SKILL.md` (Apache-2.0, author `mahipal`, blob `8061e0c51c6123cbcf55c1c9d96963326bacc67b`) with V1 `ctf-web/server-side-deser.md`. Generic pentest report/remediation text is intentionally excluded from the active CTF reference.