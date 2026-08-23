---
name: ctf-misc
description: "Solve CTF challenges whose primary primitive does not fit Web, Pwn, Reverse, Crypto, Forensics, OSINT, Malware, AI/ML, or Boot2Root: Python/bash jails, encodings, RF/SDR, unusual DNS/protocol puzzles, esolangs, game/VM/state puzzles, Active Directory/Kerberos, constraints, and hybrid edge cases. Use as a deliberate fallback."
---

# CTF Misc — V2 Router

Misc is a controlled fallback. Use `ctf-solve` for lifecycle/progress and move to a stronger category whenever the hard primitive becomes clear.

## Reference router

| Primitive | Load first | Add only if needed |
|---|---|---|
| Python eval/exec/restricted environment | `pyjails.md` | encoding ref if alphabet constrained |
| Bash/shell restricted syntax | `bashjails.md` | `linux-privesc.md` after a real host pivot |
| Base-N/Unicode/custom encoding | `encodings.md` | `encodings-advanced.md` |
| RF/SDR/raw radio puzzle | `rf-sdr.md` | `ctf-forensics/signals-and-hardware.md` |
| DNS-specific puzzle | `dns.md` | `ctf-forensics` for PCAP reconstruction |
| game/custom VM/state puzzle | `games-and-vms.md` | select `games-and-vms-2/3/4.md` by TOC |
| Linux post-foothold challenge logic | `linux-privesc.md` | `ctf-pwn` if native/kernel exploit dominates |
| CTFd platform navigation | `ctfd-navigation.md` | category from challenge evidence |
| Active Directory / Kerberos / AD CS | `references/active-directory.md` | category-specific ref only if path changes |
| recent unusual Misc pattern | `references/dalctf2026-patterns.md` | `references/sekaictf2025-misc-patterns.md` |
| Discord/parser/loop/protocol evidence lessons | `references/legacy-evidence-lessons.md` | only when those patterns match |

## Misc discipline

1. Describe the primitive without relying on the category label.
2. Confirm another canonical category does not already own it.
3. Load the narrowest reference.
4. Model state/parser/constraint before brute force.
5. Pivot once the main blocker becomes web/native/crypto/forensics/etc.

## Active Directory

Use `references/active-directory.md` as a path-driven router:

```text
owned domain principal
 -> map relationships/objective
 -> BloodHound-style graph/path reasoning
     -> SPN service account branch -> Kerberoasting
     -> vulnerable AD CS template branch -> ESC1
     -> ACL/delegation/GPO edge -> validate that edge
 -> new principal/access
 -> recompute shortest path
```

Do not load BloodHound, Kerberoasting and AD CS as separate global skills.

## Jail / encoding / game rules

For jails, enumerate parser context, available objects/builtins/binaries and filter semantics before payload lists. For encodings, justify each transformation with alphabet/length/magic evidence. For games/VMs, define state variables/actions/win condition/randomness before BFS/DP/Z3 automation.

## Cross-category pivots

- native memory corruption -> `ctf-pwn`;
- binary/VM semantics -> `ctf-reverse`;
- cipher/math construction -> `ctf-crypto`;
- signal/packet artifact reconstruction -> `ctf-forensics`;
- HTTP/API trust boundary -> `ctf-web`;
- real-world research -> `ctf-osint`.

## V2 ownership rule

Niche infrastructure and unusual challenge families remain focused Misc references unless their knowledge volume becomes large enough to justify a deliberate architecture-level promotion. Never create one top-level skill per AD technique.

The complete V1 sources remain recoverable from `archive/pre-restructure-20260823`.
