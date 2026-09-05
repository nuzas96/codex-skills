# Codex Skills V2 Migration Plan

> **Status: COMPLETED. V2 has been adopted as the canonical architecture on `main`. The migration branches/checkpoints below are retained only as historical recovery points. Ongoing upgrades use `ctf-skill-upgrade` and the existing V2 validation gates.**

## Safety points

- Canonical V2 branch: `main`
- Frozen V1 archive: `archive/pre-restructure-20260823`
- Historical core-router checkpoint: `checkpoint/v2-core-routers-20260823`
- Historical strict-pass checkpoint: `checkpoint/v2-strict-pass-20260823`
- Historical final migration candidate: `restructure/v2-category-first`
- Original V1 snapshot: `cfc30195cfed1982b28dd24b39647a2c85c8f056`

The archive is the canonical V1 rollback/history point. Do not rewrite or force-push it; normal development belongs on V2 `main`.

## V2 design goals

1. Reduce top-level activation noise.
2. Make each top-level skill represent a task/domain, not one exploit primitive.
3. Keep category `SKILL.md` files as compact routers.
4. Keep `SKILL.md` as the router; preserve broad mature category handbooks where useful, put focused/specialized techniques in `references/`, and deterministic helpers in `scripts/`.
5. Give every reusable technique exactly one canonical owner.
6. Preserve useful V1 knowledge and provenance before removing duplicate entrypoints.
7. Make future upgrades deterministic: classify -> deduplicate -> update canonical reference -> validate.
8. Preserve evidence-first solving, progress discipline and stuck recovery.

## Final top-level skills

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
- `ctf-boot2root`

No V1 specialist directory remains at the V2 root.

## Structural rule

```text
<category>/
├── SKILL.md              # routing + workflow only
├── *.md                  # optional broad/mature category handbooks
├── references/           # focused/specialized canonical technique knowledge
├── scripts/              # reusable automation
└── assets/               # optional templates/static resources
```

A technique does not become a new top-level skill merely because it is useful.

## Completed consolidation map

### Orchestration -> `ctf-solve`

- `solve-challenge`
- `ctf-desktop-workspace`
- `progress-discipline`
- `ctf-stuck-recovery`
- `ctf-modern-chains`

Canonical destinations include:

- `ctf-solve/references/workspace.md`
- `ctf-solve/references/progress.md`
- `ctf-solve/references/stuck-recovery.md`
- `ctf-solve/references/modern-chains.md`
- `ctf-solve/references/triage-routing.md`

### Web -> `ctf-web`

Merged specialist families include:

- HTTP request smuggling -> `references/request-smuggling.md`
- insecure deserialization -> `references/deserialization.md`
- JWT confusion / `alg:none` -> `references/jwt.md`
- NoSQL injection -> `references/nosql-injection.md`
- OAuth/OIDC -> `references/oauth-oidc.md`
- prototype pollution -> `references/prototype-pollution.md`
- race conditions -> `references/race-conditions.md`
- SSTI -> `references/ssti.md`
- WebSockets -> `references/websockets.md`
- CSP/browser behavior -> `references/csp-browser.md`
- traversal/LFI -> `references/path-traversal-lfi.md`
- GraphQL -> `references/graphql.md`
- WAF/parser differential -> `references/waf-parser-differentials.md`
- cache attacks -> `references/cache-attacks.md`
- business logic -> `references/business-logic.md`
- XXE/XML -> `references/xxe-xml.md`
- V1 `web-ctf` empirical workflow -> `references/empirical-workflow.md`

### Forensics -> `ctf-forensics`

- Hindsight/browser -> `references/browser-artifacts.md`
- Docker -> `references/docker-containers.md`
- malicious PDF/peepdf -> `references/pdf-analysis.md`
- Foremost -> `references/file-carving.md`
- Volatility 3 -> `references/memory-volatility.md`
- Wireshark/tshark -> `references/network-pcap.md`
- SQLite/WAL -> `references/sqlite-forensics.md`
- steganography detection -> `references/stego-detection.md`
- Zimmerman/KAPE -> `references/windows-artifacts.md`

### Reverse / mobile -> `ctf-reverse`

- Android/JADX -> `references/android-apk-jadx.md`
- .NET/dnSpy -> `references/dotnet-dnspy.md`
- iOS/Frida -> `references/ios-frida.md`
- generic Ghidra/native -> `references/ghidra-native.md`
- Rust binaries -> `references/rust-binaries.md`
- firmware/binwalk -> `references/firmware-binwalk.md`
- Android intents + mobile TLS/pinning concepts -> `references/mobile-app-security.md`

