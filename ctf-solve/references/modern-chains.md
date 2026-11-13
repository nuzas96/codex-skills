# Modern Multi-Stage Chains

Use this after normal triage establishes a primitive, or source evidence suggests multiple connected vulnerabilities with unresolved prerequisites. It is a second-pass method for challenges where adjacent parsers, protocols, trust boundaries or state machines disagree.

## Boundary-first workflow

1. Describe the observable primitive without prematurely naming an exploit.
2. List every transformation between user input and the flag:
   - parser;
   - decoder/encoder;
   - resolver;
   - proxy;
   - browser;
   - filesystem/container layer;
   - protocol bridge;
   - authorization layer;
   - state transition.
3. For each adjacent pair, ask whether they interpret the same value differently.
4. Build one small oracle/state change for each link.
5. Automate only when the manual oracle is deterministic.
6. Derive offsets, lengths, versions, endian order and framing from the target.
7. Record evidence for each chain link separately so the final stage can fail without destroying understanding of the earlier stages.

## Compact exploit dependency graph

When source or observations suggest multiple connected vulnerabilities, require a compact graph in `PROGRESS.md` before choosing another payload family. Skip this for a straightforward single primitive.

Use one row per edge:

```text
input/capability -> service + transformation -> gained capability
requires: ... | status: confirmed / plausible / rejected / runtime-blocked
source or observation: ... | smallest separating test: ...
```

- Inventory attacker control over path, authority, credentials, headers, method, body, files and state; track transformations and which service receives each output. Include error branches and alternate destinations.
- Each edge must name all prerequisites: reachability, credentials, input delivery, dependency/version, permissions, state lifetime and an observable effect. A suspicious sink is only a plausible edge until its preconditions and behavior are established.
- Work forward from current capabilities and backward from the target data. Connect a primitive's output to the next primitive's required input. File contents, database rows and process state require different final capabilities and observation channels.
- Keep statuses separate: **confirmed** has source/test evidence for the stated scope; **plausible** predicts a result; **rejected** has a specific disconfirming observation; **runtime-blocked** lacks a required reproduction environment. Source-confirmed control flow alone does not confirm an exploit. A path with any unconfirmed prerequisite remains unverified.
- Rank tests by how cheaply they resolve a missing prerequisite or distinguish two live graphs. If one chain fails, vary the destination service, state change, input-delivery mechanism, constructor behavior or observation channel rather than merely changing syntax. Reopen a rejected edge only when new evidence changes its assumptions.
- Preserve blind side effects as capabilities: an error response may coexist with an outbound request, state mutation or callback. Verify control flow and a harmless state marker independently from the returned status.
- If no useful chain survives, record the first unsatisfied dependency and the exact test or runtime needed. Do not label a blocked edge rejected, or a plausible chain solved.

Detailed Web tests for reflection, authentication state and service transitions live in [the Web chain reference](../../ctf-web/references/cross-layer-request-to-file.md#service-state-and-constructor-edges).

## Common mismatch families

- raw URL string vs resolved destination;
- front proxy parser vs backend parser;
- extension/MIME vs decoded file type vs execution handler;
- top-level authorization vs nested resolver authorization;
- advertised length vs actual allocation/buffer;
- checked state vs later committed state;
- host-visible file type vs nested container format;
- language numeric representation vs raw bit representation;
- client PRNG semantics vs server/reimplementation arithmetic.

These are pattern families, not payloads. Reproduce behavior on the supplied target instead of copying constants from historical writeups.

## Routing detailed patterns

Detailed technique knowledge belongs to canonical category references, not this orchestrator:

- Nginx/request-target -> PHP route/signature -> SQL field selector -> filesystem/static-file chains -> `ctf-web/references/cross-layer-request-to-file.md`
- Web URL/proxy/resolver/upload/GraphQL/race chains -> `ctf-web/references/`
- Format-string/ROP/partial overwrite/SROP/UAF/eBPF chains -> `ctf-pwn/references/`
- Nested documents, HID, animated-image channels -> `ctf-forensics/references/`
- Packed binaries, symbolic-execution blockers, client PRNG -> `ctf-reverse/references/`
- Huffman/LCG/RSA faults and related constructions -> `ctf-crypto/references/`
- unusual infrastructure/database chains -> `ctf-misc/references/`

V2 deliberately avoids a second encyclopedia here because that would duplicate category knowledge and cause drift.

## When to add another category

Add a second category only if the next required primitive has changed ownership. Examples:

```text
Forensics extraction -> Crypto decryption
Web request primitive -> Reverse WASM logic
Reverse bug discovery -> Pwn control-flow exploit
Malware triage -> Reverse native config routine
```

Record the boundary and why the second skill is needed.

## Guardrails

- Historical organizer/writeup patterns are evidence of a class, not proof of an identical target.
- Prefer supplied source, binaries, libc, schemas, captures and version data over remembered constants.
- Keep target interactions within the CTF scope provided by the user.
- Do not load every modern-chain reference speculatively; that creates anchoring bias.

## Completion criteria

For a multi-stage chain:

- each primitive is individually reproducible;
- each boundary mismatch is explained;
- target-derived values replace copied constants where possible;
- progress contains evidence for every stage;
- final flag/artifact is validated.

## Historical source

This workflow is derived from V1 `ctf-modern-chains`. Its detailed reusable material was redistributed into the canonical V2 category owners during the completed migration; the originals remain frozen in `archive/pre-restructure-20260823` as historical provenance.
