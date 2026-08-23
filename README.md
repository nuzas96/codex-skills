# Codex CTF Skills

A progressive-disclosure CTF skill library designed for Codex/ChatGPT-style agents.

> **V2 consolidation is complete on `restructure/v2-category-first` and is undergoing final routing validation before merge.**  
> The untouched V1 snapshot is preserved at `archive/pre-restructure-20260823` from commit `cfc30195cfed1982b28dd24b39647a2c85c8f056`.

## Why V2 exists

V1 accumulated useful knowledge quickly, but many exploit/tool techniques became independent top-level skills. That made discovery noisy: a single Web challenge could match `ctf-web`, `web-ctf`, JWT, OAuth, SSTI, XXE, race, CSP, WAF and other skills simultaneously.

V2 uses a different rule:

> **Top-level skill = task/domain. Technique = reference. Automation = script.**

The result is fewer activation candidates, smaller entrypoints, easier maintenance and one canonical owner for reusable technique knowledge.

## Normal CTF activation

```text
ctf-solve
    +
one primary category skill
    +
one focused reference selected by evidence
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
| `ctf-boot2root` | complete scoped-machine lifecycle from discovery to root/system proof |
| `ctf-writeup` | final reproducible challenge writeup |
| `ctf-skill-upgrade` | learn from writeups/solves and update canonical knowledge |
| `agent-maintenance` | token-efficient CLI and agent/context configuration |

See [CATALOG.md](CATALOG.md) for technique routing.

## Repository shape

```text
codex-skills/
├── README.md
├── CATALOG.md
├── MIGRATION_PLAN_V2.md
├── scripts/
├── agent-maintenance/
├── ctf-solve/
├── ctf-web/
├── ctf-pwn/
├── ctf-reverse/
├── ctf-crypto/
├── ctf-forensics/
├── ctf-osint/
├── ctf-malware/
├── ctf-misc/
├── ctf-ai-ml/
├── ctf-boot2root/
├── ctf-writeup/
└── ctf-skill-upgrade/
```

Each skill may contain:

```text
<skill>/
├── SKILL.md       # compact router/workflow
├── references/    # canonical technique knowledge
├── scripts/       # reusable deterministic automation
└── assets/        # static resources/templates when needed
```

Not every skill needs every directory.

## `SKILL.md` rule

A top-level `SKILL.md` should answer:

- when this domain owns the task;
- what the cheapest first pass is;
- which evidence selects which focused reference;
- when to pivot to another category;
- what completion looks like.

It should not become an encyclopedia.

## Canonical ownership

Every technique has one canonical owner.

Examples:

- JWT/OAuth/SSTI/XXE/request smuggling -> `ctf-web`
- generic Ghidra/JADX/dnSpy/Frida/Rust workflow -> `ctf-reverse`
- malware config/C2/ransomware behavior -> `ctf-malware`
- Volatility/Hindsight/Wireshark/SQLite/Foremost -> `ctf-forensics`
- heap/FSOP/kernel exploitation -> `ctf-pwn`
- LLL/Coppersmith -> `ctf-crypto`
- AD CS/BloodHound/Kerberoasting CTF paths -> `ctf-misc`

If another category needs a technique, link to the owner instead of copying the tutorial.

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
- append meaningful findings before user-facing replies;
- exact-version empirical validation;
- a pre-defeat stuck-recovery gate before declaring defeat.

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

Normal development check:

```bash
python3 scripts/validate_skills.py
```

Final architecture gate:

```bash
python3 scripts/validate_skills.py --strict-migration
```

Strict mode fails on:

- missing canonical V2 skills;
- invalid top-level skill frontmatter/name mismatch;
- duplicate skill names;
- broken relative links from top-level routers;
- legacy V1 top-level entrypoints;
- **legacy V1 directory residue**;
- unclassified top-level skills/directories.

GitHub Actions runs strict migration validation on the V2 restructuring branch and pull requests.

## Migration safety

```text
main
  original V1 baseline until final merge

archive/pre-restructure-20260823
  frozen V1 rollback branch

checkpoint/v2-core-routers-20260823
  intermediate V2 recovery point

checkpoint/v2-strict-pass-20260823
  V2 state after strict structural validation

restructure/v2-category-first
  final V2 candidate branch
```

Original snapshot commit:

```text
cfc30195cfed1982b28dd24b39647a2c85c8f056
```

The archive is the historical source for complete original specialist packages and attribution history. Do not rewrite or delete it during V2 adoption.

Full migration mapping and rollback notes live in [MIGRATION_PLAN_V2.md](MIGRATION_PLAN_V2.md).

## Design principle

The library should make the next decision easier, not make the model read everything it knows.

A good V2 solve asks:

> **What evidence do I have, which domain owns it, and which one reference should I open next?**
