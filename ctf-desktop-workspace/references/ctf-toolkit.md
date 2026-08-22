# Local CTF Toolkit

This workstation may have a lightweight helper toolkit at:

`/home/nuzhmi/Desktop/ctf-toolkit`

Use it as an optional acceleration layer for CTF solves. It does not replace the canonical challenge workspace rule: each challenge still gets its own Desktop folder and a continuously updated `PROGRESS.md`.

## When to Use

Use the toolkit when the user wants a fast start, says to use the toolkit, or a challenge needs compact triage before deeper category-specific work.

Good triggers:
- "make folder first using toolkit"
- "start challenge"
- "triage this file"
- "quick web recon"
- user provides a file/URL and wants a lean first pass

## Commands

Create a challenge workspace:

```bash
/home/nuzhmi/Desktop/ctf-toolkit/scripts/new_challenge.sh <challenge-name> [category] [target-or-url]
```

Compact file triage:

```bash
/home/nuzhmi/Desktop/ctf-toolkit/scripts/triage_file.py <file-or-dir> [more...]
```

Quick HTTP recon:

```bash
/home/nuzhmi/Desktop/ctf-toolkit/scripts/triage_web.sh <url>
```

Recursive flag/candidate search:

```bash
/home/nuzhmi/Desktop/ctf-toolkit/scripts/extract_flags.py <path> [optional-regex]
```

Generic socket/HTTP solve skeleton:

```bash
cp /home/nuzhmi/Desktop/ctf-toolkit/templates/solve_template.py ./solve.py
```

Hard challenge checklist:

```bash
/home/nuzhmi/Desktop/ctf-toolkit/checklists/hard-challenge-mode.md
/home/nuzhmi/Desktop/ctf-toolkit/checklists/hypothesis-table.md
```

## Workflow

1. If starting fresh, create/resume the challenge folder using the normal `ctf-desktop-workspace` rules.
2. If the toolkit exists and the task fits, use the relevant script for the first compact triage pass.
3. Append important results to `PROGRESS.md` rather than leaving them only in terminal output.
4. If the category becomes clear, load only the matching `ctf-*` skill.
5. For hard or unsolved challenges, copy the hypothesis table into `PROGRESS.md` and use parallel agents when there are 3+ plausible branches.

## Token/Speed Tradeoff

- Toolkit scripts are usually cheaper than broad manual terminal exploration because they produce compact summaries.
- Do not dump huge raw command output into chat if a toolkit script can summarize it.
- For very small tasks, direct commands may be cheaper than invoking multiple scripts.

## Pitfalls

- Do not treat the toolkit as the source of truth. `PROGRESS.md` is the live record.
- Do not auto-update Obsidian after toolkit runs; the vault remains dormant unless the user explicitly asks to migrate/update it.
- If a toolkit command fails due to missing dependencies or permissions, fall back to equivalent standard tools and record only the actionable blocker in `PROGRESS.md`.
