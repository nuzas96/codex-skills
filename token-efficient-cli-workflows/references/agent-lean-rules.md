# Agent Lean Rules for Token-Conscious Workflows

Sources audited:
- https://github.com/drona23/claude-token-efficient
- https://github.com/rtk-ai/rtk
- https://github.com/opensquilla/opensquilla

Purpose: keep durable instructions short enough that they save more output tokens than they cost as repeated input tokens.

## What to keep in project rules

Use short rules that change frequent behavior:

- Be thorough in reasoning, concise in output.
- Lead with the result, not a preamble.
- Use compact command output first; expand only where exact evidence matters.
- Read relevant files before editing; do not invent APIs or symbols.
- For CTF: hypothesis -> smallest test -> evidence -> next action; update PROGRESS.md before replying.
- Summarize changed files and real verification output only.

## What to avoid

- Long style manifestos loaded every turn.
- Rules already handled by the system prompt or tools.
- Generic anti-AI wording rules that modern models already follow.
- Huge copied prompt packs; persistent input cost can exceed output savings.
- Forcing terse output during exploratory architecture or debugging when tradeoffs matter.

## Token economics

Instruction files are input tokens on every turn. They are only net-positive when they reliably reduce repeated output or tool noise. If a rule is rarely triggered, move it into a skill/reference loaded on demand instead of project context.

## Recommended hierarchy

1. Global memory: only stable preferences and environment facts.
2. Project `.hermes.md` / `AGENTS.md`: 5-15 high-frequency rules.
3. Skills: procedures and domain playbooks loaded only when relevant.
4. References/templates: large checklists, payload catalogs, and command snippets.
5. Raw repos in `/tmp`: grep/read on demand, not loaded into context.

## CTF lean mode

For CTF sessions, optimize for evidence density, not maximum compression:

- Compact: `git status`, directory listing, route inventory, package manifests, broad grep counts.
- Raw/narrow: exploit output, network responses, binary offsets, stack traces, exact parser behavior.
- Save raw artifacts to files, then quote only the lines that decide the next action.

## Example small project rule block

```markdown
# Lean Agent Rules
- Be concise in final replies; no preamble unless needed.
- Use compact output first; rerun raw only for exact failing area.
- Before edits: inspect definitions/usages, then patch only needed files.
- For CTF: hypothesis -> smallest test -> evidence -> PROGRESS.md -> next action.
- Report real verification output; don't promise future steps.
```
