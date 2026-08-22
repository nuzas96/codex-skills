---
name: ctf-misc
description: Solve CTF challenges whose primary primitive does not fit Web, Pwn, Reverse, Crypto, Forensics, OSINT, Malware or AI/ML: Python/bash jails, encodings, RF/SDR, unusual DNS/protocol puzzles, esoteric languages, game/VM/state puzzles, infrastructure/AD/Kerberos challenges, constraint problems and hybrid edge cases. Use as a deliberate fallback after identifying the actual primitive, not as the default category.
license: MIT
compatibility: Requires only tooling selected by the specific edge-case challenge; do not preload broad toolsets.
metadata:
  user-invocable: "false"
---

# CTF Misc — V2 Router

Misc is a **controlled fallback**, not a dumping ground. Use `ctf-solve` for lifecycle/progress and move to a stronger category whenever the primitive becomes clear.

## First pass

1. Describe the challenge primitive in one sentence without relying on the category label.
2. Check whether another canonical category already owns it.
3. If not, select the narrowest reference below.
4. Build a small oracle/state model before brute force.
5. For hybrid challenges, keep Misc only while the main blocker is the unusual protocol/game/jail/infrastructure layer.

## Reference router

| Primitive | Load first | Add only if needed |
|---|---|---|
| Python eval/exec/restricted environment | `pyjails.md` | encoding ref if payload alphabet is constrained |
| Bash/shell restricted syntax | `bashjails.md` | `linux-privesc.md` only after actual shell/host pivot |
| Base-N/Unicode/custom encoding | `encodings.md` | `encodings-advanced.md` |
| RF/SDR/raw radio signal puzzle | `rf-sdr.md` | `ctf-forensics/signals-and-hardware.md` when decoding becomes forensic signal processing |
| DNS-specific oddity/puzzle | `dns.md` | `ctf-forensics/network*.md` for PCAP reconstruction |
| game/custom VM/state-machine puzzle | `games-and-vms.md` | select one of `games-and-vms-2/3/4.md` by TOC |
| Linux post-foothold challenge logic | `linux-privesc.md` | `ctf-pwn` if kernel/native exploitation becomes primary |
| CTFd platform navigation | `ctfd-navigation.md` | no exploit category unless challenge evidence requires it |
| recent unusual Misc pattern | `references/dalctf2026-patterns.md` | `references/sekaictf2025-misc-patterns.md` |
| AD/Kerberos/enterprise infra puzzle | canonical `references/active-directory.md` once migrated | relevant specialist source during migration |

Do not read all game/VM references together. Select by the actual mechanics.

## Jail decision tree

```text
restricted input/execution
  -> enumerate allowed syntax/builtins/environment
  -> identify target capability (read file, import, execute, escape)
  -> find one semantic gap
  -> minimize payload under constraints
```

For Python, distinguish:

- expression vs statement context;
- available globals/builtins;
- object graph access;
- blacklist vs allowlist;
- character/token filters;
- version-specific syntax.

For shell jails, inspect expansion/evaluation order, variables, globbing, redirection and available binaries. Do not spray payload lists before understanding the parser/filter.

## Encoding discipline

Before applying transforms repeatedly, identify evidence for each layer:

- alphabet and character distribution;
- length/multiples/padding;
- magic bytes after decode;
- reversible vs lossy transform;
- endian/bit ordering.

Record the decode chain explicitly. `base64 -> gzip -> xor -> ...` should be reproducible, not guessed manually.

## Game / VM discipline

Model state transitions before automation:

1. state variables;
2. legal actions;
3. win/loss/flag condition;
4. randomness and seed;
5. server/client disagreement;
6. race/check-commit boundaries;
7. invariant or solver formulation.

Use BFS/DP/Z3/game theory only after defining the state correctly.

## RF / SDR discipline

Determine signal representation first:

- sample rate;
- center frequency/channel;
- modulation;
- symbol/baud rate;
- framing/synchronization;
- error correction/encoding.

Plot spectrum/waterfall and inspect metadata before trying demodulators at random.

## Active Directory / Kerberos ownership

V2 consolidates specialist AD CS ESC1, BloodHound and Kerberoasting packages into one focused Misc infrastructure reference because they are not common enough to justify three global top-level activation candidates.

That reference should route internally by observed primitive:

```text
certificate template / AD CS -> ESC path
SPN/TGS material -> Kerberoasting
relationship/path graph -> BloodHound analysis
```

If the repository later grows enough enterprise CTF content to justify a standalone `ctf-active-directory` domain, promote it deliberately through an architecture change—not one technique at a time.

## Cross-category pivots

- native memory corruption -> `ctf-pwn`;
- VM/binary semantics -> `ctf-reverse`;
- cipher/math construction -> `ctf-crypto`;
- signal/packet artifact reconstruction -> `ctf-forensics`;
- HTTP/API trust boundary -> `ctf-web`;
- public-world research -> `ctf-osint`.

## Completion criteria

- unusual primitive/state machine is explicitly modeled;
- selected reference is justified;
- brute force/solver work is bounded by the model;
- final answer/flag validates against the challenge;
- `PROGRESS.md` records the transformation/state/constraint chain.

## V1 migration rule

Misc stays one deliberate fallback category. AD/Kerberos and other niche specialist skill directories are folded into focused internal references unless their body of knowledge later warrants a true domain-level skill.