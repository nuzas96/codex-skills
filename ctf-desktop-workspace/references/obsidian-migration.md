# Obsidian One-Shot Migration Pattern

When the user says one of the trigger phrases ("update obsidian", "save dekat vault", "migrate progress", "copy ke vault", "simpan dalam obsidian"), do a one-shot migration from the live `PROGRESS.md` into the Obsidian vault. The whole thing is two tool calls.

## Vault layout (already set up at `~/Documents/Obsidian Vault`)

```
Obsidian Vault/
├── INDEX.md              # auto-curated index, link here from new notes
├── Welcome.md            # onboarding note, leave alone
├── Challenges/           # per-target mirror notes (one file per challenge)
│   └── <target>.md
├── Techniques/           # reusable recon/exploit techniques, decoupled
│   └── <technique>.md
└── Writeups/             # polished, shareable final writeups
    └── <target>.md
```

Vault path is exposed via `OBSIDIAN_VAULT_PATH` env var. The `obsidian` skill reads it. Never pass `$OBSIDIAN_VAULT_PATH` literally to file tools — resolve the absolute path first.

## Migration procedure (two tool calls)

### Step 1 — read the live progress

```
read_file(path="/home/nuzhmi/Desktop/<target>/PROGRESS.md")
```

That gives the full timeline: every command, every output, every dead end.

### Step 2 — write a condensed summary to the vault

```
write_file(
  path="/home/nuzhmi/Documents/Obsidian Vault/Challenges/<target>.md",
  content=<frontmatter + condensed body, see template below>
)
```

Optionally also `write_file` a polished version to `Writeups/<target>.md` if the challenge is solved and the user wants a shareable artifact.

## Challenge note template

```markdown
---
type: challenge
target: <target-name-or-ip>
category: <web|pwn|rev|crypto|forensics|osint|cloud|ml>
difficulty: <easy|medium|hard|insane>
status: <solved|partial|unsolvable>
tags: [ctf, <category>, <platform>]
date: <YYYY-MM-DD>
---

# <target>

## Summary
- target: <IP / URL / file>
- foothold: <one-liner — e.g. "SQLi on /login (auth bypass)">
- privesc: <one-liner — e.g. "writable /etc/cron.d, dropped reverse shell">
- flag: <flag or "not captured">

## Recon
- <3-5 bullets of what recon revealed, only the meaningful hits>

## Exploitation
- <foothold path, condensed>
- <privesc path, condensed>

## Techniques used
- [[<technique-1>]] — short note on how it applied
- [[<technique-2>]] — short note

## Lessons
- <what to try next time on a similar target>
- <what dead ends to skip>

## Links
- [[INDEX]]
- [[Welcome]]
```

## Technique note template (only when something genuinely new emerged)

```markdown
---
type: technique
tags: [ctf, <category>, <phase:recon|foothold|privesc|post>]
---

# <Technique Name>

## When to use
- <signal that this technique applies>

## How
- <2-5 steps, commands included>

## Pitfalls
- <what to watch for>

## Examples
- [[<challenge-that-used-this>]]
```

## Worked example — minimal

User says: *"update obsidian"* after a solve.

1. `read_file` on `~/Desktop/htb-jerry/PROGRESS.md`
2. `write_file` to `~/Documents/Obsidian Vault/Challenges/htb-jerry.md`:

```markdown
---
type: challenge
target: htb-jerry
category: web
difficulty: easy
status: solved
tags: [ctf, web, htb]
date: 2026-06-18
---

# htb-jerry

## Summary
- target: 10.10.10.95
- foothold: default tomcat creds (tomcat:s3cret) on /manager
- privesc: nt authority\system via war deploy + reverse shell
- flag: <user.txt + root.txt captured>

## Recon
- nmap: 8080/tcp Apache Tomcat 7.0.88 open
- /manager/html reachable, default creds work

## Exploitation
- deployed shell.war via tomcat manager
- shell as nt authority\system (Tomcat runs as SYSTEM on Windows)

## Techniques used
- [[Tomcat-default-creds]] — always try tomcat:s3cret and admin:admin on /manager
- [[War-deploy-shell]] — quickest path from Tomcat creds to shell

## Lessons
- always try default Tomcat creds on :8080, it's the answer 30%+ of the time
- Windows Tomcat = SYSTEM by default, no real privesc needed
```

## Anti-patterns — what NOT to do

- **Do NOT** copy PROGRESS.md verbatim into the vault. The vault is curated signal, not raw log.
- **Do NOT** write to the vault without a trigger phrase. The default is dormant.
- **Do NOT** create a vault note for every tiny update. One note per challenge, one entry per technique.
- **Do NOT** put secrets (real passwords, API keys, personal info) in vault notes — Obsidian notes are not encrypted.
- **Do NOT** skip the frontmatter — it's what makes the vault searchable and the graph navigable.
- **Do NOT** use `$OBSIDIAN_VAULT_PATH` in file-tool paths. Resolve to the absolute path first.
