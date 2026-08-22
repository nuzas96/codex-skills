# SQLite Forensics

Use when a CTF artifact is an SQLite database or an application/browser/mobile artifact stores evidence in SQLite, especially when the visible rows do not contain the answer and deleted/history state may survive in WAL, freelists or page slack.

## Preserve the Database Family

Copy/preserve together when present:

- main database;
- `-wal` write-ahead log;
- `-shm` shared-memory file;
- journal file.

Opening the database normally may checkpoint/modify state. Work on a copy and use read-only modes where possible.

## First Pass

1. Verify `SQLite format 3` magic and page size.
2. List schema/tables/indexes/triggers with `sqlite3`.
3. Query high-value active rows/timestamps first.
4. Inspect WAL before manual carving; it often contains newer historical pages in a much cleaner form.
5. If needed, inspect freelist pages, freeblocks and unallocated page regions for deleted content.

## WAL

WAL consists of a header followed by frames containing page number + page data. Multiple historical versions of the same page may exist. For timeline-style CTFs, replay/compare frames to reconstruct prior application states rather than just grep the WAL as raw bytes.

## Freelist / Deleted Records

SQLite deletion may leave bytes in:

- freelist leaf pages;
- freeblocks within active B-tree pages;
- unallocated area between cell pointer array and cell content;
- older WAL frames.

Recovery becomes schema/record-format aware; simple `strings` can find clues but may merge unrelated bytes.

## CTF Edit-History Pattern

Some applications store insert/delete diffs or document versions in SQLite. The flag may have existed briefly and then been deleted. Reconstruct states sequentially from the diff/history table instead of only searching deleted raw bytes.

## Timestamp Decoding

Application timestamps vary: Unix seconds/milliseconds/microseconds, Chrome/WebKit epoch, Apple epoch, Windows FILETIME, custom integers. Infer from magnitude/schema/application rather than applying one conversion globally.

## Browser / Mobile Databases

When the DB comes from Chrome or another app, route application-specific schema interpretation to the relevant artifact reference (`browser-artifacts.md`, mobile/Windows notes). SQLite internals are the recovery layer; the app schema supplies meaning.

## Common Failure Modes

- Copying main DB without WAL and losing latest/deleted state.
- Opening original evidence in a GUI that checkpoints WAL.
- Grepping freelist bytes without understanding record boundaries/schema.
- Assuming a deleted SQL row is immediately zeroed.
- Applying Unix epoch to every integer timestamp.
- Stopping at current rows when challenge wording hints at deleted/history/edit state.

## Provenance

Consolidated from the original `performing-sqlite-database-forensics` Apache-2.0 skill and existing `ctf-forensics` disk/browser SQLite patterns. Original source remains on `archive/pre-restructure-20260823`.
