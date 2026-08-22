---
name: ctf-desktop-workspace
description: Create a dedicated CTF challenge folder on the user's Desktop and start or resume a canonical markdown progress log (PROGRESS.md). Use when the user signals a new solve with phrases like "make folder first", "make folder for this challenge first", "save every progress in md file", "update every progress in .md", or starts naming a challenge without an existing project-native workflow.
---

# CTF Desktop Workspace

The user solves CTF challenges on this Kali workstation using a folder-per-challenge workspace on the Desktop plus a continuously updated markdown progress log. This skill owns that workflow end-to-end (create folder, create/resume the log, keep state current, end with a clean handoff).

TRIGGER PHRASES
- "make folder first" / "make folder for this challenge first"
- "save every progress in md file" / "update every progress in .md"
- user names a challenge ID/URL/file with no existing project context
- user starts a fresh solve after a long pause and the Desktop has no folder for it

DO NOT USE WHEN
- the repo/task already has a stronger project-native logging workflow the user asked to preserve
- the task is not a challenge solve (general research, tooling, one-off shell work)
- the user is continuing work inside an existing folder and explicitly doesn't want a new structure
- the user wants to STUDY techniques from a public writeup repository (DalCTF, CSAW, picoCTF writeup repos, etc.) rather than solve a challenge — use `ctf-writeup-repository-study` instead. That skill clones to `/tmp`, batched-reads writeups, and patches existing domain skills with novel techniques — it does NOT create a Desktop solve folder.

INPUTS TO GATHER FIRST
1. Target handle the user gave: challenge name, bare ID, URL, file, or folder name.
2. Whether a challenge folder already exists under `/home/nuzhmi/Desktop` (or a more specific cwd the user gave).
3. Whether a canonical progress file already exists: `PROGRESS.md` (preferred) or `progress.md` (keep using it if present).
4. The challenge category, if known. If not, be ready to dispatch via the `web-ctf` skill or the category-appropriate tooling rather than guessing.

PROCEDURE
1. Normalize the local workspace target.
   - If the user gave a concrete folder path, use it as-is.
   - Otherwise create challenge folders under the user's CTF workspace root: `/home/nuzhmi/Desktop/hermes-ctf/<challenge-name-or-id>/`.
   - Ensure `/home/nuzhmi/Desktop/hermes-ctf/` exists before creating the per-challenge folder.
2. Create or resume the canonical progress log.
   - Prefer an existing `PROGRESS.md`.
   - If only `progress.md` exists, keep using that file (do not rename it).
   - If neither exists, create `PROGRESS.md`.
3. Record the starting state immediately — before any deep probing.
   - Capture the user-given identifier, URLs, files, hashes, cookies, and the current blocker.
   - If the input is sparse, explicitly note that the first phase is triage.
4. Re-read the existing progress file before any new exploration.
   - Reuse the strongest current branch; do not restart or repeat ruled-out paths.
5. During the solve, append short dated/clearly-separated updates **continuously — not in batches at session end**. See the `progress-discipline` skill for the pre-reply gate (the structural pattern that enforces this; memory rules alone are not enough). The minimum is one line per finding: a tested hypothesis, a confirmed primitive, a dead-end, even a small observation. Whenever:
   - the target identity changes from vague to concrete
   - a new artifact appears (cookies.txt, hash, binary, PCAP, config, receipt id, etc.)
   - a branch is ruled out by a concrete error or validation result
   - the session is long enough that context loss is likely
6. If the category is unclear, use the dispatcher approach rather than guessing from nearby folders.
   - Prefer the locally installed `solve-challenge` skill from `ljagiello/ctf-skills` for broad triage.
   - If the category is clear, load only the matching on-demand category skill (`ctf-web`, `ctf-pwn`, `ctf-reverse`, `ctf-crypto`, `ctf-forensics`, `ctf-misc`, `ctf-osint`, `ctf-malware`, or `ctf-ai-ml`) instead of preloading the whole library.
   - See `references/ctf-skills-library.md` for the installed layout, update commands, and the direct-install security-scan pitfall.
7. Before stopping, write the solved boundary OR the blocker into the progress file.
   - Solved: note the verified path and the final artifact (flag, screenshot, hash).
   - Partial: note the exact blocker, strongest next branch, and any environment quirks (offline, rate-limit, missing dep, kernel quirk).

