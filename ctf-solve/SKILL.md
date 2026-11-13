---
name: ctf-solve
description: "Orchestrate end-to-end CTF challenge solving in the local Codex/Kali environment: minimally bootstrap or resume the challenge workspace, preserve PROGRESS.md, perform evidence-first triage, select one primary category skill, coordinate justified pivots, run stuck recovery, validate the flag, and hand off to ctf-writeup."
---

# CTF Solve Orchestrator

This skill owns the **lifecycle** of a CTF solve. It is intentionally small. Do not preload the whole knowledge library.

Normal activation model:

```text
ctf-solve + ONE primary category skill
```

Only add a second category when observed evidence proves the challenge crosses a boundary.

## Codex local runtime

This V2 solve lifecycle is designed to run locally in Codex/Kali.

Runtime priorities:

1. obey `/home/nuzhmi/Desktop/ctf-codex/AGENTS.md` when present;
2. create/resume the challenge under `/home/nuzhmi/Desktop/ctf-codex/<challenge-name>/` unless an explicit path overrides it;
3. use locally installed skills under `/home/nuzhmi/.codex/skills/`;
4. use the local source worktree `/home/nuzhmi/Desktop/codex-skills-github/` when source/index access is needed;
5. do not make normal solving depend on fetching the skill library from GitHub over the network.

The GitHub repository is the upstream/canonical source for maintenance and upgrades, not a required network dependency for each Codex solve.

## New-challenge startup rule

A new challenge must reach a meaningful solve attempt as quickly as possible.

Mandatory startup sequence:

```text
create/resume dedicated challenge folder
  -> ensure minimal PROGRESS.md exists
  -> immediately perform first meaningful solve/triage test
  -> record the evidence in PROGRESS.md
  -> continue normal evidence-first solve + progress discipline
```

`PROGRESS.md` is mandatory, but detailed documentation **before the first meaningful test is prohibited** unless the user explicitly requests it.

Do not delay the first test to populate:

- initial hypotheses;
- environment inventories;
- next-action lists;
- detailed challenge metadata;
- `STATE.md`;
- empty `scripts/`, `artifacts/`, or `artifacts/logs/` directories.

After the first meaningful result exists, progress logging returns to the normal detailed discipline: preserve every important finding, dead end, pivot, exact error, offset, relevant version, artifact and verification result.

This startup exception applies only to a brand-new challenge. On resume, read existing state/progress before acting.

## Fast routing index

When a local V2 `ROUTING_INDEX.json` is available, use it as the machine-readable fast path for strong, specific technique signals. Prefer the local installed/source copy over network retrieval.

Use it only as an index:

```text
strong specific signal
  -> local ROUTING_INDEX.json
  -> exact primary skill + exact reference
  -> solve
```

If the signal is ambiguous, multiple routes match, or no route matches confidently, use this orchestrator and the normal category router. The index never replaces the methodology in `SKILL.md` or canonical references.

Do not scan the whole local skill tree when the index already supplies an exact valid path.

## Mandatory solve loop

