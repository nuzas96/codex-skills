# V2 Skill Catalog

Use this catalog to locate the **canonical owner** before adding or searching for a technique.

## Activation model

Normal CTF solve:

```text
ctf-solve
  +
one primary category
  +
one focused reference selected by evidence
```

Add a second category only when the hard primitive genuinely crosses a domain boundary.

## Solve lifecycle

| Need | Canonical route |
|---|---|
| workspace / resume / progress state | `ctf-solve` |
| challenge category triage | `ctf-solve/references/triage-routing.md` |
| progress persistence | `ctf-solve/references/progress.md` |
| stuck / pre-defeat enumeration | `ctf-solve/references/stuck-recovery.md` |
| unusual multi-stage boundary mismatch | `ctf-solve/references/modern-chains.md` |
| final competition writeup | `ctf-writeup` |
| learn from writeups / upgrade library | `ctf-skill-upgrade` |

## Web

Canonical owner: `ctf-web`

| Technique | Route |
|---|---|
| SQL injection | `ctf-web/sql-injection.md` |
| NoSQL / Mongo oracle | `ctf-web/references/nosql-injection.md` |
| JWT/JWE/JWK/JKU/KID | `ctf-web/references/jwt.md` |
| OAuth/OIDC | `ctf-web/references/oauth-oidc.md` |
| auth/authz/IDOR/session | `ctf-web/auth-and-access.md` |
| SSTI / template abuse | `ctf-web/references/ssti.md` |
| SSRF / internal fetch | `ctf-web/server-side.md` + one matching advanced ref |
| XXE/XML | `ctf-web/references/xxe-xml.md` |
| deserialization | `ctf-web/references/deserialization.md` |
| traversal/LFI/path parser | `ctf-web/references/path-traversal-lfi.md` |
| upload/RCE | `ctf-web/server-side-exec.md` |
| GraphQL | `ctf-web/references/graphql.md` |
| WebSockets | `ctf-web/references/websockets.md` |
| XSS/CSRF/admin bot | `ctf-web/client-side.md` |
| CSP/XSSI/CSS/postMessage | `ctf-web/references/csp-browser.md` |
| XS-Leaks / bot side channels | `ctf-web/references/modern-xs-leaks-patterns.md` |
| DOMPurify mXSS verification | `ctf-web/references/dompurify-3.3.1-mxss-verification.md` |
| prototype pollution / Node | `ctf-web/references/prototype-pollution.md` |
| request smuggling / HTTP desync | `ctf-web/references/request-smuggling.md` |
| cache poisoning/deception | `ctf-web/references/cache-attacks.md` |
| race conditions | `ctf-web/references/race-conditions.md` |
| business logic/state machine | `ctf-web/references/business-logic.md` |
| WAF/parser differential | `ctf-web/references/waf-parser-differentials.md` |
| empirical blind/admin-bot workflow | `ctf-web/references/empirical-workflow.md` |
| CVE/version-driven web | `ctf-web/cves.md` |
| Web3-integrated web | `ctf-web/web3.md` |

## Pwn

Canonical owner: `ctf-pwn`

| Technique | Route |
|---|---|
| stack/global overflow | `ctf-pwn/overflow-basics.md` |
| format string | `ctf-pwn/format-string.md` |
| ROP / ret2libc / shellcode | `ctf-pwn/rop-and-shellcode.md` |
| SROP / pivot / advanced ROP | `ctf-pwn/rop-advanced.md` |
| heap / tcache / UAF | `ctf-pwn/heap-techniques.md`, `heap-techniques-2.md` |
| custom allocator integrity-tag/header-size forgery | `ctf-pwn/references/integrity-tagged-custom-allocator.md` |
| how2heap patterns | `ctf-pwn/references/how2heap-patterns.md` |
| FSOP | `ctf-pwn/heap-fsop.md` |
| seccomp / sandbox | `ctf-pwn/sandbox-escape.md` |
| kernel | `ctf-pwn/kernel.md`, `kernel-techniques.md`, `kernel-bypass.md` |
| hard kernel patterns | `ctf-pwn/references/kernelpwn-patterns.md` |

