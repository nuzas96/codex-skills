# Triage and Category Routing

This is the first-pass decision reference for `ctf-solve`. The goal is to reach the correct primary category with the least expensive evidence, not to enumerate every possible attack.

## Cheap first pass

1. Inventory all supplied files and URLs.
2. Run `file` on unknown files; inspect magic bytes when extensions disagree.
3. Run small targeted `strings`/`xxd`/metadata checks instead of dumping whole artifacts.
4. Read challenge description, filenames, comments, Docker/compose files, dependency manifests and bot runner before deep exploitation.
5. For a remote service, make one connection/request to learn protocol shape.
6. If source is supplied, map routes/entrypoints/trust boundaries before fuzzing.
7. Record exact flag format if provided.

Example compact recon:

```bash
find . -maxdepth 2 -type f -printf '%p\n' | sort
file -- * 2>/dev/null
rg -n "flag|secret|admin|debug|TODO|FIXME|route|listen|port" .
```

Use narrower commands after the initial signal. Do not generate megabytes of tool output when a filtered query answers the decision.

## File-based routing

| Artifact | Start with |
|---|---|
| `.pcap`, `.pcapng`, `.evtx`, `.raw`, `.mem`, `.dd`, `.E01`, browser profile | `ctf-forensics` |
| ELF/PE/native binary + remote service | `ctf-pwn` unless evidence says logic-only |
| standalone ELF/PE, `.apk`, `.wasm`, `.pyc`, custom bytecode | `ctf-reverse` |
| `.sage`, crypto Python, large integers, keys/ciphertexts | `ctf-crypto` |
| web source, templates, JavaScript app, HTTP URL/API | `ctf-web` |
| suspicious executable/script explicitly framed as malware/C2 | `ctf-malware` |
| image/audio/video/PDF with hidden-data framing | `ctf-forensics` |
| ML model/weights/notebook/inference API challenge | `ctf-ai-ml` |

## Description/service routing

- `buffer overflow`, `ROP`, `libc`, `heap`, `format string`, `shellcode`, `seccomp` -> `ctf-pwn`
- `RSA`, `AES`, `ECC`, `cipher`, `signature`, `nonce`, `lattice`, `LWE`, `PRNG` -> `ctf-crypto`
- `XSS`, `SQL`, `SSTI`, `SSRF`, `JWT`, `OAuth`, `GraphQL`, `cache`, `proxy`, `upload` -> `ctf-web`
- `disk`, `memory`, `packet`, `registry`, `timeline`, `stego`, `spectrogram`, `USB`, `filesystem` -> `ctf-forensics`
- `identify`, `where`, `who`, `locate`, `social`, `map`, `venue`, `vessel` -> `ctf-osint`
- `packed`, `obfuscated`, `beacon`, `C2`, `malware`, `ransomware` -> `ctf-malware`
- `jail`, `sandbox`, `restricted eval`, `esolang`, `RF/SDR`, unusual game/constraint/protocol -> `ctf-misc`
- `adversarial`, `model`, `weights`, `prompt injection`, `inference`, `classifier` -> `ctf-ai-ml`

Service behavior:

- HTTP/HTTPS -> `ctf-web`
- native interactive service that crashes/corrupts state -> `ctf-pwn`
- arithmetic/encryption oracle -> `ctf-crypto`
- restricted interpreter/shell/eval -> `ctf-misc`

## Ambiguity resolution

When two categories seem plausible, ask which **next operation** is required:

- Need to understand code semantics? -> Reverse.
- Need to corrupt native process state? -> Pwn.
- Need to extract evidence from an artifact without changing it? -> Forensics.
- Need to break a cryptographic assumption? -> Crypto.
- Need to abuse browser/server/proxy/application trust boundaries? -> Web.
- Need to trace public-world identity/location? -> OSINT.
- Need to characterize malicious behavior/config/C2? -> Malware.

Choose the category that owns the immediate primitive. Record the pivot when ownership changes.

## Evidence ranking

Prefer paths with:

1. direct source/artifact evidence;
2. deterministic local proof;
3. strong target-version compatibility;
4. a clean success/failure oracle;
5. minimal irreversible state change;
6. low request/compute cost.

A remembered writeup pattern is a hypothesis, not evidence that the target is identical.

## CTF platform note

If a CTF platform API is relevant, identify it first. Do not request credentials/tokens unless an API workflow is actually useful. Keep platform navigation separate from exploit logic.

## Flag validation

Do not finalize the first flag-looking string automatically.

Check:

- expected prefix/format from challenge rules;
- whether the string comes from the intended artifact/path;
- corpus-wide uniqueness when decoys are possible;
- whether server response/validator accepts it when submission feedback is available.

Useful searches:

```bash
rg -n -a '(flag|ctf|htb|pico|zdk)\{[^}\r\n]+\}' .
strings -a suspect.bin | grep -Ei '[A-Za-z0-9_]+\{[^}]+\}'
```

Record the exact source path/offset/request that produced the final candidate.