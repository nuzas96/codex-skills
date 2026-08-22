---
name: progress-discipline
description: Enforce continuous PROGRESS.md updates during CTF/exploit work. The user gets frustrated when context compacts and findings are lost. This skill installs a hard pre-reply mechanism that forces a write to PROGRESS.md (or progress.md) before any reply text is sent. Load this skill at the start of every CTF/exploit session and apply the pre-reply check on EVERY turn.
---

# PROGRESS.md Discipline — Pre-Reply Hard Gate

The user has been burned multiple times by losing CTF progress when context compacts or resets. The fix is NOT promises or memory rules — those fail under load. The fix is a **hard pre-reply gate** baked into the turn structure.

## When to apply

Any turn that includes ANY of:
- CTF challenge work (web/pwn/crypto/reverse/forensics/misc/osint/malware/ai-ml)
- Exploit development, payload testing, hypothesis testing
- Bug bounty recon / vuln research with progress-style work
- Long multi-step investigation where context loss is a real risk

## Pre-flight: Check Skill References FIRST (before planning attack)

Before planning an attack chain or committing to a primitive, **grep your skill references for the challenge name, author, or technique**. Prior sessions often already documented empirical blockers (browser version compat, library CVEs, dead ends) that would invalidate the plan.

**Why this matters:** the failure mode observed in real sessions — agent plans a 20-minute attack chain (DOMPurify mXSS, CRLF injection, custom bypass), commits to PROGRESS.md, sets up infrastructure, fires the exploit, then discovers the chain is blocked by a Chrome-version-specific patch that was ALREADY documented in a prior session's reference. The 20 minutes were wasted; the agent should have grep'd first.

**Concrete pre-flight checks before planning an attack chain:**

1. **Search by challenge name/author/handle.** Use `search_files` or `rg` over `~/.hermes/skills/`:
   ```bash
   rg -l "challenge-name\|author-name\|technique-name" ~/.hermes/skills/*/references/
   ```
2. **Search by primitive.** If you plan to use `DOMPurify mXSS`, search for it:
   ```bash
   rg -l "DOMPurify.*mxs\|mxs.*DOMPurify" ~/.hermes/skills/
   ```
3. **Search by browser/library version.** If the bot is Chrome 149, search for `Chrome 149` and `149` in references — the empirical verdict is usually already there.
4. **Search by CVE/GHSA.** If you plan to use a known bypass, search for the CVE id.
5. **Read the matching reference FIRST** (not after committing). If it says "blocked on Chrome X+", pivot to a different primitive immediately.

**When to skip the check:** novel challenge name you've never seen, fresh technique not in any reference, or `0 solves globally` challenges where no prior session has touched it (in which case you ARE the empirical source — write your findings for future sessions).

**What to do if the reference confirms your plan is blocked:**
- Don't grind. Pivot to a different primitive, OR declare defeat and report honestly to the user.
- Don't re-test the blocked primitive hoping it works "this time" — the empirical ceiling has been hit.
- Update the reference with any new finding (e.g., "confirmed blocked on Chrome 150 too — still dead").

This is a structural rule, not a "remember to check" rule. Build the grep into the start of any CTF solve, the same way the pre-reply gate is built into every turn.

## The Pre-Reply Gate (mandatory, every turn)

The reply structure for a CTF turn MUST be:

1. **Do the work** — tool calls for the actual investigation/test/exploit
2. **APPEND to PROGRESS.md** — patch/write_file with any new findings (positive, negative, observations, dead-ends, hypotheses)
3. **THEN send the text reply** — explanation/conclusion comes AFTER the write

**Rule:** If a turn produced any new finding AND the response text is ready, the PROGRESS.md patch MUST happen before the text reply is sent. No exceptions.

**Adjacent rule — before declaring blocked:** If you find yourself writing "I'm stuck", "this is unsolvable", "empirical ceiling has been hit", or similar defeat language, **stop and load `ctf-stuck-recovery` BEFORE writing the defeat summary**. That skill enforces a 7-point enumeration checklist (source-code audit completeness, endpoint enumeration, CVE freshness, primitive verification on the EXACT bot version, author hint interpretation depth, CTF-infra paths, user communication). The user has repeatedly pushed back on premature defeat declarations — other solvers can solve it, so the technique exists. Don't ship a "blocked" summary without walking the checklist first.

## Trigger phrases that FORCE a write

When you find yourself about to say any of these, write FIRST, then say it:

- "I tested X and it..."
- "Hypothesis: ..."
- "Confirmed: ..."
- "Dead end: ..."
- "I noticed ..."
- "Tried X. Failed because Y."
- "Next: ..."
- "Partial result: ..."
- "This rules out ..."
- "Looks like the oracle is ..."

