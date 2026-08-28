# CTF Codex Workspace

All new authorized CTF challenge work belongs here.

Each challenge uses its own subfolder under:

```text
/home/nuzhmi/Desktop/ctf-codex/<challenge-name>/
```

The only mandatory file at initial bootstrap is:

- `PROGRESS.md` for chronological progress and evidence continuity.

For a brand-new challenge, `PROGRESS.md` starts minimal and Codex should perform the first meaningful solve/triage action immediately. Detailed progress writing begins after that first test produces evidence.

After solving has begun, important findings, dead ends, pivots, exact blockers, relevant versions/offsets, recovered artifacts, and final verification must be recorded in `PROGRESS.md` as usual.

Additional workspace structure is created only when useful:

- `STATE.md` for a compact current-state snapshot on long/complex/multi-session work;
- `scripts/` when multiple repeatable probes/solvers/exploits need organization;
- `artifacts/` when multiple generated or recovered files need organization;
- `artifacts/logs/` when exact raw evidence is worth preserving.

Do not create empty structure merely because a template lists it.

The operating rules are defined in this workspace's `AGENTS.md`.
