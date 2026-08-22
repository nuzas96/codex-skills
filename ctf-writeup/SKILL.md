---
name: ctf-writeup
description: Produce a concise, reproducible CTF solution writeup after the final flag/answer has been verified. Use for competition submission, teammate handoff or organizer review. Build the writeup from the solved challenge artifacts and PROGRESS.md, preserving the decisive reasoning and one complete solver/exploit path without dumping every dead end.
license: MIT
compatibility: Requires access to the solved challenge workspace and any final solver/exploit artifacts.
metadata:
  user-invocable: "true"
---

# CTF Writeup — V2

Use only after the challenge result is verified. Live investigation belongs to `ctf-solve` and `PROGRESS.md`.

## Source of truth

Prefer, in order:

1. final working solver/exploit/script;
2. exact artifact/request/command that produced the flag;
3. `PROGRESS.md` / `progress.md` for the reasoning trail;
4. supplied challenge source/binary/config for explanation.

Do not reconstruct a confident story from chat memory when the saved evidence disagrees.

## Default structure

```markdown
# <Challenge Name>

**Category:** <category>
**Flag:** `<verified flag>`

## Summary
<1 short paragraph: vulnerability/technique and decisive chain>

## Solution
1. <recognition / important evidence>
2. <primitive / exploit or recovery step>
3. <final flag path>

## Solver / Exploit
```<language>
<one complete reproducible script or minimal commands>
```

## Key Lesson
<reusable technique or pitfall, 1-3 bullets/short paragraph>
```

Adapt headings only when the competition requires another format.

## Content rules

- Keep the intended path clear enough for another player to reproduce.
- Include exact target-derived values only when they are required to reproduce the solve.
- Explain **why** the primitive works, not every failed payload variation.
- Remove irrelevant debug output, temporary credentials and accidental secrets.
- If a challenge requires several stages, preserve the dependency chain in order.
- If the final answer is OSINT rather than a flag, show the evidence chain and exact normalization.
- For forensics, include artifact/extraction path.
- For crypto, include equations/weakness and verifier.
- For pwn, include mitigations, leaks/bases/offset derivation and final chain.
- For web, include request/trust-boundary primitive and final authorization/data-access step.
- For reverse, include decisive functions/transformation and validation against the original binary.

## Solver rule

Prefer one final complete solver/exploit over many partial snippets. It should:

- accept obvious target parameters where practical;
- derive values instead of embedding unrelated historical constants;
- contain no real secrets unrelated to the CTF;
- end at the final flag/answer, not at an intermediate shell/primitive unless the competition stops there.

## Dead ends

Normally omit dead ends. Include one only when it teaches an important non-obvious constraint, such as an exact browser/libc version invalidating the expected technique.

## Accuracy gate

Before finalizing:

1. flag/answer matches the verified artifact/server result;
2. script/commands correspond to the final working path;
3. names/ports/offsets are not copied from an earlier failed attempt;
4. challenge-specific flag format is preserved exactly;
5. no unsupported claim is added merely to make the narrative cleaner.

## Library harvesting

A writeup and a skill reference serve different purposes. Do not automatically paste the full writeup into the skill library.

If the solve contains a genuinely reusable novel technique, use `ctf-skill-upgrade` separately to extract the compact reusable pattern into its canonical category.
