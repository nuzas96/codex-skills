# V2 Skill Catalog

Use this catalog to locate the **canonical owner** before adding or searching for a technique.

## Solve lifecycle

| Need | Owner |
|---|---|
| workspace / resume / progress state | `ctf-solve` |
| challenge category triage | `ctf-solve/references/triage-routing.md` |
| pre-reply progress persistence | `ctf-solve/references/progress.md` |
| stuck / pre-defeat enumeration | `ctf-solve/references/stuck-recovery.md` |
| unusual multi-stage boundary mismatch | `ctf-solve/references/modern-chains.md` |
| final competition writeup | `ctf-writeup` |
| study writeups / upgrade this library | `ctf-skill-upgrade` |

## Web

Canonical owner: `ctf-web`

| Technique | Current canonical/reference route |
|---|---|
| SQL injection | `ctf-web/sql-injection.md` |
| NoSQL / Mongo oracle | `ctf-web/server-side-advanced-4.md` (to be normalized during migration) |
| JWT/JWE/JWK/JKU/KID | `ctf-web/references/jwt.md` |
| OAuth/OIDC/SAML/CORS | `ctf-web/auth-infra.md` |
| auth/authz/IDOR/session | `ctf-web/auth-and-access.md` |
| SSTI / template abuse | `ctf-web/server-side.md` |
| SSRF / internal fetch | `ctf-web/server-side.md`, selected advanced ref |
| XXE/XML | `ctf-web/server-side-2.md` |
| deserialization | `ctf-web/server-side-deser.md` |
| traversal/LFI/path parser | `ctf-web/server-side-advanced.md` |
| upload/RCE | `ctf-web/server-side-exec.md` |
| GraphQL | `ctf-web/server-side-2.md` |
| XSS/CSRF/admin bot | `ctf-web/client-side.md` |
| CSP/XSSI/CSS/postMessage | `ctf-web/client-side-advanced.md` |
| XS-Leaks / bot side channels | `ctf-web/references/modern-xs-leaks-patterns.md` |
| DOMPurify mXSS verification | `ctf-web/references/dompurify-3.3.1-mxss-verification.md` |
| prototype pollution / Node | `ctf-web/node-and-prototype.md` |
| request smuggling | Web + source/proxy model; specialist merge pending |
| cache poisoning | Web client/proxy reference; specialist merge pending |
| race / business logic | Web state-machine references; specialist merge pending |
| CVE/version-driven web | `ctf-web/cves.md` |
| Web3-integrated web | `ctf-web/web3.md` |

## Pwn

Canonical owner: `ctf-pwn`

| Technique | Route |
|---|---|
| stack/global overflow | `overflow-basics.md` |
| format string | `format-string.md` |
| ROP / ret2libc / shellcode | `rop-and-shellcode.md` |
| SROP / pivot / advanced ROP | `rop-advanced.md` |
| heap / tcache / UAF | `heap-techniques.md`, `heap-techniques-2.md` |
| how2heap patterns | `references/how2heap-patterns.md` |
| FSOP | `heap-fsop.md` |
| seccomp / sandbox | `sandbox-escape.md` |
| kernel | `kernel.md`, `kernel-techniques.md`, `kernel-bypass.md` |
| hard kernel patterns | `references/kernelpwn-patterns.md` |
| historical hard chains | select matching `advanced-exploits*.md` |

## Reverse

Canonical owner: `ctf-reverse`

| Technique | Route |
|---|---|
| static reversing | `tools.md` |
| debugger/dynamic | `tools-dynamic.md` |
| emulation | `tools-emulation.md` |
| Unicorn PE | `references/unicorn-pe-emulation.md` |
| symbolic/advanced tools | `tools-advanced.md`, `tools-advanced-2.md` |
| anti-debug/anti-analysis | `anti-analysis.md`, `anti-analysis-ctf.md` |
| common validator/CTF patterns | `patterns*.md` selected by need |
| runtime/self-modifying | `patterns-runtime.md` |
| languages/platforms | `languages*.md`, `platforms*.md` |
| firmware | `firmware-extraction.md` |
| Ghidra/JADX/dnSpy/Frida/Rust specialist content | migration into Reverse pending |

## Crypto

Canonical owner: `ctf-crypto`

