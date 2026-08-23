# Windows Artifact Forensics

Use when a CTF provides a Windows disk/triage collection, NTFS metadata, registry hives, Prefetch, Event Logs, LNK/Jump Lists, Shellbags, or KAPE/Eric Zimmerman-style outputs.

## Artifact Router

| Evidence | High-value parser / purpose |
|---|---|
| `$MFT`, `$J`, `$Boot`, `$LogFile` | MFTECmd / NTFS timeline and deleted/path metadata |
| Prefetch `.pf` | PECmd / execution evidence, run count, timestamps, referenced files |
| Registry hives | RECmd / user/system configuration and activity |
| `.evtx` | EvtxECmd / event timeline |
| `.lnk` | LECmd / opened target/path/volume metadata |
| Jump Lists | JLECmd / recent files/application destinations |
| Shellbags | SBECmd / folder navigation evidence |
| broad triage set | KAPE / collect+process targeted artifacts |

Do not run the entire suite if one artifact directly answers the challenge.

## NTFS Timeline

For `$MFT`, compare `$STANDARD_INFORMATION` and `$FILE_NAME` timestamps, parent relationships, in-use/deleted state and file size/path. Combine with USN Journal when present to understand rename/create/delete sequences.

Timestamp differences can indicate manipulation, but do not label every mismatch as timestomping; normal file operations can update the two attribute sets differently.

## Prefetch

Prefetch can prove program execution and expose referenced paths/files. Check executable name/hash, last-run timestamps, run count and referenced volume/files. Absence of Prefetch is not proof of non-execution because OS configuration/version may disable or prune it.

## Registry

Choose hives based on the question:

- SYSTEM — services, device/USB and system configuration;
- SOFTWARE — installed software/system configuration;
- SAM/SECURITY — account/security material;
- NTUSER.DAT / UsrClass.dat — per-user MRUs, Shellbags and application state.

Use focused RECmd batches or direct registry parsing; broad export is useful only when the question is open-ended.

## Event Logs

Start from challenge-relevant channels/event IDs/time window. Correlate Security/System/PowerShell/Sysmon/etc. rather than treating one log as complete. Preserve original timestamps/time zone context.

## LNK / Jump Lists / Shellbags

These can recover paths to removable drives, deleted files, network shares and folders no longer present. Correlate volume serials/drive letters and timestamps with MFT/registry evidence.

## KAPE

KAPE is an orchestration layer. In a CTF, use it to collect/process a targeted artifact set, not as a substitute for understanding what each parser output means.

## Timeline Strategy

Normalize outputs to CSV/structured form and correlate around the smallest suspicious time window. Useful keys include path, executable, user, volume, process, event record ID and timestamp.

## Common Failure Modes

- Running `!EZParser` on everything before defining the question.
- Treating parser CSV as ground truth without retaining original artifact.
- Assuming `$SI` vs `$FN` timestamp mismatch always means timestomping.
- Ignoring LNK/Jump List/Shellbag evidence after a file is deleted.
- Missing user-specific hives because only SYSTEM/SOFTWARE were collected.
- Mixing local/UTC timestamps without normalization.

## Provenance

Consolidated from the original `performing-windows-artifact-analysis-with-eric-zimmerman-tools` Apache-2.0 skill and existing `ctf-forensics/windows.md` material. Original source remains frozen on `archive/pre-restructure-20260823`.
