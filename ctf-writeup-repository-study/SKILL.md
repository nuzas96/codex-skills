---
name: ctf-writeup-repository-study
description: "Use when the user provides a public CTF-related repository URL (GitHub org repo, archived challenge archive, methodology playbook, or technique encyclopedia) and wants to extract/upgrade skills from it — typically triggered by phrases like 'ada writeup ctf', 'study this CTF repo', 'update skill dengan writeup ni', 'harini nak upgrade skills', 'cari skills berkaitan ctf ke', 'pergi github cari writeup', or a URL pointing to a known CTF repo. The repo can be — writeup-per-challenge (DalCTF, CSAW, HackTheBox writeups), methodology/playbook (kernelpwn, how2heap, xsleaks/wiki, RSA-and-LLL-attacks), or technique encyclopedia. Distinguishes this from solving a live CTF (use ctf-desktop-workspace for that) and from solving a single archived challenge (use solve-challenge from ljagiello/ctf-skills for that) — THIS skill is about EXTRACTING novel techniques from existing repos into the local skill library, not solving new challenges."
license: MIT
compatibility: Linux/macOS with git, python3, and basic Unix tools (curl, jq optional).
allowed-tools: Bash Read Write Edit Glob Grep WebFetch
metadata:
  user-invocable: "false"
---

# CTF Writeup Repository Study

When the user drops a public CTF writeup repo URL and asks you to "learn from it" / "extract techniques" / "update skills", this skill owns the workflow: clone, triage, batched-read, extract, patch existing skills.

The key invariant: do NOT solve the challenges in the repo. Do NOT read full source code or binaries. EXTRACT from the writeups — they contain the technique signal in a fraction of the bytes.

## When to Use vs Alternatives

| Trigger                                                        | Skill to use                       |
| -------------------------------------------------------------- | ---------------------------------- |
| "Solve this challenge" + URL to live CTF or single challenge   | `ctf-desktop-workspace`            |
| "Solve this challenge from a repo" + archive of one challenge  | `solve-challenge` (ljagiello/...)  |
| "Study this repo of writeups" / "update skills with these"     | **THIS skill**                     |
| "Find writeups for THIS challenge I'm solving"                 | web search + this skill's triage   |
| **"Install/curate skills from THIS skill repo"** (URL points to `SKILL.md` collection, not `writeup.md`) | **`external-skill-repo-curation`** — different deliverable, installs SKILL.md files instead of extracting technique patterns |
| Repo is a **methodology/playbook/encyclopedia**, not writeup-per-challenge (e.g., `kernelpwn`, `how2heap`, `xsleaks/wiki`, `RSA-and-LLL-attacks`) | **THIS skill** — extract technique patterns the same way; reference file format still applies |

## Workflow

### 1. Verify it's a writeup repo, not a challenge archive

Look for these structural tells (use one `ls`/GitHub API call):

- `writeup/` or `writeups/` directories inside challenge folders
- `writeup.md` / `WRITEUP.md` files
- `challenge.yml` / `challenge.yaml` (CTFd config) — `flags:` block with `content:` often present in solved repos
- `solve.py` / `exploit.py` / `payload.*` scripts alongside challenge source
- `README.md` with a challenge index table

If the repo only has source/binary files without writeups, ask the user — they may want a different approach (solve one to learn, or just take personal notes).

### 1.5. Pre-flight: identify the user's weak domains BEFORE choosing repos

Skip this step for "study THIS specific repo" tasks — the user already chose. Apply this step when the user says something broad like "upgrade everything", "go look at GitHub for writeups", "harini nak upgrade skills" — i.e., a class upgrade not a single-repo task.

```bash
# If a growth log exists, read it
cat ~/.hermes/skills/una-growth-log.md 2>/dev/null | grep -A2 "Current Tier"
# Or check existing ctf-skills umbrella for thin spots
for d in ~/.hermes/skills/ctf-skills/ctf-*; do
  echo "$(basename $d): $(ls $d/references/ 2>/dev/null | wc -l) references"
done
```