| Technique | Route |
|---|---|
| classical ciphers | `classic-ciphers.md` |
| AES/block modes/MAC/padding oracle | `modern-ciphers.md`, `modern-ciphers-2/3.md` |
| stream/XOR/RC4/LFSR | `stream-ciphers.md` |
| RSA | `rsa-attacks.md`, `rsa-attacks-2.md` |
| Coppersmith / Boneh-Durfee / RSA LLL | `references/rsa-lll-patterns.md` |
| ECC | `ecc-attacks.md` |
| PRNG | `prng.md`, `prng-attacks.md` |
| lattice/LWE/CVP | `lattice-and-lwe.md` |
| ZKP/protocols | `zkp-and-advanced.md` |
| number theory / advanced algebra | `advanced-math.md` |
| exotic constructions | `exotic-crypto.md`, `exotic-crypto-2.md` |
| hard modern patterns | `references/crypto-hard-pattern-playbook.md` |

## Forensics

Canonical owner: `ctf-forensics`

| Technique | Current route |
|---|---|
| memory/Volatility | `disk-and-memory.md`; focused Volatility migration pending |
| disk/filesystem | `disk-and-memory.md` |
| deleted/corrupt/nested recovery | `disk-recovery.md`, `disk-advanced.md` |
| Linux/application artifacts | `linux-forensics.md` |
| Windows artifacts | `windows.md` |
| network/PCAP | `network.md`, `network-advanced.md` |
| USB/HID/Bluetooth | `peripheral-capture.md` |
| general/image stego | `steganography.md`, `stego-image.md` |
| audio/video/advanced stego | `stego-advanced.md`, `stego-advanced-2.md` |
| signals/hardware | `signals-and-hardware.md` |
| 3D/CAD/G-code | `3d-printing.md` |
| Hindsight browser forensics | focused migration pending |
| Docker forensics | focused migration pending |
| SQLite/WAL forensics | focused migration pending |
| Foremost carving | focused migration pending |
| Zimmerman/KAPE | focused migration pending |
| PDF/peepdf | focused migration pending |

## OSINT

Canonical owner: `ctf-osint`

| Technique | Route |
|---|---|
| geolocation / reverse-image / maps | `geolocation-and-media.md` |
| highway kilometer markers | `references/highway-km-marker-geolocation.md` |
| social media / usernames / IDs | `social-media.md` |
| web / DNS / archives / repositories | `web-and-dns.md` |

## Malware

Canonical owner: `ctf-malware`

| Technique | Route |
|---|---|
| script deobfuscation | `scripts-and-obfuscation.md` |
| PE/.NET malware workflow | `pe-and-dotnet.md` |
| C2/custom protocols | `c2-and-protocols.md` |
| JS/PowerShell specialist content | focused migration pending |
| ransomware/config behavior | Malware reference migration pending |
| generic Ghidra/JADX/dnSpy/Frida/Rust | owned by `ctf-reverse` |

## Misc / Infrastructure

Canonical owner: `ctf-misc`

| Technique | Route |
|---|---|
| Python jail | `pyjails.md` |
| Bash jail | `bashjails.md` |
| encodings | `encodings.md`, `encodings-advanced.md` |
| RF/SDR | `rf-sdr.md` |
| DNS puzzle | `dns.md` |
| games/VM/state puzzles | `games-and-vms*.md` selected by need |
| Linux privilege challenge | `linux-privesc.md` |
| CTFd navigation | `ctfd-navigation.md` |
| AD CS / BloodHound / Kerberoasting | `references/active-directory.md` migration pending |

## AI / ML

Canonical owner: `ctf-ai-ml`

| Technique | Route |
|---|---|
| adversarial examples / poisoning / backdoors | `adversarial-ml.md` |
| weights / LoRA / extraction / inversion / membership | `model-attacks.md` |
| prompt injection / jailbreak / LLM agents | `llm-attacks.md` |

## Agent maintenance

Canonical owner: `agent-maintenance`

| Need | Route |
|---|---|
| compact CLI / RTK / token savings | `references/token-efficiency.md` |
| Hermes context compression | `references/context-compression.md` |

## Adding a technique

Before creating anything:

```text
1. find canonical owner in this catalog
2. grep existing references
3. duplicate -> skip
4. variation -> improve existing section
5. new reusable pattern -> focused reference/section
6. reusable deterministic work -> script
7. update router/catalog only if discoverability requires it
8. run scripts/validate_skills.py
```

If you believe a technique needs a new top-level skill, first explain why it is a **new task/domain** rather than a technique inside an existing category.