1. **Bootstrap or resume.** For a new challenge, create the dedicated folder plus minimal `PROGRESS.md` using [references/workspace.md](references/workspace.md), then immediately execute the first meaningful test. For an existing challenge, read `STATE.md` if present and `PROGRESS.md` / `progress.md` before new exploration.
2. **Route cheaply.** Identify the dominant category from supplied evidence. Use the local routing index or [references/triage-routing.md](references/triage-routing.md). Do not preload unrelated skills.
3. **Choose one primary category.** Load only the matching locally installed `ctf-*` skill.
4. **Test before over-documenting.** On a new challenge, the first useful action should be an actual discriminating test, not documentation or scaffold generation.
5. **Search local knowledge when it helps the active path.** Grep local category references for challenge name/author, exact versions, CVE/GHSA and suspected primitive. Do not let broad reference search postpone an obvious cheap test.
6. **Run evidence-first iterations.** Hypothesis -> smallest discriminating test -> evidence -> update progress -> next ranked path. If multiple explanations remain credible with different predicted observations, the same explanation fails repeated discriminating tests, or 2-3 iterations produce no new evidence, use only [Competing hypotheses](references/triage-routing.md#competing-hypotheses) before choosing the next branch. Compare each live path's clue, separating observation, test cost and disconfirming result; try the cheapest informative reversible test first, while retaining a credible expensive path if cheaper paths are ruled out. When one evidence-supported path is clear, test it directly without this review.
7. **Persist important evidence.** After solving has begun, append every important finding to the progress log. Detailed entries are fine; speed optimization applies only to pre-test startup overhead. See [references/progress.md](references/progress.md).
8. **Pivot only on evidence.** Add another category only when a concrete primitive requires it. When evidence suggests connected vulnerabilities or unusual adjacent-layer mismatches, use the compact dependency graph in [references/modern-chains.md](references/modern-chains.md).
9. **Before defeat, recover systematically.** Run [references/stuck-recovery.md](references/stuck-recovery.md) before saying the challenge is blocked or unsolved.
10. **Complete and validate the answer.** If meaningful evidence is recovered but no justified exact candidate exists, use [Evidence to answer](references/triage-routing.md#evidence-to-answer). A clearly recovered flag-shaped value can take the fast path: check its provenance and required format, then report only the strongest validation level actually reached. Do not report obvious decoys as solved.
11. **Write up after solve.** Use `ctf-writeup` once the flag or required final answer is verified.

## Workspace growth rule

The challenge folder and `PROGRESS.md` are mandatory. Everything else is lazy/on-demand.

- `STATE.md`: create when a compact snapshot materially helps a long, complex, multi-session or multi-agent solve.
- `scripts/`: create when multiple scripts need organization; a single `solve.py`/`exploit.py` may live in the challenge root.
- `artifacts/`: create when multiple generated/recovered artifacts need organization.
- `artifacts/logs/`: create when raw logs are worth preserving.

Do not create empty structure merely to satisfy a template.

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

For a brand-new challenge, create minimal `PROGRESS.md`, run the first meaningful test, then record its result.

After that point, a solve that produces important new evidence is incomplete until that evidence is persisted in the progress file. Entries may be concise or detailed; do not discard useful technical detail for formatting speed.

Preserve exact errors, paths, versions, request/response differences, offsets, addresses/relationships, dead ends, pivots and verification evidence when they matter.

When multiple Codex sessions or terminals share the same progress file, treat it as collaborative state: re-read before patching and append/patch instead of overwriting.

## Stuck gate

Do not declare `blocked`, `unsolvable`, `can't solve`, or equivalent until the stuck-recovery checklist has been walked. A failed payload variant is not exhaustion of a primitive class, and exhaustion of one primitive class is not exhaustion of the challenge.

## Language and files

- User conversation may be Bahasa Melayu / English naturally.
- Challenge notes, scripts, code comments and writeups should default to English unless the user explicitly requests another language.
- Commands and code remain in their canonical technical language.

## Supporting references

- [references/triage-routing.md](references/triage-routing.md) — cheap triage, category selection and flag validation.
- [references/workspace.md](references/workspace.md) — minimal bootstrap, Codex challenge folder and continuity rules.
- [references/progress.md](references/progress.md) — startup exception plus mandatory evidence persistence after the first meaningful test.
- [references/codex-agents-template.md](references/codex-agents-template.md) — canonical workspace `AGENTS.md` policy to sync into `/home/nuzhmi/Desktop/ctf-codex/AGENTS.md`.
- [references/codex-readme-template.md](references/codex-readme-template.md) — matching workspace README policy.
- [references/stuck-recovery.md](references/stuck-recovery.md) — pre-defeat 7-point enumeration.
- [references/modern-chains.md](references/modern-chains.md) — second-pass boundary mismatch workflow.
- [references/migration-sources.md](references/migration-sources.md) — V1 source provenance used to build this orchestrator.
- [references/legacy-evidence-lessons.md](references/legacy-evidence-lessons.md) — preserved user-specific evidence discipline.

## Completion criteria

A solve lifecycle is complete only when one of these is true:

- **Solved:** final artifact/flag is verified, progress contains the decisive path, and the user can reproduce it; or
- **Explicit handoff:** exact blocker, tested paths, current strongest hypothesis and next action are recorded in progress after stuck-recovery.
