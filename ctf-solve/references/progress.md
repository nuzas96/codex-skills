# Continuous Progress Discipline

This is a structural gate for active CTF solving. It exists because chat context, tool output and compressed history are not reliable long-term state.

## New-challenge startup exception

`PROGRESS.md` remains mandatory for every challenge, but a brand-new challenge must not spend time populating detailed notes before the first meaningful solve attempt.

For a new challenge:

```text
1. create/resume the dedicated challenge folder
2. ensure PROGRESS.md exists with only a minimal heading/status if it is new
3. immediately run the strongest cheap, meaningful solve/triage test
4. after that first test produces evidence, record the result in PROGRESS.md
5. continue normal progress discipline from that point onward
```

Do **not** delay the first meaningful test to write initial hypotheses, environment inventories, next-action lists, category essays, or workspace metadata. Those details should be written only after evidence exists and only when they matter.

This exception applies only to the startup of a **new** challenge. When resuming an existing challenge, read its existing progress/state before new exploration.

## Mandatory progress gate after the first meaningful result

Once the first meaningful test has produced evidence, the normal gate applies for the rest of the solve:

```text
1. do the investigation/test
2. append important new findings to PROGRESS.md/progress.md
3. continue the solve / send the user-facing reply
```

Do not skip important findings merely to save time. The optimization is about avoiding documentation **before evidence exists**, not weakening evidence persistence after solving has begun.

A turn/session that produced important new information and leaves it only in transient chat/tool context is incomplete.

## What counts as an important finding

Record anything that may affect the current solve or a future resume, including:

- hypothesis tested;
- primitive confirmed;
- primitive ruled out;
- exact error/change/no-signal result that rejects or narrows a path;
- relevant version/environment fact;
- new artifact or path;
- new endpoint/route/service;
- response difference;
- debugger/memory observation;
- exploitable offset/address relationship or cryptographic relation;
- successful or failed bypass with evidence;
- pivot reason;
- next branch chosen because of evidence;
- flag candidate and its verification status.

The entry may be concise or detailed. Do not shorten useful technical evidence merely for formatting speed. Preserve exact values when they matter for reproduction.

Housekeeping alone does not need a progress entry unless it changes the solve. Examples that normally do not need logging: `pwd`, `cd`, creating the challenge folder, or creating an empty helper directory.

## Pre-flight knowledge check

Before committing to a long attack chain, search installed/local category references for:

1. challenge name / author;
2. suspected primitive;
3. exact browser/library/runtime version;
4. CVE/GHSA/advisory identifier;
5. known empirical blocker.

The purpose is to avoid rebuilding an exploit path already known to be impossible on the target version.

A prior note saying a primitive failed on **another** version is not proof that it fails on the target version.

For a brand-new challenge, this knowledge check must not become a reason to postpone an obvious, cheap first test. If the supplied artifact exposes a direct high-confidence test, run it first.

## Do not loop on theory

After a small amount of reasoning, if a hypothesis has a cheap discriminating test, run it. In browser/parser/version-dependent CTFs, a five-second empirical test is often worth more than repeated speculation.

Use:

```text
hypothesis -> minimal test -> logs/result -> record -> iterate
```

Do not spend multiple turns trying to theoretically prove a cheap-to-test behavior.

## Append-only behavior

- Prefer existing `PROGRESS.md`.
- If only `progress.md` exists, keep that name.
- Never rewrite history simply to make notes cleaner.
- Patch/append rather than overwrite the whole file.

When multiple sessions write the same file, re-read recent content before appending if mtime/content changed.

## Self-check before reply or major pivot

Ask:

1. Did the latest meaningful work produce information that matters to the solve or resume?
2. If yes, is that information already in the progress file?
3. If no, write it before leaving the branch, ending the session, or sending a handoff.

The first meaningful test of a brand-new challenge is the only startup exception: run the test first, then record its evidence.

## Before declaring defeat

The progress gate does not decide whether the challenge is exhausted. If the next reply would say `stuck`, `blocked`, `unsolvable`, `can't solve`, or equivalent, run `stuck-recovery.md` first and write its findings into progress.

## Verification

During a long solve, periodically verify:

```bash
stat -c '%y %n' PROGRESS.md 2>/dev/null || stat -c '%y %n' progress.md

tail -n 20 PROGRESS.md 2>/dev/null || tail -n 20 progress.md
```

The recent important evidence should be represented there.

## Historical source

This V2 reference preserves the core behavioral mechanisms from V1 `progress-discipline` and the continuity sections of `ctf-desktop-workspace`, while removing the startup behavior that documented a new challenge before attempting the first meaningful solve action. Full originals remain in `archive/pre-restructure-20260823`.