Pick 3-5 repos that DIRECTLY fill weak domains, not top-starred multi-domain writeup repos that overlap 50%+ with what the user already has. Worked example from a real session: user rated Pwn ⚔️ 2.5 and Crypto ⚔️ 2.5 — selected `smallkirby/kernelpwn` (kernel pwn), `shellphish/how2heap` (per-glibc heap), `mimoo/RSA-and-LLL-attacks` (lattice). Skipped `pwning/public-writeup` (PPP omnibus, 700+ writeups, 80%+ overlap), `Hackplayers/hackthebox-writeups` (1MB+ HTB noise). Final: 3 repos, 40MB, ~28KB references added.

Token math: 3 narrow targeted repos + 3 reference files (~28KB) >> 1 omnibus repo (700+ files, 80% redundant) for the user's actual gap.

### 1.6. Known-good canonical methodology repos (starter library when gap is unclear)

When Step 1.5 reveals a weak domain but you're not sure which repo to grab, start from this shortlist. Each is verified high-quality, well-maintained, and fills a specific gap that the existing `ctf-skills` umbrella does NOT cover:

| Domain gap | Repo | What it covers | Size | Why gap-fill |
|------------|------|----------------|------|--------------|
| 🌐 Web — XS-Leak / bot-XSS | [xsleaks/wiki](https://github.com/xsleaks/wiki) | Cross-site oracle taxonomy, primitive catalog, defense bypass map | ~7MB / 86 docs | THE canonical resource; existing `ctf-web` is server-side heavy |
| 🌐 Web — tiny XSS payloads | [terjanq/Tiny-XSS-Payloads](https://github.com/terjanq/Tiny-XSS-Payloads) | Payload catalog tagged by browser constraint (unsafe-inline, unsafe-eval, scripts, etc.) | ~550KB | Pick payload by CSP constraint instead of guessing |
| 🌐 Web — bug-bounty breadth | [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) | 754 enterprise + security skills, but CTF-relevant subset is ~5-10 (broken-link-hijacking, crypto audit, Go malware, heap spray) | 13MB | Wholesale install is too costly (14MB token cost); cherry-pick 3-5 only |
| 💥 Pwn — kernel exploitation | [smallkirby/kernelpwn](https://github.com/smallkirby/kernelpwn) | `modprobe_path` (AAW-only LPE), `tty_struct`, `userfaultfd` race, situation-based checklist | ~23MB | Existing `ctf-pwn` is userspace-heavy; no kernel playbook |
| 💥 Pwn — heap (per-glibc-version) | [shellphish/how2heap](https://github.com/shellphish/how2heap) | Working `.c` demos for each technique across glibc 2.23-2.43, with patch-tracking links | ~3MB | Heap primitives are glibc-version-specific; writeups go stale fast |
| 🔐 Crypto — lattice RSA | [mimoo/RSA-and-LLL-attacks](https://github.com/mimoo/RSA-and-LLL-attacks) | Production sage code: Coppersmith (stereotyped + high-bits-known) + Boneh-Durfee (d < N^0.292) | ~14MB | Existing `ctf-crypto` is theory-heavy; this is the practical implementation |
| 🔍 Rev — DalCTF2026 patterns | [DalCTF/DalCTF2026](https://github.com/DalCTF/DalCTF2026) | Already extracted — see `ctf-web/references/dalctf2026-patterns.md` etc. | — | Don't re-extract; already in `ctf-skills` references |
| 🛰️ OSINT, 🤖 AI/ML, 🎲 Misc | (no canonical repo identified yet) | — | — | Generic `ctf-osint` / `ctf-ai-ml` / `ctf-misc` are adequate for now; revisit if user reports gap |

Worked example: user said "harini nak upgrade skills" with no specific direction → read growth log (Pwn 2.5, Crypto 2.5, OSINT 2.0), pick `kernelpwn` + `how2heap` (Pwn gap) + `RSA-and-LLL-attacks` (Crypto gap). Skip the OSINT/AI/ML rows — those need active CTF exposure first, not more references.

### 2. Clone shallow to `/tmp`

```bash
cd /tmp && git clone --depth 1 <repo-url>
```

Why `/tmp`:
- `~/Desktop` is reserved for active solves (per `ctf-desktop-workspace`).
- `~/Documents/Obsidian Vault` is for curated knowledge — too curated for raw extraction.
- `/tmp` is fine because the remote is the source of truth.

Don't `git pull` later. If you need fresh data, re-clone.

### 3. Size the work before reading anything

```bash
du -sh /tmp/<repo>
find /tmp/<repo> -name "writeup.md" | wc -l
find /tmp/<repo> -name "writeup.md" -exec wc -l {} + | tail -1
```

This tells you:
- Total size (binaries inflate; consider whether to skim source/dist dirs at all).
- How many writeups exist (out of total challenges — most repos have ~50% coverage).
- Total writeup content size (token-cost signal).

Decision points:
- `<10` writeups with `<500` total lines: read all in one batched call.
- `10-30` writeups: read all, but skip writeups that look like 1-2 lines (often "view source" warmups).
- `50+` writeups: sample 1 per category first, then decide whether to read all.

### 4. Batched read with Python (not per-file `read_file`)

DO NOT call `read_file` once per writeup — that's 30 tool calls and bloats context.

Run the helper script (see `scripts/extract_writeups.py`) or inline:

```python
from pathlib import Path
from collections import defaultdict

repo = Path("/tmp/<repo>")
writeups = sorted(repo.rglob("writeup.md"))

by_cat = defaultdict(list)
for w in writeups:
    parts = w.relative_to(repo).parts
    cat = parts[0] if len(parts) > 1 else "?"
    by_cat[cat].append(w)

for cat in sorted(by_cat):
    print(f"\n{'='*60}\n=== {cat} ({len(by_cat[cat])} writeups) ===\n{'='*60}")
    for w in by_cat[cat]:
        rel = w.relative_to(repo)
        content = w.read_text()
        print(f"\n--- {rel} ({len(content)} chars) ---")
        print(content.strip())
        print("---END---")
```

This produces a structured view that fits in one tool output block — easier to triage than 30 separate reads.

Also collect any `solve.py` / `exploit.py` siblings — they often have the exact payload shape that's worth quoting.

### 5. Categorize techniques by existing skill domain

After reading, group each technique into one of:

| Domain                                       | Skill to patch             |
| -------------------------------------------- | -------------------------- |
| HTTP, templates, SQL, JWT, GraphQL, upload   | `ctf-web`                  |
| Memory corruption, format string, shellcode  | `ctf-pwn`                  |
| Reversing, patching, decompilation           | `ctf-reverse`              |
| Disk/memory/network forensics, USB, pcap     | `ctf-forensics`            |
| Encoding, containers, weird platforms        | `ctf-misc`                 |
| Public-source intelligence (geo, image, etc.)| `ctf-osint`                |
| Math, crypto primitives                      | `ctf-crypto`               |
| AI/ML adversarial                           | `ctf-ai-ml`                |
| Malware analysis                             | `ctf-malware`              |

Skip anything already covered well by existing skill references. The bar for adding a new technique:
- "I cannot find this exact pattern in any of the existing `references/*.md` files"
- OR it's a non-obvious twist on a known technique (e.g. `syscall@plt` instead of raw `syscall` for SROP)
- OR a specific tool chain that worked (compilation commands, library versions, exact payload shapes)

If unsure whether it's novel, grep existing references for a key term from the writeup first.

### 6. Patch per domain, not per technique

For each affected domain:
1. Create `~/.hermes/skills/ctf-skills/ctf-<domain>/references/<repo-slug>-patterns.md`
2. Add ONE line at the end of `ctf-<domain>/SKILL.md` linking to it (or a new `## <Repo> Patterns` section if the skill doesn't already end with one)
3. Don't restructure the existing SKILL.md — preserve its conventions

Reference file format that works well (from DalCTF2026 extraction):
```markdown
# <RepoSlug> — <Domain> Patterns

Source: <repo URL>. Notes below capture patterns that aren't already in the main
<reference-name> references — keep this file as a <RepoSlug>-flavored supplement, not a replacement.

---

## 1. <Technique Name> (<challenge-folder>)

**Pattern:** <one-line description of the bug class>

**Recon / Detect:** <how to recognize this bug class in a new challenge>

**Exploit / Solve:** <exploit steps, with commands>

**Tell:** <how to recognize the same bug in another challenge>
```

Per-technique sections within a single file work better than per-technique files — keeps related patterns together for cross-reference.

Don't put all domains in one file — references should be discoverable per skill (user opens `ctf-web/SKILL.md` and sees the dalctf2026-patterns.md link when working a web challenge, not buried in an omnibus).

### 7. Don't auto-commit third-party skill repos

The `ctf-skills/` repo at `~/.hermes/skills/ctf-skills/` is third-party (ljagiello/ctf-skills). Convention:
- Local modifications show as `M` (modified SKILL.md) and `??` (untracked `references/<file>.md`) in `git status`.
- DO NOT `git commit` — leave for the user to decide.
- If user wants to commit, point them at the exact `git add`/`git commit` commands.

This matches the existing convention (ctf-reverse already had untracked `references/unicorn-pe-emulation.md` from previous sessions).

### 8. Concise end-of-task report

End with a short Malay/English summary:
- Number of writeups read (out of total)
- Number of reference files created, total KB
- Which skills were patched (one-line each)
- Total line/token delta
- Whether to clean up `/tmp` clone

## Pitfalls

- **Reading source code or binaries:** huge and rarely contain technique signal beyond what the writeup already describes. Exception: small `solve.py` / `exploit.py` files have exact payloads, worth reading. Skip `dist/`, `src/`, image files, etc.
- **One mega-reference file across all domains:** the user reads the relevant domain's reference when working on a challenge, not a 500-line omnibus. Split per domain.
- **Duplicating existing techniques:** check `references/server-side*.md`, `references/heap*.md`, etc. before adding. The bar for new content is "not already covered".
- **Trying to solve the challenges in the repo:** that's `ctf-desktop-workspace` or `solve-challenge`. This skill is for studying, not solving.
- **Asking abstract clarification questions:** "What do you want me to extract?" with 5 category options is jargon-heavy. The user gave you a repo URL — they want extraction. Ask only if scope is genuinely ambiguous (e.g. "do you want me to solve one or just study?").
- **Re-explaining basic CTF concepts:** assume the user knows what ROT13, SQLi, format string, SROP, etc. are. Focus on what's specific to this CTF / this repo.
- **Committing to third-party skill repos:** don't. Local patches only.
- **Calling `read_file` per writeup:** use batched Python. 30 writeups = 1 tool call, not 30.
- **Cleaning up `/tmp` automatically:** `/tmp` gets cleared on reboot. Don't waste tool calls on `rm -rf`. Just mention the path in the report.
- **Don't preemptively clean `/tmp`.** User often asks follow-up questions about the same repo in the same session ("what about X from that repo?", "any more worth using?"). Keep the `/tmp` clone until the session ends, then clean. Mention path in final report.
- **Subagent fanout fragility for network-heavy recon.** `delegate_task` for parallel GitHub recon can fail unpredictably: API key errors (delegated model has no auth), timeouts on slow connections, or subagents that return useless one-line summaries. Have a documented fallback ready: switch to direct `curl` GitHub API calls + inline Python batched reads (which this skill already prescribes for writeups). Don't promise "I'll do this in parallel" via subagents unless you've verified the delegated model has the needed API credentials.
- **Top-starred ≠ best fit.** A repo with ⭐8000+ that covers 8 domains at surface level is usually worse than 3 narrow ⭐800-1000 repos each covering one domain deeply. Star count attracts writeups that look technique-rich but are mostly recycled CS-class material. Filter by what fills the user's SPECIFIC gap, not by popularity.
- **"Upgrade lagi" after a recent failure → FIRST check session_search for the failed challenge, then target.** When the user follows up "upgrade lagi" / "cari more writeup" right after failing a CTF challenge, do NOT just scrape more repos. Run `session_search(query="solve fail blocked <domain>", sort=newest)` and read the failed challenge's title and category. The right upgrade is the one that fills the SPECIFIC gap the failed challenge exposed — e.g., bot-XSS failure → grab `xsleaks/wiki` + `terjanq/Tiny-XSS-Payloads`, kernel-pwn failure → grab `kernelpwn`, lattice-crypto failure → grab `RSA-and-LLL-attacks`. Generic scraping burns tokens on repos that won't fix the actual gap. User has explicitly flagged this: "upgrade lagi sebab 2 chall kau tkleh solve.. so kau still tak bijak" — the upgrade must target the failure domain, not just add more volume.
- **More references ≠ smarter.** User has corrected this: adding references after a failed challenge did not improve subsequent solves. The bottleneck is the execution loop (empirical primitive verification, source-code-first analysis, decision-tree discipline), not the knowledge base. If the user reports repeated failure despite new references, do NOT do another general upgrade. Instead: (a) audit the recent PROGRESS.md to find the specific dead-end, (b) identify the missing primitive, (c) surgically add ONLY that primitive. Volume of references has diminishing returns past ~15KB per domain reference file.
- **Browser-version-specific primitives MUST note Chrome/Firefox/Safari version in the reference.** Modern web primitives (CRLF injection, mXSS via DOMPurify, SameSite behavior, PNA / Private Network Access, partitioned cache, SafeLinking XOR) change substantially across browser versions. Any reference that documents a "known-working" primitive must include: the browser version tested, the date verified, and an empirical reproduce recipe (set up logging server, trigger primitive, inspect raw bytes). Without this, the reference becomes stale within ~6 months and future agents will commit to a primitive that no longer works. Worked example: `ctf-web/references/modern-xs-leaks-patterns.md` has a Chrome 147/149 reality table listing which "well-known" primitives are now dead (CRLF blocked Chrome 88+, DOMPurify noscript-backtick mXSS patched, etc.).

## Verification Checklist

1. `/tmp` clone was created and successfully read.
2. All `writeup.md` files were batched into ONE output block for triage.
3. Each new technique was categorized into the correct domain before writing.
4. Each new reference file was added to the right skill's `references/` directory.
5. Each `SKILL.md` was patched with a single-line link (or short new section) to its new reference.
6. `git status` in `~/.hermes/skills/ctf-skills/` shows the new modifications (NOT auto-committed).
7. Concise summary reported to the user, including scope and token delta.

## Token-Cost Discipline

This skill is designed for token-conscious users. Per-step expectations:

| Step                      | Expected tool calls |
| ------------------------- | ------------------- |
| Repo URL → verify + clone | 1-2                 |
| Size the work             | 1 (batched shell)   |
| Read all writeups         | 1 (batched Python)  |
| Categorize + draft refs   | 1 per affected domain (write_file) |
| Patch each SKILL.md       | 1 per affected domain (patch) |
| Final summary             | 0 (text reply only) |

Total for a 50-challenge repo with 30 writeups touching 6 domains: ~15 tool calls.

If you find yourself doing more than this, you're either reading too much source code, duplicating existing content, or splitting files too granularly.

## References

- `scripts/extract_writeups.py` — re-runnable batched-read helper. Reads every `writeup.md` under a path, groups by top-level category, prints a structured dump suitable for triage in one tool output.
- `ctf-desktop-workspace` — for LIVE CTF solves (different class of work, but related — see "When to Use" table above).
- `solve-challenge` (from ljagiello/ctf-skills) — for solving a single archived challenge.
