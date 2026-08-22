# Codex Skills V2 Migration Plan

> Status: restructuring work-in-progress. Do not merge to `main` until validation passes.

## Safety snapshot

- Original branch: `main`
- Frozen archive branch: `archive/pre-restructure-20260823`
- Working branch: `restructure/v2-category-first`
- Original snapshot commit: `cfc30195cfed1982b28dd24b39647a2c85c8f056`
- `main` and the archive branch were verified identical before migration began.

The archive branch is the canonical rollback point. Never rewrite or force-push it during V2 migration.

## V2 design goals

1. Reduce top-level skill activation noise.
2. Make each top-level skill represent a task/domain, not one exploit primitive.
3. Use category `SKILL.md` files as small routers.
4. Put detailed techniques in `references/` and executable helpers in `scripts/`.
5. Give every technique exactly one canonical owner.
6. Preserve imported knowledge, scripts, licenses, and attribution before deduplication.
7. Make future upgrades deterministic: classify -> deduplicate -> update canonical reference -> validate.
8. Keep challenge solving evidence-first and preserve progress/stuck-recovery behavior.

## Target top-level skills

- `ctf-solve`
- `ctf-web`
- `ctf-pwn`
- `ctf-reverse`
- `ctf-crypto`
- `ctf-forensics`
- `ctf-osint`
- `ctf-malware`
- `ctf-misc`
- `ctf-ai-ml`
- `ctf-writeup`
- `ctf-skill-upgrade`
- `agent-maintenance`

## Structural rule

```text
<category>/
├── SKILL.md              # routing + workflow only
├── references/           # canonical technique knowledge
├── scripts/              # reusable automation
└── assets/               # templates/static resources only when needed
```

A technique must not become a new top-level skill merely because it is useful. Add it to the relevant category reference unless it is a genuinely separate task/domain.

## Current -> V2 mapping

| Current directory | V2 owner | Action |
|---|---|---|
| `solve-challenge` | `ctf-solve` | Merge into orchestrator |
| `ctf-desktop-workspace` | `ctf-solve/references/workspace.md` | Merge |
| `progress-discipline` | `ctf-solve/references/progress.md` | Merge |
| `ctf-stuck-recovery` | `ctf-solve/references/stuck-recovery.md` | Merge |
| `ctf-modern-chains` | `ctf-solve/references/modern-chains.md` | Merge |
| `ctf-web` | `ctf-web` | Keep name; slim `SKILL.md`; retain canonical references |
| `web-ctf` | `ctf-web` + `ctf-solve` | Deduplicate workflow/field notes |
| `exploiting-http-request-smuggling` | `ctf-web/references/request-smuggling.md` | Merge |
| `exploiting-insecure-deserialization` | `ctf-web/references/deserialization.md` | Merge |
| `exploiting-jwt-algorithm-confusion-attack` | `ctf-web/references/jwt.md` | Merge |
| `performing-jwt-none-algorithm-attack` | `ctf-web/references/jwt.md` | Merge |
| `exploiting-nosql-injection-vulnerabilities` | `ctf-web/references/nosql-injection.md` | Merge |
| `exploiting-oauth-misconfiguration` | `ctf-web/references/oauth-oidc.md` | Merge |
| `exploiting-prototype-pollution-in-javascript` | `ctf-web/references/prototype-pollution.md` | Merge |
| `exploiting-race-condition-vulnerabilities` | `ctf-web/references/race-conditions.md` | Merge |
| `exploiting-template-injection-vulnerabilities` | `ctf-web/references/ssti.md` | Merge |
| `exploiting-websocket-vulnerabilities` | `ctf-web/references/websockets.md` | Merge |
| `performing-content-security-policy-bypass` | `ctf-web/references/csp.md` | Merge |
| `performing-directory-traversal-testing` | `ctf-web/references/traversal-lfi.md` | Merge |
| `performing-graphql-introspection-attack` | `ctf-web/references/graphql.md` | Merge |
| `performing-web-application-firewall-bypass` | `ctf-web/references/waf-bypass.md` | Merge |
| `performing-web-cache-poisoning-attack` | `ctf-web/references/cache-poisoning.md` | Merge |
| `testing-for-business-logic-vulnerabilities` | `ctf-web/references/business-logic.md` | Merge |
| `testing-for-xxe-injection-vulnerabilities` | `ctf-web/references/xxe.md` | Merge |
| `ctf-pwn` | `ctf-pwn` | Keep; slim router and organize references |
| `ctf-reverse` | `ctf-reverse` | Keep; slim router and organize references |
| `reverse-engineering-android-malware-with-jadx` | `ctf-reverse` + `ctf-malware` | Canonical tooling in reverse; malware workflow links to it |
| `reverse-engineering-dotnet-malware-with-dnspy` | `ctf-reverse` + `ctf-malware` | Canonical tooling in reverse; malware workflow links to it |
| `reverse-engineering-ios-app-with-frida` | `ctf-reverse/references/mobile-ios-frida.md` | Merge |
| `reverse-engineering-malware-with-ghidra` | `ctf-reverse/references/ghidra.md` | Merge generic reversing; malware-specific notes retained in malware |
| `reverse-engineering-ransomware-encryption-routine` | `ctf-malware/references/ransomware-crypto.md` | Merge |
| `reverse-engineering-rust-malware` | `ctf-reverse/references/rust.md` + malware notes | Deduplicate |
| `ctf-crypto` | `ctf-crypto` | Keep; slim router and organize references |
| `ctf-forensics` | `ctf-forensics` | Keep; slim router and organize references |
| `analyzing-browser-forensics-with-hindsight` | `ctf-forensics/references/browser-artifacts.md` | Merge |
| `analyzing-docker-container-forensics` | `ctf-forensics/references/docker-containers.md` | Merge |
| `analyzing-malicious-pdf-with-peepdf` | `ctf-forensics/references/pdf.md` + malware handoff | Merge |
| `performing-file-carving-with-foremost` | `ctf-forensics/references/file-carving.md` | Merge |
| `performing-memory-forensics-with-volatility3` | `ctf-forensics/references/memory-volatility.md` | Merge |
| `performing-network-forensics-with-wireshark` | `ctf-forensics/references/network-pcap.md` | Merge |
| `performing-sqlite-database-forensics` | `ctf-forensics/references/sqlite.md` | Merge |
| `performing-steganography-detection` | `ctf-forensics/references/steganography.md` | Merge |
| `performing-windows-artifact-analysis-with-eric-zimmerman-tools` | `ctf-forensics/references/windows-artifacts.md` | Merge |
| `performing-firmware-extraction-with-binwalk` | `ctf-forensics/references/firmware-extraction.md` + reverse handoff | Merge |
| `ctf-osint` | `ctf-osint` | Keep; slim router and organize references |
| `ctf-malware` | `ctf-malware` | Keep; slim router and organize references |
| `deobfuscating-javascript-malware` | `ctf-malware/references/javascript-deobfuscation.md` | Merge |
| `deobfuscating-powershell-obfuscated-malware` | `ctf-malware/references/powershell-deobfuscation.md` | Merge |
| `ctf-misc` | `ctf-misc` | Keep; slim router and organize references |
| `ctf-ai-ml` | `ctf-ai-ml` | Keep; slim router and organize references |
| `exploiting-active-directory-certificate-services-esc1` | `ctf-misc/references/active-directory.md` | Merge under infrastructure/AD section |
| `exploiting-active-directory-with-bloodhound` | `ctf-misc/references/active-directory.md` | Merge |
| `performing-kerberoasting-attack` | `ctf-misc/references/active-directory.md` | Merge |
| `performing-mobile-app-certificate-pinning-bypass` | `ctf-reverse/references/mobile-dynamic-analysis.md` | Merge |
| `testing-android-intents-for-vulnerabilities` | `ctf-reverse/references/mobile-android.md` | Merge |
| `ctf-writeup` | `ctf-writeup` | Keep; simplify |
| `ctf-writeup-repository-study` | `ctf-skill-upgrade` | Merge as knowledge-ingestion workflow |
| `token-efficient-cli-workflows` | `agent-maintenance/references/token-efficiency.md` | Merge |
| `hermes-context-compression` | `agent-maintenance/references/context-compression.md` | Merge |