If you have a finding but didn't write — write it as a one-liner. Even "tested X, failed, no signal" is enough. PROGRESS.md > clean context.

## Self-check (before sending text reply)

Ask yourself:
1. Did this turn produce any new information? (test result, observation, hypothesis, ruled-out path, new artifact)
2. If YES — did I already patch PROGRESS.md with it?
3. If NO to (2) — **WRITE FIRST, then send reply**.

This is the verification gate. Run it mentally every turn. It takes <1 second and prevents the "I forgot to write" failure mode.

## Write style (keep it minimal)

Append entries with a short timestamp prefix. Examples:

```
- 2026-06-19 14:32: Tested `<object>` without width/height. Both 200/404 still create same frame count. Hypothesis ruled out.
- 2026-06-19 14:35: Noticed: DOMPurify preserves `<style>` only when inline on element, not as block tag. Try inline style on parent.
- 2026-06-19 14:40: Dead end: contentDocument cross-origin access. Blocked by SOP. Don't retry.
- 2026-06-19 14:45: Next: lazy `<img loading=lazy>` + sibling layout trick — `<object>` size differential pushes sibling out of viewport.
```

One line per finding. Don't overformat. Don't rewrite history. Append.

## Where to write

- Prefer existing `PROGRESS.md` in the active challenge folder.
- If only `progress.md` exists (lowercase), use that — do NOT rename.
- If neither exists and this is a fresh challenge, follow `ctf-desktop-workspace` skill to create one FIRST.
- Always patch/append — never overwrite the whole file mid-solve.

## What this skill does NOT do

- It does NOT auto-update Obsidian vault (that's a separate dormant flow, see `ctf-desktop-workspace`).
- It does NOT replace writing English writeups later.
- It does NOT force writes for non-CTF work (general chat, one-off shell, no-progress context).

## Verification

The user will check. If a turn produced findings and PROGRESS.md doesn't show them, the discipline failed. The user has called this out multiple times — treat the next occurrence as a regression that needs immediate patch.

Concrete checks (use any time, especially after a long turn or compaction):

1. **Last-entry timestamp.** `stat -c '%y' PROGRESS.md` — should be within the last few minutes if work is active.
2. **Grep for the most recent test result.** If the latest tool call produced "test X failed because Y" and the file's last entry doesn't mention it, write was skipped.
3. **Cross-check the todo list.** If the todo had items like "test hypothesis 1/2/3" and they're all completed but the file doesn't show results, the discipline failed.
4. **User pushback as signal.** If the user says something like "kenapa tak update PROGRESS.md?" or "tk update pon" — the discipline failed. Patch the workflow AND acknowledge the gap in the file.

## How this skill relates to others

- **Workspace setup, folder creation, file naming** → `ctf-desktop-workspace` (the umbrella for "how to start a solve")
- **When and how to write PROGRESS.md during the solve** → this skill (`progress-discipline`)
- **One-shot vault migration after solve** → `ctf-desktop-workspace` (Obsidian section) + `obsidian` skill
- **Polished writeup for handoff/submission** → `ctf-writeup` (use after the flag is captured, not for live progress)

## Why memory rules alone don't work (expanded)

Three reasons observed in real sessions:

1. **Memory is read on every turn but doesn't create triggers.** A rule like "always update PROGRESS.md" sits in the context as text. Under tool-use load (3+ tool calls, hypothesis branching, parallel exploration), the rule gets deprioritised below the immediate task. The agent finishes the work, generates the text reply, and forgets to write.

2. **Context compaction is aggressive by default.** Hermes `compression.threshold` defaults to 0.5, and the preflight check counts system prompt + tool schemas (20-30K+ tokens) + messages. So a session can look "not full" in the visible status bar (which only updates on successful API responses) while the preflight check sees the conversation as past threshold and compresses it. The agent that "had a lot of context" suddenly has none — and the PROGRESS.md is the only thing that survived. If it's not current, the solve is lost. This is why the pre-reply gate exists: even if compaction happens, the file is up to date. See `references/hermes-context-compression.md` (under `ctf-desktop-workspace`) for the full mechanism and threshold fix.

3. **The visible status bar lies.** It shows the last successful API response's token count. After an interrupt, error, or compression, the bar is stale. A future agent that reads the bar and decides "we have room" is wrong — the next preflight will see the real total and may compress. Trust PROGRESS.md, not the bar.

The pre-reply gate works because it's a **structural change to the turn output**, not a rule to remember. Lean on the structure, not the memory.
