# V1 -> V2 Orchestrator Provenance

This file records the V1 sources consolidated into `ctf-solve` so unique behavior can be audited during migration.

Frozen source branch: `archive/pre-restructure-20260823`

| V1 source | V1 blob SHA | V2 destination |
|---|---|---|
| `solve-challenge/SKILL.md` | `70b1922ba0a951e89813cf7c2ee903eefac8fb17` | `ctf-solve/SKILL.md`, `triage-routing.md` |
| `ctf-desktop-workspace/SKILL.md` | `da74764a3ccda23a9503b3c5396bdcfc65c9396d` | `workspace.md`, `progress.md` |
| `progress-discipline/SKILL.md` | `78a940c00a49f1bb31a3aecbc1b90d01aa79c16f` | `progress.md` |
| `ctf-stuck-recovery/SKILL.md` | `4ca7e2608a6186a0166fdbd2e6db28ed671b82ea` | `stuck-recovery.md` |
| `ctf-modern-chains/SKILL.md` | `f47ebb8bcae34eb9a9fa08120bd4fae558f3535d` | `modern-chains.md` |
| `ctf-modern-chains/references/web.md` | `09c94d0e7e203c6e931aa4a6a8e091b2a7d3282a` | redistribute to `ctf-web/references/` |
| `ctf-modern-chains/references/pwn.md` | `1db987571a5a7f18c0ccb80a4e4fc7701c7c6787` | redistribute to `ctf-pwn/references/` |
| `ctf-modern-chains/references/artifacts-reverse.md` | `f07344a0f67107d09c6e02e50b56762b62e2c7aa` | split between `ctf-forensics` and `ctf-reverse` |
| `ctf-modern-chains/references/crypto-misc.md` | `d4e5fb377172c2ea31fe904554e0c2858819c7ca` | split between `ctf-crypto`, `ctf-web`, and `ctf-misc` |

## Preservation policy

An old top-level directory is not deleted merely because its name appears in this table. Deletion waits until:

1. all unique instruction content has a V2 destination;
2. its supporting `references/`, `scripts/` and `assets/` have been audited;
3. attribution/license requirements are preserved;
4. repository search finds no unresolved incoming links that still require the old path;
5. representative activation/solve tests pass.

The archive branch remains the authoritative historical copy even after migration.