## Canonical ownership rules

### Web
Auth/JWT/OAuth, parser bugs, browser/client attacks, API protocols, caching/proxy behavior, business logic, request races, traversal/LFI, SSRF, XXE, SSTI, deserialization and WAF behavior belong to `ctf-web`.

### Pwn
Memory corruption, mitigations, ROP, heap, FSOP, seccomp, kernel exploitation and native binary exploitation primitives belong to `ctf-pwn`.

### Reverse
Static/dynamic program analysis, decompilers, symbolic execution, VM/bytecode analysis, APK/iOS native reversing, language-specific reversing and anti-analysis belong to `ctf-reverse`.

### Crypto
Cryptographic construction attacks, number theory, lattices, PRNGs, RSA/ECC/AES/signatures/oracles belong to `ctf-crypto`.

### Forensics
Evidence extraction/reconstruction from memory, disks, filesystems, browsers, PCAP, media, SQLite, containers and artifacts belongs to `ctf-forensics`.

### Malware
Malware triage, unpacking/deobfuscation, C2/config extraction, behavioral analysis and malware-specific workflows belong to `ctf-malware`. Generic reverse-engineering tooling stays canonical in `ctf-reverse` and is linked rather than duplicated.

### Misc
Jails, unusual protocols, infrastructure challenges, AD/Kerberos, esolangs, game/VM puzzles and challenges that do not fit a stronger category belong to `ctf-misc`.

## Migration sequence

1. Freeze archive branch. **DONE**
2. Create isolated restructuring branch. **DONE**
3. Add migration manifest. **DONE with this commit**
4. Build `ctf-solve` orchestrator.
5. Consolidate Web specialist skills into `ctf-web`.
6. Consolidate Forensics specialist skills.
7. Consolidate Reverse/Malware/Mobile specialist skills.
8. Consolidate AD/infrastructure into Misc.
9. Consolidate agent-maintenance skills.
10. Build `ctf-skill-upgrade`.
11. Slim all category `SKILL.md` files into routing documents.
12. Add root `README.md`, `CATALOG.md`, attribution index and validator.
13. Validate all paths, links, frontmatter, scripts, references and skill sizes.
14. Compare V2 against archive to ensure no source knowledge was accidentally lost.
15. Test representative challenge prompts for each category.
16. Only then open/merge a PR into `main`.

## Non-negotiable migration checks

Before deleting an old top-level skill directory:

- its `SKILL.md` knowledge has a canonical V2 destination;
- useful `references/` content has been preserved or deduplicated;
- reusable scripts have been moved and still have their dependencies documented;
- license/attribution requirements are retained;
- all incoming references to the old path are updated;
- no unique technique or field note is silently discarded.

## Rollback

If V2 fails, restore from `archive/pre-restructure-20260823` or reset to commit:

```text
cfc30195cfed1982b28dd24b39647a2c85c8f056
```

Do not delete the archive branch after V2 is merged. Keep it as the historical V1 baseline until V2 has been used successfully in real CTFs.