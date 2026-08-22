---
name: ctf-crypto
description: Solve CTF cryptography challenges where the main blocker is a cryptographic or mathematical weakness: classical ciphers, RSA, ECC, AES/block modes, stream ciphers, hashes/MACs/signatures, PRNGs, ZKP/protocols, lattices/LWE/CVP, Coppersmith/LLL, number theory, algebraic constructions and custom crypto. Use when breaking the construction or recovering secret mathematical state is the primary path to the flag; use ctf-reverse instead when understanding the implementation is still the main blocker.
license: MIT
compatibility: Requires Python 3 and target-specific math/crypto tooling such as SageMath, SymPy or solver libraries only when the selected technique needs them.
metadata:
  user-invocable: "false"
---

# CTF Crypto — V2 Router

Use `ctf-solve` for workspace/progress/stuck-recovery. This skill selects the smallest cryptographic reference needed for the current construction.

## First pass

1. Write the construction exactly from source/output: equations, modulus/order, mode, nonce/IV, oracle, signature relation, PRNG recurrence.
2. Separate representation bugs from mathematical weaknesses.
3. Count what is known, unknown and attacker-controlled.
4. Estimate parameter sizes before choosing an attack.
5. Build the smallest local verifier for candidate secrets/plaintexts.
6. Load one technique family below; do not read the whole crypto library.
7. Use known flag format only as a validation/scoring constraint, never as replacement plaintext.

## Technique router

| Construction / signal | Load first | Add only if needed |
|---|---|---|
| Caesar/Vigenere/substitution/transposition/classical | `classic-ciphers.md` | `historical.md` |
| AES/ECB/CBC/CFB/GCM, padding/MAC/oracle | `modern-ciphers.md` | `modern-ciphers-2.md`, `modern-ciphers-3.md` |
| XOR/RC4/LFSR/stream reuse | `stream-ciphers.md` | `prng.md` |
| RSA textbook/weak parameters/common attacks | `rsa-attacks.md` | `rsa-attacks-2.md` |
| RSA partial-key/small-root/LLL/Boneh-Durfee | `references/rsa-lll-patterns.md` | `lattice-and-lwe.md` |
| ECC/DLP/singular/small subgroup | `ecc-attacks.md` | `advanced-math.md` |
| MT/LCG/xorshift/seed/state recovery | `prng.md` | `prng-attacks.md` |
| lattice, HNP, LWE, CVP/SVP | `lattice-and-lwe.md` | `advanced-math.md` |
| ZKP/signature/protocol/solver-heavy | `zkp-and-advanced.md` | matching math/cipher reference |
| isogeny/finite-field/polynomial/number-theory hard math | `advanced-math.md` | `references/crypto-hard-pattern-playbook.md` |
| exotic algebra/protocol/rare construction | `exotic-crypto.md` | `exotic-crypto-2.md` |
| unusual hard/near-zero-solve pattern | `references/crypto-hard-pattern-playbook.md` | `references/sekaictf2025-hard-crypto-patterns.md` |

Choose by the actual mathematical structure, not by challenge title.

## Core classification questions

Before coding, answer:

- What exact value must be recovered or forged?
- Is the secret reused across samples?
- Is there an oracle? What bit/value does it reveal?
- Are nonce/IV/random values repeated, biased, truncated or attacker-controlled?
- Is arithmetic modulo a prime, composite, power, curve order, polynomial ring or finite field?
- Are there more equations than unknowns, or many more unknowns than equations?
- Is the weakness cryptographic, implementation-level, or representation-level?

These answers usually determine the reference faster than trying tools.

## RSA decision tree

Record `n`, `e`, ciphertext/signature samples and any leaked information.

Check cheap conditions before lattices:

```text
small e / no padding
shared modulus
common factors / batch gcd
close primes / Fermat
small d / Wiener
known phi-related value
CRT fault
multiplicative/textbook signature
partial p/q/message bits
```

Only move to Coppersmith/LLL/Boneh-Durfee when parameter bounds support it. Derive polynomial, root bound and modulus relation explicitly before tuning lattice parameters.

## Block cipher / MAC discipline

For AES/modes, determine:

- exact mode;
- block size;
- IV/nonce source and reuse;
- padding;
- authentication order;
- whether ciphertext/header/length fields are authenticated;
- whether attacker gets encrypt/decrypt/validation oracle.

A bit flip, padding oracle, nonce reuse or MAC confusion only works when the surrounding parsing/authentication relation permits it. Reproduce the entire parser state locally when source is available.

## PRNG discipline

Mirror implementation semantics exactly:

- integer width and masking;
- signed/unsigned shifts;
- output truncation;
- number of draws between observations;
- seed derivation/time source;
- state transition order.

Validate predicted outputs before using recovered state for the flag stage.

## Lattice discipline

Before running LLL/BKZ:

1. identify the hidden-number/small-root/CVP relation;
2. normalize equations and scales;
3. write expected secret bounds;
4. construct the basis intentionally;
5. estimate determinant/dimension where useful;
6. verify recovered vector algebraically.

Do not treat LLL as a blind solver. Poor scaling/bounds can make a valid attack look impossible.

## ECC / finite-field discipline

Determine:

- curve equation and field;
- group/order and factorization;
- point validation behavior;
- singular/anomalous/small-subgroup conditions;
- scalar/nonce reuse;
- exceptional formulas or attacker-supplied points.

Verify every recovered scalar/point against the original public relation.

## Oracle discipline

For padding, parity, timing, signature or custom boolean oracles:

- define exactly what response state means `true`;
- establish noise/retry behavior;
- use binary search/statistics when possible rather than linear scans;
- cache observations;
- keep request volume bounded and reproducible.

## Representation pitfalls

Many CTF crypto failures are not deep cryptanalysis. Check:

- endian conversion;
- integer-vs-bytes encoding;
- signedness;
- leading zeros;
- UTF-8/Unicode transforms;
- base64/hex layers;
- float/raw-bit reinterpretation;
- field polynomial/basis choices.

## Cross-category pivots

- custom binary must be understood before equations are known -> `ctf-reverse`;
- token/application authorization is the real weakness -> `ctf-web`;
- ciphertext/key material must first be recovered from PCAP/disk/memory -> `ctf-forensics`;
- crypto is embedded in malware/config recovery and behavior is primary -> `ctf-malware`;
- constrained interactive jail/game is the main challenge -> `ctf-misc`.

## Completion criteria

- construction and weakness are stated mathematically;
- attack parameters/bounds come from the target;
- recovered key/plaintext/signature validates against the original construction;
- solver is reproducible when practical;
- `PROGRESS.md` contains equations, parameters, oracle behavior and decisive result.

## V1 migration rule

Crypto techniques remain internal category references. New writeups should update the canonical family file or hard-pattern reference instead of creating another top-level skill.