## Reverse

Canonical owner: `ctf-reverse`

| Technique | Route |
|---|---|
| ELF architecture / deterministic tool readiness | `ctf-reverse/references/tool-readiness.md` |
| generic native/Ghidra | `ctf-reverse/references/ghidra-native.md` |
| debugger/dynamic | `ctf-reverse/tools-dynamic.md` |
| emulation | `ctf-reverse/tools-emulation.md` |
| Unicorn PE | `ctf-reverse/references/unicorn-pe-emulation.md` |
| symbolic/advanced tools | `ctf-reverse/tools-advanced.md`, `tools-advanced-2.md` |
| anti-debug/anti-analysis | `ctf-reverse/anti-analysis.md`, `anti-analysis-ctf.md` |
| common validator/CTF patterns | selected `ctf-reverse/patterns*.md` |
| runtime/self-modifying | `ctf-reverse/patterns-runtime.md` |
| Android APK/JADX | `ctf-reverse/references/android-apk-jadx.md` |
| .NET/dnSpy | `ctf-reverse/references/dotnet-dnspy.md` |
| iOS/Frida runtime analysis | `ctf-reverse/references/ios-frida.md` |
| Rust binaries | `ctf-reverse/references/rust-binaries.md` |
| firmware/binwalk | `ctf-reverse/references/firmware-binwalk.md` |
| mobile IPC / TLS security | `ctf-reverse/references/mobile-app-security.md` |

## Crypto

Canonical owner: `ctf-crypto`

| Technique | Route |
|---|---|
| classical ciphers | `ctf-crypto/classic-ciphers.md` |
| AES/block modes/MAC/padding oracle | `ctf-crypto/modern-ciphers*.md` |
| AES-CTR nonce reuse / reused keystream / two-time pad | `ctf-crypto/references/keystream-reuse.md` |
| stream/XOR/RC4/LFSR constructions | `ctf-crypto/stream-ciphers.md` |
| RSA | `ctf-crypto/rsa-attacks.md`, `rsa-attacks-2.md` |
| Coppersmith / Boneh-Durfee / RSA LLL | `ctf-crypto/references/rsa-lll-patterns.md` |
| ECC | `ctf-crypto/ecc-attacks.md` |
| PRNG | `ctf-crypto/prng.md`, `prng-attacks.md` |
| lattice/LWE/CVP | `ctf-crypto/lattice-and-lwe.md` |
| ZKP/protocols | `ctf-crypto/zkp-and-advanced.md` |
| advanced algebra | `ctf-crypto/advanced-math.md` |
| exotic constructions | `ctf-crypto/exotic-crypto*.md` |
| hard modern patterns | `ctf-crypto/references/crypto-hard-pattern-playbook.md` |

## Forensics

Canonical owner: `ctf-forensics`

| Technique | Route |
|---|---|
| memory / Volatility 3 | `ctf-forensics/references/memory-volatility.md` |
| disk/filesystem | `ctf-forensics/disk-and-memory.md` |
| deleted/corrupt/nested recovery | `ctf-forensics/disk-recovery.md`, `disk-advanced.md` |
| browser/Hindsight artifacts | `ctf-forensics/references/browser-artifacts.md` |
| Docker/container artifacts | `ctf-forensics/references/docker-containers.md` |
| Office DOCX/DOCM/OOXML, encrypted Office, static VBA | `ctf-forensics/references/office-documents.md` |
| PDF/peepdf | `ctf-forensics/references/pdf-analysis.md` |
| file carving / Foremost | `ctf-forensics/references/file-carving.md` |
| network / Wireshark / tshark | `ctf-forensics/references/network-pcap.md` |
| SQLite/WAL/freelist | `ctf-forensics/references/sqlite-forensics.md` |
| stego detection | `ctf-forensics/references/stego-detection.md` |
| Windows/KAPE/Zimmerman | `ctf-forensics/references/windows-artifacts.md` |
| Linux/application artifacts | `ctf-forensics/linux-forensics.md` |
| USB/HID/Bluetooth | `ctf-forensics/peripheral-capture.md` |
| signals/hardware | `ctf-forensics/signals-and-hardware.md` |
| Rez `VECTOR:ICON` / Haiku `ncif` vector icon | `ctf-forensics/references/legacy-vector-icons.md` |
| ASCII-art / FIGlet-style text recovered from artifacts | `ctf-forensics/references/ascii-art-text-recovery.md` |
| 3D/CAD/G-code | `ctf-forensics/3d-printing.md` |

