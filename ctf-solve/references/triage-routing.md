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

## Competing hypotheses

When two or more plausible paths fit the observations, keep them as short candidates rather than committing to the most elaborate story. For each, record (1) the concrete clue, (2) the cheapest test that separates it from alternatives, (3) what new information a positive or negative result would provide, (4) expected time/tool cost, and (5) an explicit disconfirming result. Run high-information, reversible tests early. Re-rank after every result; stop repeating a branch when its predicted evidence is absent. Do not discard a technically credible but expensive path solely because a cheaper path exists: test the cheap path first, then return to the credible path if the evidence supports it or the cheap path is ruled out.

Include directly observable output channels in this comparison when the artifact suggests them: GPIO/LED state, UART, display or framebuffer, files, network responses, and protocol output. Their presence is a clue to test, not evidence that the challenge necessarily hides an easier solution there.

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

## Evidence to answer

Use this short procedure when a meaningful primitive, plaintext, artifact or intermediate result has been recovered but it does not yet justify one exact final answer. Skip reconstruction when a clear flag is directly present in the intended source; perform the ordinary quick provenance/format check instead.

1. Preserve the raw evidence and its path, offset, request or extraction step. Decide what it is before transforming it: a literal flag string is an **observed string**, while decoded, reordered or otherwise derived content is only an **inferred/reconstructed candidate**.
2. Apply only transformations supported by challenge code, metadata, format, checksums or a concrete artifact clue. For non-obvious text, binary, image or multi-layer output, write down the exact byte/bit order, encoding, framing and layer sequence. Use a small deterministic script or local fixture when that makes the reconstruction reproducible; verify intermediate lengths, magic, checksums, round trips or other available invariants.
   For an explicit byte pipeline, use `python3 "$HOME/.codex/skills/ctf-solve/scripts/evidence_transform.py" INPUT OUTPUT --step base64 --step gzip` (repeat `--step` in evidence-derived order). Supported steps are strict Base64/hex decoding, gzip/zlib decompression, whole-byte reversal, per-byte bit reversal and fixed-width word reversal. Set `--expect-sha256` only when an independent digest is supplied. The helper never guesses transformations, writes candidates to stdout, or overwrites an existing output; without an independent digest, its output remains an inferred candidate.
3. Validate the exact candidate against independent local structure or semantics when available. A plausible phrase or expected flag format alone is not validation. Mark it **locally validated** only when a reproducible local predicate supports the exact candidate.
4. Mark it **accepted by an independent verifier** only after an actual challenge/platform verifier accepts it. Submit only an evidence-justified candidate through the authorized flow; never vary guessed formats or suffixes to use private verifier feedback as a search oracle. If no independent verifier is available, say so and report the strongest lower status without implying acceptance.

Keep the status explicit in progress: `observed string` -> `inferred/reconstructed candidate` -> `locally validated` -> `accepted by independent verifier`. These describe evidence strength, not automatic sequential requirements: record only the stages actually supported.
