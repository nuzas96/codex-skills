# Continuous Progress Discipline

This is a structural gate for active CTF solving. It exists because chat context, tool output and compressed history are not reliable long-term state.

## Mandatory pre-reply gate

For every active CTF turn:

```text
1. do the investigation/test
2. append new findings to PROGRESS.md/progress.md
3. only then send the user-facing reply
```

If a turn produced new information and the progress file was not updated, the turn is incomplete.

## What counts as a finding

Write even small results:

- hypothesis tested;
- primitive confirmed;
- primitive ruled out;
- exact error/change/no-signal result;
- new version/environment fact;
- new artifact or path;
- new endpoint/route/service;
- response difference;
- debugger/memory observation;
- next branch chosen because of evidence.

A one-line negative result is enough. The purpose is continuity, not polished prose.

Example:

```text
- 2026-08-23 00:31: Tested alternate JWT alg path; server rejects before signature verification. Rule out `alg:none` for current middleware.
- 2026-08-23 00:36: Bot UA confirms HeadlessChrome/149. Re-test browser primitive on exact version before trusting older notes.
- 2026-08-23 00:44: Next: compare nested GraphQL resolver authorization with root resolver.
```

## Pre-flight knowledge check

Before committing to a long attack chain, search installed/local category references for:

1. challenge name / author;
2. suspected primitive;
3. exact browser/library/runtime version;
4. CVE/GHSA/advisory identifier;
5. known empirical blocker.

The purpose is to avoid rebuilding an exploit path already known to be impossible on the target version.

A prior note saying a primitive failed on **another** version is not proof that it fails on the target version.

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

## Self-check before reply

Ask:

1. Did this turn produce any new information?
2. If yes, is that information already in the progress file?
3. If no, write it now before replying.

## Before declaring defeat

The progress gate does not decide whether the challenge is exhausted. If the next reply would say `stuck`, `blocked`, `unsolvable`, `can't solve`, or equivalent, run `stuck-recovery.md` first and write its findings into progress.

## Verification

During a long solve, periodically verify:

```bash
stat -c '%y %n' PROGRESS.md 2>/dev/null || stat -c '%y %n' progress.md

tail -n 20 PROGRESS.md 2>/dev/null || tail -n 20 progress.md
```

The most recent meaningful tool result should be represented there.

## Historical source

This V2 reference preserves the core behavioral mechanisms from V1 `progress-discipline` and the continuity sections of `ctf-desktop-workspace`. Full originals remain in `archive/pre-restructure-20260823`.