# CTF Workspace and Continuity

This reference defines the live workspace used by `ctf-solve`.

## Canonical location

Unless the user explicitly gives another working directory, create or resume:

```text
/home/nuzhmi/Desktop/hermes-ctf/<challenge-name>/
```

Inside it, use one canonical progress file:

1. existing `PROGRESS.md` if present;
2. otherwise existing `progress.md` (do not rename it);
3. otherwise create `PROGRESS.md`.

Do not scatter the live solve across multiple note files.

## Start/resume procedure

1. Normalize the challenge name/path.
2. Check whether the challenge folder already exists.
3. Read the existing progress file **before new exploration**.
4. Record the user-provided identifier, URLs, files, hashes, known credentials/cookies supplied for the CTF, flag format and current blocker.
5. Reuse the strongest surviving branch; do not restart paths already ruled out by evidence.
6. Store new artifacts in the challenge folder with descriptive names.

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

The workspace may be shared by another agent, terminal or human editor.

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
- Read progress first on resume.
- Use compact filtered recon before broad dumps.
- Stop broad fuzzing when responses become repetitive and move to the strongest validated clue.
- Preserve generated exploit/solver scripts rather than relying on chat-only snippets.

## Historical source

V2 consolidates the unique workspace behavior from V1 `ctf-desktop-workspace`. The original remains frozen at `archive/pre-restructure-20260823` for audit/rollback.