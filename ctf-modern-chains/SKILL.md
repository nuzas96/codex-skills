---
name: ctf-modern-chains
description: Identify and execute unusual multi-stage CTF exploit chains where ordinary category playbooks stall, especially cross-protocol web attacks, resolver-path authorization gaps, parser and file-format exploitation, partial-overwrite pwn, game-state races, uncommon artifact containers, symbolic-execution blockers, eBPF primitives, or weak custom crypto constructions. Use after initial triage by the normal ctf-web, ctf-pwn, ctf-forensics, ctf-reverse, ctf-crypto, or ctf-misc skill reveals one of these patterns.
---

# CTF Modern Chains

Use this skill as a second-pass pattern matcher. Start with the appropriate `ctf-*` category skill, establish a concrete primitive, then load only the relevant reference below.

## Workflow

1. Record the observable primitive without naming an exploit prematurely: controlled URL, sort order, file extension, parser length, pointer field, resolver path, seed, or artifact boundary.
2. List every parser, protocol, trust boundary, and state transition between input and flag.
3. Search for a mismatch between adjacent layers: raw URL versus resolved IP, FTP versus Redis framing, extension versus decoded image, guarded root resolver versus unguarded nested resolver, or advertised length versus real buffer.
4. Build the smallest deterministic oracle or state change before attempting the full chain.
5. Automate only after a manual probe distinguishes success from failure.
6. Re-derive offsets, versions, byte order, and protocol framing from the target. Never copy constants from an example.
7. Preserve evidence for each link in the chain so a failed final stage can be debugged independently.

## Reference Routing

- Read [references/web.md](references/web.md) for cross-protocol SSRF, blind sort oracles, upload polyglots, GraphQL alternate paths, weak JWT plus authorization, and memory-overread web services.
- Read [references/pwn.md](references/pwn.md) for staged format-string/ROP, partial return overwrites, SROP staging, UAF callback overwrite, and raw eBPF program-array execution.
- Read [references/artifacts-reverse.md](references/artifacts-reverse.md) for nested PDF/container artifacts, USB HID reconstruction, APNG channels, packed binaries, anti-symbolic-execution patching, and client PRNG reproduction.
- Read [references/crypto-misc.md](references/crypto-misc.md) for Huffman ambiguity, LCG reversal, RSA fault leakage, representation punning, state-race underflow, and over-privileged PostgreSQL chains.

## Guardrails

- Treat organizer writeups as evidence of a pattern, not proof that an identical payload applies.
- Prefer locally supplied challenge source, binaries, libc, schemas, and protocol traces over remembered constants.
- Keep network actions within the CTF target and scope supplied by the user.
- Do not load all references by default; irrelevant patterns create anchoring bias.

## Completion Criteria

- Reproduce the primitive reliably.
- Explain why each boundary accepts the crafted input.
- Convert hard-coded values into target-derived calculations where possible.
- Verify the flag path without depending on challenge-specific flags or credentials.
