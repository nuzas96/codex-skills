# Browser Artifact Forensics

Use when a CTF provides Chromium-family profile data, browser databases/cache, a disk image containing browser profiles, or a browser timeline is needed to recover URLs, downloads, searches, sessions, extension activity or hidden challenge data.

## High-Value Chromium Artifacts

- `History` — URLs, visits, downloads, keyword searches.
- `Cookies` — domains, names, timestamps and encrypted values.
- `Web Data` — autofill and related form data.
- `Login Data` — credential metadata/encrypted values.
- `Bookmarks` — JSON tree.
- `Preferences` — settings and extension metadata.
- `Local Storage/`, `Session Storage/`, IndexedDB — application state.
- session/tab files and cache — recently viewed content.

Common profile roots include Chrome/Edge/Brave `User Data/<profile>` directories on Windows and corresponding `~/.config/...` paths on Linux.

## Workflow

1. Preserve the profile directory and note browser/version if recoverable.
2. Run Hindsight for a unified timeline when available.
3. Query SQLite artifacts directly when a particular answer/flag is easier to target.
4. Convert Chrome timestamps correctly: microseconds since 1601-01-01 UTC.
5. Correlate visits, downloads, searches, cookies/storage and filesystem timestamps.
6. Search recovered URLs/titles/values/download names for challenge-specific markers before broad manual browsing.

## Hindsight

Hindsight is useful for quickly normalizing Chromium artifacts to XLSX/JSON/SQLite. It should accelerate triage, not replace artifact-level verification. If Hindsight omits an edge-case record, inspect the underlying database/WAL/cache directly.

## SQLite Notes

Open evidence databases read-only or copy them first. Browser databases may have WAL/SHM companions containing newer/deleted state; preserve and analyze those with the main DB.

Useful `History` relationships include `visits -> urls`, `downloads`, and `keyword_search_terms`. Reconstruct chronology instead of treating each table independently.

## CTF-Specific Checks

- URLs visited only once immediately before/after a suspicious event.
- download source URL vs final target filename.
- searches containing fragments of flag/key/path.
- local-storage/session values from a challenge site.
- extension IDs and extension config.
- deleted/recent records in SQLite freelists/WAL when the visible DB lacks the answer.
- browser profile copied from a bot/admin session; cookies may be encrypted and require OS/browser-key context rather than simple SQLite extraction.

## Common Failure Modes

- Copying only the main SQLite file and losing WAL state.
- Misreading Chrome timestamps as Unix epoch.
- Assuming `Login Data` plaintext values are directly recoverable without OS encryption context.
- Running one parser and declaring absence without querying the raw artifacts.
- Ignoring Local Storage/IndexedDB because History has no flag.

## Provenance

Consolidated from the original `analyzing-browser-forensics-with-hindsight` Apache-2.0 skill and existing `ctf-forensics` browser/SQLite notes. Original source remains frozen on `archive/pre-restructure-20260823`.
