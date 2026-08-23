---
name: agent-maintenance
description: "Maintain the agent environment around CTF work: reduce noisy CLI/token usage, debug or tune context compression, and keep always-loaded instructions lean. Use when asked about token efficiency, compact terminal workflows, unexpected context compression, threshold or tool-schema overhead, or agent configuration rather than a CTF challenge."
---

# Agent Maintenance — V2 Router

This domain is intentionally separate from CTF challenge knowledge. Agent/runtime configuration should not compete with `ctf-web`, `ctf-pwn`, etc. during normal challenge routing.

## Reference router

- Noisy terminal output / RTK / lean command usage -> [references/token-efficiency.md](references/token-efficiency.md)
- Unexpected Hermes compaction / threshold/tool-schema questions -> [references/context-compression.md](references/context-compression.md)

## Core rule

Keep always-loaded instructions and skill entrypoints small. Move long checklists, environment-specific debugging notes and technique catalogs into references loaded only when needed.

## Environment verification

Before changing an agent setting:

1. inspect the installed version/config;
2. distinguish model/provider/backend limits from local UI assumptions;
3. change the smallest relevant setting;
4. restart/reload only the process that actually owns the setting;
5. verify behavior rather than assuming the command succeeded.

## Relationship to CTF skills

`ctf-solve` may use compact-output principles during recon, but it should not load this skill unless token/runtime configuration is itself being debugged. The CTF progress file remains the continuity mechanism even when context compression is tuned.

## V1 provenance

Consolidates V1 `token-efficient-cli-workflows` and `hermes-context-compression`. Their originals remain frozen at `archive/pre-restructure-20260823` until V2 migration validation is complete.
