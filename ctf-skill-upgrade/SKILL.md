---
name: ctf-skill-upgrade
description: Maintain and improve this CTF skill library by studying public writeups/methodology repositories or newly solved challenges, extracting only novel reusable techniques, classifying each technique into its canonical ctf-* owner, deduplicating against existing references, preserving provenance, updating focused references/scripts, and validating the repository. Use when the user asks to learn from writeups, upgrade skills, add a newly discovered technique, study a CTF repository, or improve the library after a solve. Do not use it to solve the live challenge itself.
license: MIT
compatibility: Requires git, filesystem/search access, Python 3 and web/GitHub access when studying external public sources.
metadata:
  user-invocable: "true"
  argument-hint: "[writeup-repo-or-technique-source]"
---

# CTF Skill Upgrade

This skill exists so the V2 repository grows **vertically inside canonical categories**, not horizontally as dozens of new top-level skills.

Core invariant:

```text
new knowledge
  -> classify domain
  -> search existing canonical references
  -> extract only novel reusable pattern
  -> update one canonical owner
  -> preserve source/provenance
  -> validate
```

Do **not** create a new top-level skill just because a technique has a recognizable name.

## 1. Determine the task type

Use this skill for:

- "study this CTF/writeup repo";
- "upgrade my skills";
- "add this technique to my skill";
- harvesting lessons after a solved challenge;
- methodology/playbook repositories such as heap/kernel/XS-Leak/crypto references.

Do not use it for:

- actively solving a challenge -> `ctf-solve`;
- producing the final competition writeup -> `ctf-writeup`;
- installing an unrelated third-party skill collection wholesale.

## 2. Identify the canonical owner

| Technique family | Canonical owner |
|---|---|
| HTTP/API/browser/auth/proxy/web bugs | `ctf-web` |
| native memory corruption/kernel exploit | `ctf-pwn` |
| program semantics/reversing/platform tools | `ctf-reverse` |
| mathematical cryptanalysis | `ctf-crypto` |
| disk/memory/network/media/artifact recovery | `ctf-forensics` |
| public-source identity/geolocation | `ctf-osint` |
| malicious behavior/config/C2/deobfuscation workflow | `ctf-malware` |
| jails/games/AD/infra/edge cases | `ctf-misc` |
| adversarial/model/LLM challenges | `ctf-ai-ml` |
| solve lifecycle/workspace/progress/stuck logic | `ctf-solve` |
| final writeup format | `ctf-writeup` |
| agent/context/token maintenance | `agent-maintenance` |

When a technique touches two categories, assign the **primitive itself** to one canonical owner and add a cross-reference from the other category. Never maintain two copied versions.

## 3. Search before adding

Before writing anything, search the target category for distinctive terms:

```bash
rg -ni "technique|primitive|CVE-ID|library-name|challenge-name" ctf-*/
```

Classify the proposed addition:

- **duplicate** -> do not add; optionally improve wording/source metadata;
- **variation** -> append to the existing technique section;
- **novel pattern** -> add a focused section/reference;
- **reusable automation** -> add/update a script;
- **one-off challenge constant** -> do not add as permanent knowledge.

The novelty bar is not "new challenge name". It is "new reusable recognition/exploitation/analysis pattern".

## 4. Studying a public writeup/methodology repository

Prefer technique-dense sources over huge omnibus repositories.

### Repository triage

Before reading deeply:

```bash
du -sh /tmp/<repo>
find /tmp/<repo> -iname '*writeup*.md' | wc -l
find /tmp/<repo> -iname '*solve*.py' -o -iname '*exploit*.py' | wc -l
```

For writeup repositories, read writeups and small solver/exploit scripts first. Skip large challenge binaries/source trees unless the writeup omits a detail required to understand the reusable pattern.

For methodology repositories, read the focused docs/code that correspond to the known gap.

Clone external study material shallowly into `/tmp` unless another temporary location is explicitly supplied:

```bash
git clone --depth 1 <url> /tmp/<repo>
```

### Batch reading

Avoid one tool call per writeup. Group files by category and read compactly/batched. Extract:

- recognition signal / "tell";
- minimal primitive;
- solve/exploit sequence;
- target-version constraints;
- exact useful tooling/commands;
- pitfalls/dead ends;
- source/challenge attribution.

Do not copy flags, credentials or irrelevant story content into the skill library.

## 5. Reference design

Prefer updating an existing canonical family file. Create a new reference only when the topic is coherent enough to deserve focused progressive disclosure.

Good:

```text
ctf-web/references/jwt.md
ctf-forensics/references/memory-volatility.md
ctf-pwn/references/how2heap-patterns.md
```

Bad:

```text
jwt-new-trick-from-challenge-x/SKILL.md
heap-technique-foo/SKILL.md
```

A reference should contain reusable sections such as:

```markdown
## Technique name

### Recognize
What target evidence suggests this pattern.

### Primitive
What capability actually exists.

### Solve / exploit workflow
Target-derived steps, not copied constants.

### Version / environment constraints
Where the technique changes or dies.

### Pitfalls
Common false assumptions.

### Source
Writeup/repository/challenge reference.
```

## 6. Script design

Move repeated deterministic work into `scripts/` when it saves reasoning/tool tokens:

- token decoders/forgers;
- packet/artifact extraction;
- mathematical solvers/templates;
- format/VM parsers;
- payload builders;
- repository validation.

Scripts should:

- take parameters instead of challenge-specific constants;
- produce compact machine/human-readable output;
- fail loudly on invalid assumptions;
- avoid embedding real flags/secrets;
- document dependencies.

## 7. Do not inflate category SKILL.md

Category `SKILL.md` files are routers.

When adding knowledge:

- reference exists already -> update it, no SKILL change unless routing is missing;
- new coherent reference -> add **one short route entry** to category SKILL;
- helper script -> mention it only where it materially improves routing/workflow.

If a category SKILL begins turning into a textbook again, stop and move detail into references.

## 8. Provenance and attribution

For imported/adapted knowledge record at minimum:

- source repository/page;
- challenge/writeup name when relevant;
- retrieval/update date when freshness matters;
- original license/attribution obligations for copied/adapted code/text;
- exact source file/blob when migrating existing V1 content.

Do not silently strip third-party license notices from reusable scripts.

During V2 migration, the frozen branch `archive/pre-restructure-20260823` is the authoritative provenance source for old specialist packages.

## 9. Post-solve harvesting

After a hard challenge is solved, harvest only lessons that will help a future unrelated challenge.

Ask:

- What clue should make an agent recognize this technique next time?
- Which assumption caused wasted time?
- Was behavior version-specific?
- Is there a reusable script/parser?
- Does an existing reference already cover it?

A good upgrade is usually 5-30 high-signal lines, not a raw copy of `PROGRESS.md`.

## 10. Validation gate

Before considering an upgrade complete:

1. run repository validator;
2. check all new relative links;
3. check frontmatter/name for new top-level skill only if one was intentionally created;
4. check that category SKILL stays router-sized;
5. search for duplicate technique text/entrypoints;
6. verify scripts at least parse/help-run where practical;
7. update catalog/provenance when structure changed.

During V2 restructuring, do not merge into `main` until the migration validation plan passes.

## Upgrade completion report

Report concisely:

- sources studied;
- novel patterns added vs duplicates skipped;
- canonical category/files updated;
- scripts added/changed;
- validation result;
- any unresolved attribution/version questions.

## V1 provenance

This replaces and generalizes V1 `ctf-writeup-repository-study`. The V1 original remains frozen in `archive/pre-restructure-20260823`; the missing `external-skill-repo-curation` dependency is intentionally not carried forward into the core CTF upgrade path.