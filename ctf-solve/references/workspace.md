# CTF Workspace and Continuity

This reference defines the live workspace used by `ctf-solve` in the user's local Codex/Kali environment.

## Runtime ownership

This workspace behavior is for the local Codex environment. The authoritative workspace policy is:

```text
/home/nuzhmi/Desktop/ctf-codex/AGENTS.md
```

The GitHub repository is the upstream/source copy of the skill library. Normal Codex solves should use the locally installed skills under:

```text
/home/nuzhmi/.codex/skills/
```

The local Git worktree used to maintain/sync the skill source is:

```text
/home/nuzhmi/Desktop/codex-skills-github/
```

Do not make normal Codex solving depend on network/GitHub retrieval when the local installed copy is available.

## Canonical challenge location

Unless the user explicitly gives another working directory or the active `AGENTS.md` defines a more specific project path, create or resume:

```text
/home/nuzhmi/Desktop/ctf-codex/<challenge-name>/
```

`/home/nuzhmi/Desktop/hermes-ctf/` is a stale historical path and must not be used as the default.

## Minimal bootstrap for a new challenge

The initial workspace must be intentionally small so filesystem/documentation setup never blocks an obvious solve.

For a brand-new challenge, create only:

```text
<challenge-name>/
└── PROGRESS.md
```

`PROGRESS.md` may contain only a heading/status at creation time. Immediately after bootstrap, perform the first meaningful solve/triage action **before** populating detailed progress notes.

Do not create these merely because a template mentions them:

- `STATE.md`
- `scripts/`
- `artifacts/`
- `artifacts/logs/`

Create them lazily only when the solve actually benefits from them.

A lightweight helper may be used:

```text
ctf-solve/scripts/ctf-init
```

When installed into the workspace helper location, it should create/resume the challenge folder plus minimal `PROGRESS.md` and return the challenge path. It must not perform analysis or generate a full project scaffold.

## Start/resume procedure

### New challenge

1. Read `/home/nuzhmi/Desktop/ctf-codex/AGENTS.md` when present.
2. Normalize the challenge name/path.
3. Create/resume the dedicated challenge folder.
4. Ensure `PROGRESS.md` exists; if new, keep it minimal.
5. Put/copy supplied artifacts into the challenge folder when practical without mutating originals.
6. Immediately run the strongest cheap, meaningful test.
7. After that test produces evidence, update `PROGRESS.md` normally and continue evidence-first solving.

Do **not** spend the pre-test phase writing hypotheses, environment summaries, planned actions, or empty directory structures.

### Existing challenge

1. Enter the existing challenge folder; never create a duplicate.
2. Read `STATE.md` if it exists.
3. Read the existing `PROGRESS.md` / `progress.md` before new exploration.
4. Reuse the strongest surviving branch; do not restart paths already ruled out by evidence.
5. Continue normal progress discipline immediately; the new-challenge startup exception no longer applies.

## Lazy workspace expansion

### `STATE.md`

Optional. Create it when a compact current-state snapshot materially helps, especially for:

- long or multi-session challenges;
- multi-agent/parallel-terminal work;
- complex Boot2Root or multi-stage exploit chains;
- very long `PROGRESS.md` histories where resume cost becomes high.

Do not require `STATE.md` for a short single-session challenge.

### Scripts

A dedicated `scripts/` directory is optional. A single `solve.py`, `exploit.py`, or helper may live directly in the challenge folder. Create `scripts/` when multiple reusable scripts would otherwise clutter the root.

### Artifacts and logs

Create `artifacts/` only when multiple generated/recovered artifacts need organization. Create `artifacts/logs/` only when raw logs are valuable for exact evidence or later reproduction.

Never create empty artifact/log directories merely to satisfy structure.

## What belongs in progress

After the first meaningful test, record detailed, reproducible state as usual:

- target/service identifiers;
- supplied artifact names and hashes when relevant;
- exact dependency/browser/libc/runtime versions that affect exploitability;
- confirmed primitives;
- failed branches and why they failed;
- request/response or debugger evidence needed to resume;
- generated scripts/payload paths;
- current strongest next action;
- final verified flag/artifact when solved.

Preserve exact error strings and paths because they are good retrieval handles after context compression.

## End-of-turn and handoff

Live findings are persisted continuously via `progress.md` rules after solving has begun. Before stopping a session, make sure the final entry is one of:

- **Solved:** decisive path + final verified artifact/flag; or
- **Partial:** exact blocker + tested branches + strongest next action + environment quirks.

## Multiple writers / parallel terminals

The workspace may be shared by another Codex session, terminal or human editor.

- Treat file modification time and changed content as freshness signals.
- Re-read before patching if the file changed since the last read.
- Append/patch; never replace the entire progress file mid-solve.
- Notes written by another session are collaborative evidence, not noise.

## Language

- Conversation may use natural Bahasa Melayu + English technical terms.
- Files, scripts, code comments and writeups default to English unless the user explicitly asks otherwise.
- Commands/code remain in their canonical technical form.

## Optional long-term knowledge migration

A live `PROGRESS.md` is the source of truth during a solve. Do not automatically copy every milestone into Obsidian or another knowledge base. Long-term migration should be explicit and condensed:

```text
raw live timeline -> distilled technique/lesson -> long-term knowledge base
```

Do not duplicate the raw progress log as a permanent knowledge note.

## Efficiency rules

- One challenge folder per challenge.
- `PROGRESS.md` is mandatory; detailed pre-test population is not.
- First meaningful execution comes before detailed startup documentation.
- After evidence exists, important findings must be persisted normally.
- `STATE.md`, `scripts/`, `artifacts/`, and `logs/` are lazy/on-demand.
- Read state/progress first on resume.
- Use local installed skills/references before any GitHub/network retrieval.
- Stop broad fuzzing when responses become repetitive and move to the strongest validated clue.
- Preserve generated exploit/solver scripts rather than relying on chat-only snippets.

## Historical source

V2 consolidates the unique workspace behavior from V1 `ctf-desktop-workspace`, but the old `hermes-ctf` default from that archived skill was superseded by the later Codex workspace at `/home/nuzhmi/Desktop/ctf-codex/`. This revision also removes unnecessary full-scaffold startup overhead while keeping detailed progress persistence after the first meaningful solve action. The V1 original remains frozen at `archive/pre-restructure-20260823` for audit/rollback.