---
name: ctf-solve
description: "Orchestrate end-to-end CTF challenge solving: create or resume the workspace, preserve PROGRESS.md, perform evidence-first triage, select one primary category skill, coordinate justified pivots, run stuck recovery, validate the flag, and hand off to ctf-writeup. Use for any active CTF solve, especially when category is unknown or continuity matters."
---

# CTF Solve Orchestrator

This skill owns the **lifecycle** of a CTF solve. It is intentionally small. Do not preload the whole knowledge library.

Normal activation model:

```text
ctf-solve + ONE primary category skill
```

Only add a second category when observed evidence proves the challenge crosses a boundary.

## Fast routing index

When repository access is available, [ROUTING_INDEX.json](../ROUTING_INDEX.json) is the machine-readable fast path for strong, specific technique signals.

Use it only as an index:

```text
strong specific signal
  -> ROUTING_INDEX.json
  -> exact primary skill + exact reference
  -> solve
```

If the signal is ambiguous, multiple routes match, or no route matches confidently, fall back to this orchestrator and the normal category router. The index never replaces the methodology in `SKILL.md` or canonical references.

Do not scan the repository when the index already supplies an exact valid path.

## Mandatory solve loop

1. **Resume before exploring.** Read an existing `PROGRESS.md` / `progress.md` first. If this is a new challenge, create the workspace and progress file using [references/workspace.md](references/workspace.md).
2. **Search local knowledge before committing.** Grep category references for the challenge name, author, exact library/browser version, CVE/GHSA, and suspected primitive. This prevents repeating already-documented dead ends.
3. **Triage cheaply.** Identify files, service behavior, source structure and flag format. Use [references/triage-routing.md](references/triage-routing.md).
4. **Choose one primary category.** Load only the matching `ctf-*` skill.
5. **Run evidence-first iterations.** Hypothesis -> smallest discriminating test -> evidence -> update progress -> next ranked path.
6. **Persist before replying.** If a turn produced a finding, append it to the progress log before sending the user-facing reply. See [references/progress.md](references/progress.md).
7. **Pivot only on evidence.** Add another category only when a concrete primitive requires it. For unusual adjacent-layer mismatches, use [references/modern-chains.md](references/modern-chains.md).
8. **Before defeat, recover systematically.** Run [references/stuck-recovery.md](references/stuck-recovery.md) before saying the challenge is blocked or unsolved.
9. **Validate the final artifact.** Confirm source/path, uniqueness and expected flag format; do not report obvious decoys as solved.
10. **Write up after solve.** Use `ctf-writeup` once the flag or required final answer is verified.

## Evidence-first rule

For every meaningful branch:

```text
observable -> hypothesis -> smallest test -> result -> recorded evidence -> next decision
```

Prefer, in order:

1. supplied source / exact artifact evidence;
2. local deterministic reproduction;
3. one minimal remote validation;
4. targeted automation/fuzzing;
5. broad brute force or broad external searching only when justified.

Do not repeat a failed branch unless new evidence changes the expected outcome.

## Primary category router

| Evidence | Primary skill |
|---|---|
| HTTP app, API, browser bot, auth/session, injection, proxy/cache | `ctf-web` |
| Native memory corruption, remote ELF/service, ROP/heap/FSOP | `ctf-pwn` |
| RSA/AES/ECC/signatures/PRNG/lattice/custom crypto | `ctf-crypto` |
| Binary semantics, bytecode/VM, APK/WASM, anti-analysis | `ctf-reverse` |
| PCAP/disk/memory/browser/media/container/artifact recovery | `ctf-forensics` |
| Geolocation, identity, social/web-public-data investigation | `ctf-osint` |
| Malware triage, obfuscation, C2/config extraction, behavior | `ctf-malware` |
| Jail/sandbox, esolang, unusual game/protocol/infra puzzle | `ctf-misc` |
| Full HTB/VulnHub/Boot2Root machine lifecycle | `ctf-boot2root` |
| Model extraction, adversarial ML, prompt/tool/model attacks | `ctf-ai-ml` |

Ambiguous binary rule: a binary plus a remote exploitation service usually starts at `ctf-pwn`; a standalone binary whose logic must be understood starts at `ctf-reverse`. Pivot between them when evidence demands it.

## Cross-category rule

Do **not** activate categories speculatively. Add one only for a concrete boundary, for example:

- Web -> Crypto: custom token/MAC/signature must be broken.
- Web -> Reverse: WASM/native/obfuscated client logic gates progress.
- Reverse -> Pwn: reversing exposes a memory-corruption primitive that must be exploited.
- Forensics -> Crypto: recovered ciphertext/key material needs cryptanalysis.
- Forensics -> OSINT: recovered identity/location artifact must be traced publicly.
- Malware -> Reverse: a native routine requires deeper program analysis.

Record why the second category was activated in `PROGRESS.md`.

## Progress gate

A CTF turn that produced a new finding is incomplete until the finding is written to the progress file. Keep entries short and append-only. Preserve exact errors, paths, versions, request/response differences and dead ends.

When multiple agents or terminals share the same progress file, treat it as collaborative state: re-read before patching and append/patch instead of overwriting.

## Stuck gate

Do not declare `blocked`, `unsolvable`, `can't solve`, or equivalent until the stuck-recovery checklist has been walked. A failed payload variant is not exhaustion of a primitive class, and exhaustion of one primitive class is not exhaustion of the challenge.

## Language and files

- User conversation may be Bahasa Melayu / English naturally.
- Challenge notes, scripts, code comments and writeups should default to English unless the user explicitly requests another language.
- Commands and code remain in their canonical technical language.

## Supporting references

- [references/triage-routing.md](references/triage-routing.md) — cheap triage, category selection and flag validation.
- [references/workspace.md](references/workspace.md) — challenge folder and continuity rules.
- [references/progress.md](references/progress.md) — hard pre-reply persistence gate.
- [references/stuck-recovery.md](references/stuck-recovery.md) — pre-defeat 7-point enumeration.
- [references/modern-chains.md](references/modern-chains.md) — second-pass boundary mismatch workflow.
- [references/migration-sources.md](references/migration-sources.md) — V1 source provenance used to build this orchestrator.
- [references/legacy-evidence-lessons.md](references/legacy-evidence-lessons.md) — preserved user-specific evidence discipline.

## Completion criteria

A solve lifecycle is complete only when one of these is true:

- **Solved:** final artifact/flag is verified, progress contains the decisive path, and the user can reproduce it; or
- **Explicit handoff:** exact blocker, tested paths, current strongest hypothesis and next action are recorded in progress after stuck-recovery.
