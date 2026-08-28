# CTF Operating Rules

Apply this section only to authorized CTF, lab, wargame, or challenge work.

## Workspace location

- Use `/home/nuzhmi/Desktop/ctf-codex` as the root for all new CTF work.
- Create one dedicated subfolder per challenge under this root.
- `PROGRESS.md` is mandatory for every challenge.
- If a challenge folder already exists, resume it instead of creating a duplicate.
- Do not create empty `STATE.md`, `scripts/`, `artifacts/`, or `artifacts/logs/` merely to satisfy a template.

## Start and resume

### New challenge

- Run `.ctf/bin/ctf-init "<challenge name>"` when available. The initializer must create/resume only the dedicated challenge folder plus a minimal `PROGRESS.md`.
- If the helper is unavailable, create the challenge folder and minimal `PROGRESS.md` directly.
- Immediately perform the first meaningful solve/triage test after bootstrap.
- Do **not** spend time populating detailed progress notes, hypotheses, environment summaries, next actions, `STATE.md`, or empty helper directories before that first meaningful test.
- After the first meaningful test produces evidence, update `PROGRESS.md` normally and continue the usual evidence discipline.

### Existing challenge

- Read `STATE.md` first if it exists.
- Read the existing `PROGRESS.md` / `progress.md` before acting.
- Resume the strongest surviving branch instead of restarting ruled-out paths.

### Optional state and structure

- `STATE.md` is optional. Create/update it when a compact current-state snapshot materially helps a long, complex, multi-session, or multi-agent solve.
- A single `solve.py`, `exploit.py`, or helper may live directly in the challenge root. Create `scripts/` only when multiple scripts need organization.
- Create `artifacts/` only when multiple generated/recovered files need organization.
- Create `artifacts/logs/` only when raw evidence is actually worth preserving.

## Evidence discipline

- Separate `Confirmed`, `Inferred`, and `Hypothesis` statements. Do not promote a hypothesis without a reproducer or independent evidence.
- Give every important artifact a path and every network result a timestamp or request description when it matters for reproduction.
- Preserve raw command output in files when exact bytes, offsets, packets, errors, timing, heap state, crypto values, or binary structures matter. Summaries must link back to raw evidence when raw evidence is retained.
- Mark false positives and dead ends with the reason they were rejected so future sessions do not repeat them.
- Never treat a decoy, local example flag, readable plaintext, valid padding alone, or an unverified candidate as solved.
- After the first meaningful test, every important finding must be written to `PROGRESS.md`. Detailed entries are fine; do not drop useful technical evidence merely to keep notes short.

## Token and search discipline

- Run a short, high-information triage first, then inspect only the references and artifact regions relevant to the current primitive.
- Prefer `rg`, targeted `sed`, structured parsers, and saved raw logs over repeatedly printing entire files.
- If `STATE.md` exists, keep it compact: current facts, active primitive, dead ends, and the next three actions. Put chronological detail in `PROGRESS.md`.
- Automate repeated transforms or probes when useful; do not repeatedly reconstruct large one-off commands in chat.
- Use raw, unfiltered output for cryptography, disassembly, heap state, packet analysis, binary formats, and exploit debugging when exact values matter.
- Prefer locally installed skills and references. Do not fetch the skill library from GitHub during ordinary solving when the local copy is available.

## Execution loop

For a new challenge, bootstrap the folder and minimal progress file, then execute before documenting detailed startup state.

After solving has begun:

1. Establish a minimal reproducible observation.
2. Convert it into a named primitive such as read, write, leak, oracle, bypass, or code execution when applicable.
3. Validate the primitive independently before chaining it.
4. Record every important discovery, rejection, pivot, failure, exact blocker, or verification result in `PROGRESS.md`.
5. Update `STATE.md` only if it exists and a material discovery, pivot, failure, or handoff makes the compact snapshot stale.
6. Stop broad enumeration once evidence supports a narrower path.

The startup optimization changes only **when detailed documentation begins**. It does not weaken progress persistence after evidence exists.

## Completion

- A challenge is solved only when the final value is reproduced from the supplied or live challenge and matches the required format.
- Keep a deterministic solve or exploit script when practical.
- Ensure the decisive path and final verification are recorded in `PROGRESS.md` before ending the solve.
- After solving, extract only genuinely reusable techniques into skills. Do not store live tokens, challenge flags, hostnames, or narrative writeups in skills.
- For blind eval runs under `.ctf/eval-runs/`, obey the nested `AGENTS.override.md`; do not inspect source challenge folders, old writeups, answer hashes, memories, or web writeups when prohibited by the evaluation rules.
