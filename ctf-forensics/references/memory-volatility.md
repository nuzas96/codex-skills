# Memory Forensics with Volatility 3

Use when a challenge provides RAM/raw/LiME/crash dump or when secrets/process/network/filesystem artifacts must be recovered from memory.

## First Pass

1. Identify dump format/OS architecture with `file`, Volatility banners/info and challenge context.
2. Confirm symbols/profile requirements before assuming plugin failure means absence.
3. Run a small triage set, not every plugin:
   - process list/tree/scan;
   - command lines/environment;
   - network connections;
   - file/MFT scanning;
   - suspicious memory mappings only when malware/injection is relevant.
4. Search strings for challenge markers in parallel when the flag format is known.
5. Dump only targeted processes/files/regions after triage identifies a lead.

## Windows High-Value Plugins

Common Volatility 3 paths include:

- `windows.info`
- `windows.pslist`, `windows.pstree`, `windows.psscan`
- `windows.cmdline`, `windows.envars`
- `windows.netscan`
- `windows.filescan`, `windows.dumpfiles`
- `windows.mftscan`
- registry hive/key plugins
- `windows.dlllist`
- `windows.malfind` when injection is suspected

Plugin names change across versions; verify current Volatility 3 syntax instead of copying Volatility 2 names such as `mftparser` blindly.

## CTF Recovery Patterns

### Process / command secrets

Command-line arguments, environment variables, shell history buffers, application process strings and configuration may expose the answer without full malware analysis.

### Deleted files / MFT fragments

A deleted file may survive in MFT records or memory-resident file objects. `windows.mftscan`/`filescan` can locate metadata even when normal filesystem extraction fails. For resident NTFS data or older Volatility 2-specific techniques, use the repository's advanced disk/memory notes and verify tool version.

### Dump process memory

When a process clearly owns the interesting state, dump its mapped memory/files and search locally rather than running global expensive scans repeatedly.

### Encryption keys / credentials

Determine the application/key format first. Memory may hold decrypted key material, tokens, database handles, browser secrets or crypto state, but generic `grep password` is only a starting point.

## Linux

Linux Volatility analysis requires matching symbols for the kernel. If symbols are unavailable, raw strings, process/core artifacts, LiME metadata, `/proc`-like reconstruction, and application-specific analysis may be cheaper than forcing a full plugin stack.

## Malware Overlap

Use `malfind`, YARA, module comparisons and injection analysis only when malicious-code behavior is central. If the main problem becomes understanding a malware sample, add `ctf-malware`; do not load it for every RAM dump.

## Common Failure Modes

- Using Volatility 2 plugin names/profiles against Volatility 3.
- Running dozens of plugins before identifying OS/version.
- Assuming symbol failure means the artifact is absent.
- Dumping everything and losing the signal in gigabytes of output.
- Ignoring simple command-line/env/strings evidence because a sophisticated memory framework is available.
- Forgetting timeline correlation between process, network and file artifacts.

## Provenance

Consolidated from the original `performing-memory-forensics-with-volatility3` Apache-2.0 skill and existing `ctf-forensics/disk-and-memory.md` / advanced memory notes. Original source remains on `archive/pre-restructure-20260823`.