Generic platform/tool reversing is owned here. Malware links here instead of copying generic tutorials.

### Malware -> `ctf-malware`

- JavaScript + PowerShell deobfuscation -> `references/script-deobfuscation.md`
- ransomware encryption/config recovery -> `references/ransomware-crypto.md`
- C2/config/behavior remains owned by malware references and core files

### Infrastructure / AD -> `ctf-misc`

- BloodHound path analysis
- Kerberoasting
- AD CS ESC1

All are consolidated into `ctf-misc/references/active-directory.md` so enterprise CTF knowledge is a focused subfamily rather than three global activation candidates.

### Agent maintenance

- token-efficient CLI workflow -> `agent-maintenance/references/token-efficiency.md`
- Hermes context compression -> `agent-maintenance/references/context-compression.md`

### Knowledge ingestion

- `ctf-writeup-repository-study` -> `ctf-skill-upgrade`

New writeups should update canonical owners instead of spawning top-level technique skills.

### Installed legacy evidence skills

The installed `solve-ctf-evidence-first` and seven category solvers contributed distilled evidence, validation, mistake-bank, and personal field lessons to focused `legacy-evidence-lessons.md` references in their canonical V2 owners.

The installed `solve-boot2root-ctf` exposed a lifecycle gap not covered by isolated Linux privilege-escalation or AD references. Its discovery -> enumeration -> foothold -> movement -> privilege escalation -> user/root proof workflow is preserved as the dedicated `ctf-boot2root` domain.

## Canonical ownership boundaries

### Web
HTTP/application/API/browser/auth/proxy/cache/parser/business-logic trust boundaries.

### Pwn
Native memory corruption, mitigations, ROP, heap, FSOP, seccomp and kernel exploitation.

### Reverse
Program semantics, static/dynamic tooling, decompilers, symbolic execution, VM/bytecode, mobile/platform/language reversing.

### Crypto
Cryptographic construction attacks, number theory, lattices, PRNG, RSA/ECC/AES/signatures/oracles.

### Forensics
Evidence extraction and reconstruction from memory, disks, filesystems, browsers, PCAP, media, SQLite, containers and document artifacts.

### Malware
Malware behavior, deobfuscation workflow, unpacking, C2/config extraction and malware-specific crypto/framing.

### Misc
Jails, unusual protocols, games/state puzzles, AD/Kerberos/infrastructure and edge cases that do not fit a stronger domain.

## Migration sequence

1. Freeze archive branch. **DONE**
2. Create isolated restructuring branch. **DONE**
3. Add migration manifest. **DONE**
4. Build `ctf-solve` orchestrator. **DONE**
5. Consolidate Web specialists. **DONE**
6. Consolidate Forensics specialists. **DONE**
7. Consolidate Reverse/Malware/Mobile specialists. **DONE**
8. Consolidate AD/infrastructure. **DONE**
9. Consolidate agent-maintenance skills. **DONE**
10. Build `ctf-skill-upgrade`. **DONE**
11. Slim category `SKILL.md` files into routers. **DONE**
12. Add root README/catalog/validator. **DONE**
13. Deactivate V1 specialist entrypoints. **DONE**
14. Remove migrated V1 physical subtrees from V2 root. **DONE**
15. Enforce strict physical root cleanliness in CI. **DONE**
16. Run strict structural validation. **DONE**
17. Run representative routing-path checks. **DONE**
18. Review PR diff/status and only then merge to `main`. **DONE**

## Non-negotiable validation gates

These were the V2 adoption gates and remain the baseline validation contract for ongoing maintenance:

- exactly the 14 canonical top-level skills are present;
- no legacy V1 top-level directory remains;
- all skill frontmatter names match parent directories;
- all required canonical skills exist;
- local relative links across all Markdown documents resolve;
- no unclassified root directory exists;
- representative challenge routes resolve to existing canonical references;
- GitHub Actions strict validation succeeds.

Run locally:

```bash
python3 scripts/validate_skills.py --strict-migration
```

## Rollback / historical comparison

If a regression requires comparison with the pre-V2 system, restore or inspect from:

```text
archive/pre-restructure-20260823
```

or original commit:

```text
cfc30195cfed1982b28dd24b39647a2c85c8f056
```

Keep the archive as the historical V1 baseline and attribution source. It is no longer an active alternative architecture; V2 `main` is the canonical development line.
