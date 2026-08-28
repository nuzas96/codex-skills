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

Inside the challenge folder, use one canonical progress file:

1. existing `PROGRESS.md` if present;
2. otherwise existing `progress.md` (do not rename it);
3. otherwise create `PROGRESS.md`.

Do not scatter the live solve across multiple note files.

## Start/resume procedure

1. Read `/home/nuzhmi/Desktop/ctf-codex/AGENTS.md` when present and obey its project-local workflow.
2. Normalize the challenge name/path.
3. Check whether the challenge folder already exists under `/home/nuzhmi/Desktop/ctf-codex/` or the explicit path supplied by the user.
4. Read the existing progress file **before new exploration**.
5. Record the user-provided identifier, URLs, files, hashes, known credentials/cookies supplied for the CTF, flag format and current blocker.
6. Reuse the strongest surviving branch; do not restart paths already ruled out by evidence.
7. Store new artifacts/scripts in the challenge folder with descriptive names.

A sparse new challenge should still get a workspace and an initial `triage` state.

## What belongs in progress

Record concise, reproducible state:

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

Live findings are persisted continuously via `progress.md` rules. Before stopping a session, make sure the final entry is one of:

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

- One challenge folder, one live progress log.
- Read `AGENTS.md` and progress first on resume.
- Use local installed skills/references before any GitHub/network retrieval.
- Use compact filtered recon before broad dumps.
- Stop broad fuzzing when responses become repetitive and move to the strongest validated clue.
- Preserve generated exploit/solver scripts rather than relying on chat-only snippets.

## Historical source

V2 consolidates the unique workspace behavior from V1 `ctf-desktop-workspace`, but the old `hermes-ctf` default from that archived skill was superseded by the later Codex workspace at `/home/nuzhmi/Desktop/ctf-codex/`. The V1 original remains frozen at `archive/pre-restructure-20260823` for audit/rollback.