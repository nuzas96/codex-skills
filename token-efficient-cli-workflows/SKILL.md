---
name: token-efficient-cli-workflows
description: Reduce token cost from terminal-heavy agent work by using compact command wrappers, output filtering, and on-demand detail expansion. Use when configuring RTK/Rust Token Killer, optimizing Hermes/Claude/Codex shell output, reviewing noisy build/test/git logs, or helping a token-conscious user choose lean workflows.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  created_by: agent
  tags: [tokens, cli, terminal, rtk, hermes, output-filtering]
---

# Token-Efficient CLI Workflows

Use this skill when the user wants lower token usage during terminal-heavy work, or when a session involves noisy command output such as git status/diff/log, test runners, build logs, directory listings, grep/search output, Docker/Kubernetes listings, or CTF recon commands.

## Core Principle

Default to compact, filtered outputs first, then expand only when the missing detail materially affects the next decision. For token-conscious users, explicitly call out the tradeoff between a lean path and a fuller/raw-output path.

## Workflow

1. Identify the noisy output source:
   - Git: `status`, `diff`, `log`, `show`.
   - Tests/builds: `pytest`, `cargo test`, `npm test`, `tsc`, `ruff`, `mypy`, etc.
   - Filesystem/recon: `ls`, `tree`, `find`, `grep`, `rg`, `strings`, `binwalk`.
   - Infra: `docker`, `kubectl`, cloud CLIs.
2. Use purpose-built agent tools when they are already compact and structured:
   - File reads: prefer `read_file` with pagination.
   - Searches: prefer `search_files` over raw grep/find when available.
   - Targeted edits: prefer `patch` over shell text manipulation.
3. Use RTK or compact shell wrappers for terminal-heavy paths:
   - If RTK is installed and initialized for the agent, normal terminal commands may be auto-rewritten.
   - If not auto-rewritten, call `rtk <command>` explicitly for supported commands.
4. Verify that compact output still preserves the evidence needed to act. If debugging depends on exact raw lines, rerun the command in raw mode or with narrower scope.
5. Track savings after meaningful usage with `rtk gain` when the user asks about token/cost impact.

## RTK for Hermes

RTK (Rust Token Killer) can be initialized as a Hermes plugin that rewrites terminal tool commands through `rtk rewrite` before execution.

Quick install/setup:

```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
rtk --version
rtk init --agent hermes --auto-patch
```

Verification:

```bash
rtk rewrite 'git status'
rtk rewrite 'ls -la'
rtk gain
```

Expected rewrite examples:

```text
git status -> rtk git status
ls -la     -> rtk ls -la
```

Hermes must be restarted after `rtk init --agent hermes --auto-patch` for automatic command rewriting to take effect. Before restart, direct `rtk ...` commands still work.

See `references/rtk-hermes.md` for the specific Hermes plugin files, verification commands, and caveats.

## CTF-Specific Token Discipline

For CTF sessions, compact output is useful for first-pass triage and noisy recon, but do not over-compress evidence needed for exploitation.

Good compact candidates:

```bash
rtk ls -la
rtk find '*.php' .
rtk grep 'flag\|secret\|admin' .
rtk git status
rtk git diff
```

Use raw/narrow output when exact bytes, offsets, stack traces, binary strings, or exploit responses matter:

```bash
xxd -g1 -l 256 file.bin
python3 exploit.py
nc host port
```

If using RTK with CTF recon commands like `strings` or `binwalk`, prefer saving raw artifacts to files and summarizing selected snippets, rather than losing potentially important rare lines.

## Lean instruction files

GitHub audit notes for project-rule/token saving patterns live in [agent-lean-rules.md](references/agent-lean-rules.md). Key rule: keep always-loaded instructions tiny; move large checklists, payload catalogs, and workflows into on-demand skills/references.

## Pitfalls

- Do not claim RTK affects every tool call. Hermes file tools such as `read_file`, `search_files`, and `patch` do not necessarily pass through RTK.
- Do not use compact output when the task requires exact raw evidence, precise error text, or byte-for-byte output.
- Do not run broad installer scripts blindly just to reduce tokens. Inspect or dry-run when possible, especially third-party tools.
- Avoid turning a transient setup problem into a permanent rule. Capture the setup/fix, not a negative claim that a tool is broken.

## User-Facing Summary Pattern

When reporting setup or workflow choices to a token-conscious user, keep it short:

```text
Lean path: compact output first, expand only if needed. Lowest token cost.
Full path: raw logs/output everywhere. More complete but expensive.
Recommendation: start lean, rerun raw for the exact failing area.
```
