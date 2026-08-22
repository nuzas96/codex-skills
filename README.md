# Codex CTF Skills

A progressive-disclosure CTF skill library designed for Codex/ChatGPT-style agents.

> **V2 migration is currently developed on `restructure/v2-category-first`.**  
> The untouched V1 snapshot is preserved at `archive/pre-restructure-20260823` from commit `cfc30195cfed1982b28dd24b39647a2c85c8f056`.

## Why V2 exists

V1 accumulated useful knowledge quickly, but many exploit/tool techniques became independent top-level skills. That made discovery noisy: a single Web challenge could match `ctf-web`, `web-ctf`, JWT, OAuth, SSTI, XXE, race, CSP, WAF and other skills simultaneously.

V2 uses a different rule:

> **Top-level skill = task/domain. Technique = reference. Automation = script.**

The goal is fewer activation candidates, smaller entrypoints, easier maintenance and no duplicated canonical technique knowledge.

## Normal CTF activation

```text
ctf-solve
    +
one primary category skill
```

Example:

```text
JWT web challenge
  -> ctf-solve
  -> ctf-web
  -> ctf-web/references/jwt.md
```

A second category is added only when evidence proves the hard primitive crossed a domain boundary.

```text
Forensics extraction -> Crypto decryption
Reverse analysis -> Pwn exploitation
Web -> Reverse WASM logic
Malware -> Reverse native routine
```

## V2 top-level skills

| Skill | Responsibility |
|---|---|
| `ctf-solve` | lifecycle, workspace, progress, triage, pivots, stuck recovery |
| `ctf-web` | HTTP/API/browser/auth/proxy/server-side web trust boundaries |
| `ctf-pwn` | native memory corruption, ROP/heap/FSOP/kernel exploitation |
| `ctf-reverse` | program semantics, static/dynamic analysis, VM/platform reversing |
| `ctf-crypto` | mathematical cryptanalysis and crypto constructions |
| `ctf-forensics` | artifact extraction/reconstruction: disk, memory, PCAP, media, etc. |
| `ctf-osint` | public-source geolocation, identity, social/web/DNS research |
| `ctf-malware` | malicious behavior, deobfuscation workflow, config/C2 recovery |
| `ctf-misc` | deliberate fallback for jails, games, AD/infra and edge cases |
| `ctf-ai-ml` | adversarial ML, model attacks, LLM/agent challenges |
| `ctf-writeup` | final reproducible challenge writeup |
| `ctf-skill-upgrade` | learn from writeups/solves and update canonical knowledge |
| `agent-maintenance` | token-efficient CLI and agent/context configuration |

See [CATALOG.md](CATALOG.md) for technique routing.

## Skill layout

Target structure:

```text
<skill>/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

Not every skill needs every directory.

### `SKILL.md`

Small router/workflow only:

- when this domain owns the task;
- cheapest first pass;
- decision tree;
- links to focused references;
- cross-category handoff rules;
- completion criteria.

Do not turn it into an encyclopedia.

### `references/`

Canonical reusable technique knowledge:

```text
ctf-web/references/jwt.md
ctf-pwn/references/how2heap-patterns.md
ctf-forensics/references/memory-volatility.md
```

A reference should explain how to **recognize**, **verify**, and **apply** a technique, including important version/environment constraints.

### `scripts/`

Reusable deterministic automation:

- parsers;
- token/artifact analyzers;
- solver templates;
- extraction helpers;
- repository validation.

Scripts should accept target-derived parameters rather than hard-coded challenge constants.

## Canonical ownership

Every technique has one canonical owner.

Examples:

- JWT -> `ctf-web`
- generic Ghidra/JADX/dnSpy/Frida workflow -> `ctf-reverse`
- malware config/C2 interpretation -> `ctf-malware`
- Volatility/Hindsight/Wireshark/SQLite/Foremost -> `ctf-forensics`
- heap/FSOP -> `ctf-pwn`
- LLL/Coppersmith -> `ctf-crypto`

If another category needs the technique, link to the owner instead of copying the tutorial.

## Evidence-first solving

V2 preserves the core solving discipline:

```text
observable
 -> hypothesis
 -> smallest discriminating test
 -> evidence
 -> PROGRESS.md
 -> next ranked path
```

`ctf-solve` also preserves:

- read/resume progress before exploration;
- pre-flight search for prior version-specific findings;
- append findings before user-facing replies;
- exact-version empirical validation;
- a seven-point stuck-recovery gate before declaring defeat.

## Upgrading the library

Do not create `new-technique-name/SKILL.md` for every new trick.

Use `ctf-skill-upgrade`:

```text
source/writeup/solve
 -> classify canonical owner
 -> search existing references
 -> duplicate? skip
 -> variation? update existing section
 -> novel reusable pattern? add focused section/reference
 -> reusable code? add script
 -> preserve provenance
 -> validate
```

Challenge-specific flags, credentials and copied constants do not belong in permanent skill knowledge.

## Validation

Run:

```bash
python3 scripts/validate_skills.py
```

During migration, remaining V1 entrypoints are warnings:

```bash
python3 scripts/validate_skills.py --strict-migration
```

Strict mode will fail while legacy top-level `SKILL.md` files are still active.

The validator checks:

- top-level skill frontmatter/name consistency;
- duplicate names;
- missing core V2 entrypoints;
- relative links from top-level routers;
- oversized router warnings;
- remaining legacy V1 activation candidates.

## V2 migration safety

Never restructure directly on the frozen archive branch.

Current safety points:

```text
main                          original V1 baseline until final merge
archive/pre-restructure-20260823
                              frozen V1 rollback branch
restructure/v2-category-first
                              V2 working branch
```

Original snapshot commit:

```text
cfc30195cfed1982b28dd24b39647a2c85c8f056
```

Before deleting/deactivating a V1 top-level skill, verify:

1. unique `SKILL.md` knowledge has a canonical V2 destination;
2. useful references/scripts/assets are preserved or intentionally superseded;
3. license/attribution obligations are retained;
4. incoming links are updated;
5. no reusable technique is silently discarded.

Full migration mapping and rollback notes live in [MIGRATION_PLAN_V2.md](MIGRATION_PLAN_V2.md).

## Design principle

The library should make the next decision easier, not make the model read everything it knows.

A good V2 skill answers:

> "What evidence do I have, what family owns it, and which one reference should I open next?"