## OSINT

Canonical owner: `ctf-osint`

| Technique | Route |
|---|---|
| geolocation / reverse image / maps | `ctf-osint/geolocation-and-media.md` |
| highway kilometer markers | `ctf-osint/references/highway-km-marker-geolocation.md` |
| social media / usernames / IDs | `ctf-osint/social-media.md` |
| web / DNS / archives / repositories | `ctf-osint/web-and-dns.md` |

## Malware

Canonical owner: `ctf-malware`

| Technique | Route |
|---|---|
| JavaScript / PowerShell deobfuscation | `ctf-malware/references/script-deobfuscation.md` |
| PE/.NET malware behavior | `ctf-malware/pe-and-dotnet.md` |
| C2/custom protocols | `ctf-malware/c2-and-protocols.md` |
| ransomware encryption/config recovery | `ctf-malware/references/ransomware-crypto.md` |
| generic Ghidra/JADX/dnSpy/Frida/Rust | owned by `ctf-reverse` |

## Misc / Infrastructure

Canonical owner: `ctf-misc`

| Technique | Route |
|---|---|
| Python jail | `ctf-misc/pyjails.md` |
| Bash jail | `ctf-misc/bashjails.md` |
| encodings | `ctf-misc/encodings.md`, `encodings-advanced.md` |
| RF/SDR | `ctf-misc/rf-sdr.md` |
| DNS puzzle | `ctf-misc/dns.md` |
| games/VM/state puzzles | selected `ctf-misc/games-and-vms*.md` |
| Linux privilege challenge | `ctf-misc/linux-privesc.md` |
| CTFd navigation | `ctf-misc/ctfd-navigation.md` |
| AD CS / BloodHound / Kerberoasting | `ctf-misc/references/active-directory.md` |

## AI / ML

Canonical owner: `ctf-ai-ml`

| Technique | Route |
|---|---|
| adversarial examples / poisoning / backdoors | `ctf-ai-ml/adversarial-ml.md` |
| weights / LoRA / extraction / inversion / membership | `ctf-ai-ml/model-attacks.md` |
| prompt injection / jailbreak / LLM agents | `ctf-ai-ml/llm-attacks.md` |

## Boot2Root

Canonical owner: `ctf-boot2root`

| Technique | Route |
|---|---|
| full HTB/VulnHub/VM lifecycle | `ctf-boot2root/references/lifecycle.md` |
| isolated Linux privilege-escalation technique | `ctf-misc/linux-privesc.md` |
| AD relationship/Kerberos/AD CS branch | `ctf-misc/references/active-directory.md` |
| native/kernel exploit construction | `ctf-pwn` |

## Agent maintenance

Canonical owner: `agent-maintenance`

| Need | Route |
|---|---|
| compact CLI / RTK / token savings | `agent-maintenance/references/token-efficiency.md` |
| Hermes context compression | `agent-maintenance/references/context-compression.md` |

## Adding or upgrading a technique

```text
1. find canonical owner in this catalog
2. search existing references
3. duplicate -> skip
4. variation -> improve existing section
5. novel reusable pattern -> focused reference/section
6. reusable deterministic work -> script
7. preserve provenance
8. update router/catalog only if discoverability requires it
9. run strict validation
```

A new top-level skill requires a **new task/domain**, not merely a new exploit technique or tool.
