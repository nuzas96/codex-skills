# Hard CTF writeup-repository mining lessons

Use this reference when mining a public CTF writeup/source repository to upgrade the skill library, especially for hard/zero/near-zero-solve challenges.

## Workflow that worked

1. Start from the repository README/score table to identify hard, zero-solve, near-zero, and unusually long time-to-blood targets.
2. Inspect challenge source plus author solution artifacts before writing skills. Do not infer a technique from a README alone.
3. Distill reusable class-level patterns, not challenge-by-challenge narrative. Good outputs are:
   - recognition checklists,
   - practical workflow steps,
   - pitfalls/failure modes,
   - templates/scripts only when they can be reused.
4. If a target was already captured by an existing umbrella reference, do not duplicate it; update only if the remaining pass adds a novel primitive.
5. Explicitly mark artifact limitations. If a challenge only has external VM metadata or missing dist/source, say that and avoid inventing a solve pattern.
6. Patch the relevant category SKILL.md so future agents can discover the new reference; then run the skill repo's discoverability/cross-reference tests.
7. If an Obsidian checkpoint is explicitly requested/active, update it with a concise delta and high-value tells.

## High-value patterns from the SekaiCTF 2025 remaining pass

- Admin-bot browser oracles: when secret state affects search results, frame origins, subdomains, cache/process state, or browser crash/timing behavior, build a boolean side-channel instead of forcing direct XSS or cookie theft.
- Browser-version-specific CSS/rendering crashes can be legitimate CTF oracles when sanitizer allows CSS but blocks script; reproduce exact bot version and navigation choreography.
- Multi-origin iframe leaks: if secret characters are encoded into wildcard subdomains/origins and the admin keeps the secret page open, candidate origins can leak via heap size, cache warmth, timing, or resource/process state.
- Windows custom packers: writable per-page decryption metadata beside an input buffer can be an exploitation primitive. Overflowing XOR keys/status can make the next VEH/lazy-decrypt fault patch code into chosen stubs.

## User-specific preference observed

For this class of task, the user prefers a lean high-signal pass: hard/zero/near-zero first, reusable playbooks/patterns over raw dumps, honest scope notes for missing artifacts, and fresh pytest verification after skill edits.