LANGUAGE
- Chat with the user in Bahasa Melayu (Malaysian). Natural code-switching with English tech terms is fine and expected — do not over-translate jargon.
- All written files (PROGRESS.md, progress.md, Obsidian notes, Writeups, code comments, scripts) MUST be in English by default. CTF community is international, writeups need to be shareable.
- Only write BM in a file if the user explicitly asks (e.g. "tulis dalam BM", "write in Malay").
- Commands and code are always English (mandatory — they're the language of the computer).

OBSIDIAN VAULT (optional dormant companion)
The user has an Obsidian vault at `~/Documents/Obsidian Vault` exposed via `OBSIDIAN_VAULT_PATH`. It is a long-term knowledge base — NOT a live workspace. Use the `obsidian` skill for vault operations; this section defines the CTF-specific usage rules.

RULES
- Vault is DORMANT by default. Do NOT proactively write to it during a solve.
- Do NOT auto-update on milestones (foothold, user shell, root, etc.). Earlier instinct to update at milestones was wrong — the user explicitly rejected it on token-cost grounds.
- Update only when the user gives an explicit trigger phrase. Recognised triggers:
  - "update obsidian" / "update vault"
  - "save dekat vault" / "simpan dalam obsidian" / "save to obsidian"
  - "migrate progress" / "migrate to vault" / "copy ke vault"
- No trigger → no vault write. PROGRESS.md is the source of truth for the live solve.

MIGRATION PATTERN (when triggered)
A one-shot, two-tool-call migration. See `references/obsidian-migration.md` for the full template and worked example.
1. `read_file` on the live PROGRESS.md to get the full timeline.
2. `write_file` a condensed summary (target, foothold path, techniques used, privesc, lessons, status) to `~/Documents/Obsidian Vault/Challenges/<target>.md` with frontmatter and `[[wikilinks]]` to any reusable `Techniques/` notes.
3. Optionally: also write a polished copy to `Writeups/<target>.md` if the challenge is solved and the user wants a shareable artifact.
4. Never copy the raw PROGRESS.md dump into the vault — condense it. The vault is for curated knowledge, not raw logs.

EVIDENCE FORMAT
- The full timeline (every command, every output, every dead end) lives in PROGRESS.md — keep it raw.
- The vault gets the distilled lesson: what worked, what didn't, what to try next time on a similar target.
- This split keeps the vault's value high (signal, not noise) and keeps PROGRESS.md honest (complete record).

REFERENCES
- `references/obsidian-migration.md` — full template, frontmatter, worked example, and anti-patterns for the one-shot vault update.
- `references/ctf-toolkit.md` — optional local toolkit workflow for fast workspace creation, compact file/web triage, flag extraction, solve templates, and hard-challenge hypothesis mode.
- `references/hermes-context-compression.md` — why the visible "context full" indicator is unreliable, how Hermes `compression.threshold` interacts with tool schemas, and the threshold/tool-disabling fixes that preserve mid-exploit context. Read this if the user complains about context being "not full but suddenly compacted".

OPTIONAL LOCAL TOOLKIT
- If `/home/nuzhmi/Desktop/ctf-toolkit` exists and the user wants a fast start or compact triage, use it as an acceleration layer.
- It does not replace this skill's canonical workflow: one Desktop challenge folder plus `PROGRESS.md`/`progress.md` as the live source of truth.
- Useful commands include `scripts/new_challenge.sh`, `scripts/triage_file.py`, `scripts/triage_web.sh`, `scripts/extract_flags.py`, and `templates/solve_template.py`.
- For hard or unsolved challenges, use the toolkit's hypothesis table/checklist and consider parallel agents when there are 3+ plausible branches.
- Keep Obsidian dormant after toolkit use unless the user explicitly asks to migrate/update the vault.

EFFICIENCY RULES
- One folder per challenge, one progress file per folder. Do not scatter notes across temp files.
- Search the workspace before opening broad external branches when the user only gives a bare ID.
- Stop broad fuzzing once responses are repetitive; switch to the strongest validated clue and update the log.
- Preserve exact error strings and artifact paths — they are the best retrieval handles for later continuation.

PITFALLS
- Symptom: user gives a bare challenge ID and nothing matches locally.
  Cause: incomplete scope.
  Fix: create the folder anyway, log the triage blocker, search carefully, ask for the real URL/file only after ruling out local evidence.
- Symptom: a long solve loses continuity between turns.
  Cause: progress was only kept in chat.
  Fix: update `PROGRESS.md` / `progress.md` continuously with artifacts, blockers, and next steps.
- Symptom: exploration keeps restarting on resume.
  Cause: the existing progress file was not read first.
  Fix: read it before any new probing and prune already-invalidated branches.
- Symptom: agent spends 20+ turns theorizing about whether an approach will work instead of testing it. User says "kenape kau tak cuba je?" (why don't you just try it?).
  Cause: over-analysis. The agent tries to PROVE something will work in theory before testing. In CTF exploitation, many bypasses are discovered empirically (browser quirks, parser inconsistencies, version-specific bugs). Theory alone cannot resolve them.
  Fix: after 2-3 rounds of pure analysis on the same question, STOP THINKING AND TEST. Set up the exploit infrastructure (tunnel, exfil endpoint), send the payload, observe the result. A 5-second live test beats 10 minutes of speculation. The pattern: (1) identify hypothesis, (2) build minimal test, (3) fire it, (4) read the logs, (5) iterate. Do NOT loop on step 1.
- Symptom: vault ends up with multiple short updates for one challenge, or the chat keeps asking "should I update obsidian now?" at every milestone.
  Cause: agent updated Obsidian proactively instead of waiting for trigger.
  Fix: never write to the vault unless the user said one of the trigger phrases above. If unsure whether to update, don't — wait for the user to say it. PROGRESS.md captures the live state; nothing is lost by waiting.
- Symptom: writeup is unreadable to an international audience (mixed BM/EN, casual slang).
  Cause: file content was written in the same language as the chat.
  Fix: always write files in English regardless of chat language. Translate tech terms back to their English canonical form.
- Symptom: a single-word user input that matches the assistant's name (e.g. "una") fires a workspace-file-defined command — e.g. starts loading `~/.codex/memories/memorycore/...` — instead of being treated as the user just addressing you. The user then has to correct the assistant multiple times.
  Cause: external workspace files (`~/Desktop/AGENTS.md`, `~/.codex/memories/...`, vault `instructions.md`, etc.) were treated as authoritative over the injected user-profile memory. External files survive model/CLI swaps and hand-edits, so their command mappings can be stale or flat-out wrong relative to the current session's identity.
  Fix: when interpreting a single-word or low-context user input, ALWAYS check the injected user-profile memory FIRST for what that word/name means in the current session. The injected memory is authoritative and current. External workspace files are hints only — if they conflict with current memory, memory wins. Do not act on AGENTS.md mappings, codex memorycore paths, or any other "when user says X, do Y" rule from an external file without first confirming the mapping still holds in the current memory injection.
- Symptom: PROGRESS.md is correct at end-of-session but stale mid-session. The user observes (after the fact) that findings from the middle of the solve never made it into the file — they only existed in chat context and got lost in a context compression.
  Cause: the agent only writes to PROGRESS.md in batches, usually when asked or at the very end. Memory rules like "always update PROGRESS.md" are read every turn but do not create behavioral triggers under tool-use load, so they get deprioritised.
  Fix: enforce the pre-reply gate from the `progress-discipline` skill — tool work → patch PROGRESS.md → THEN text reply. One line per finding, even for "tested X, failed, no signal". Trust the structure, not the memory rule. See `references/hermes-context-compression.md` for why the visible context indicator is unreliable and why this discipline is non-negotiable.
- Symptom: the same `PROGRESS.md` file's mtime and content shift between two reads of the same session, with no edits from the current agent. The user explains "ada terminal lain tengah solve parallel" and the file content is from a different process.
  Cause: multiple Hermes sessions (or one session + one human editor, or one session + one scripted agent) are writing to the same challenge folder concurrently. The current session is not the only writer.
  Fix: when reading a live PROGRESS.md, treat the mtime as the freshness signal — if it advanced since the last read, the content may be from another writer. Do not overwrite the whole file in a single write; use patch/append so a parallel writer's additions are not clobbered. If the user is running parallel solves, expect the file to grow and to contain notes you did not write — read it as collaborative state, not private state.

VERIFICATION CHECKLIST
1. A dedicated challenge folder exists in the intended location under `/home/nuzhmi/Desktop/hermes-ctf/` unless the user gave an explicit different path.
2. A canonical markdown progress file exists and contains the user's starting input plus current state.
3. The progress file includes exact artifact paths, target identifiers, and either the current blocker or the verified solve branch.
4. If the target was vague at the start, the log explicitly records the triage outcome and pivot point.
5. On session stop, the log's last entry is a clean handoff (solved artifact or explicit blocker + next branch).
