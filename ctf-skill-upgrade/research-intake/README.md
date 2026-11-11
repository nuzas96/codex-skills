# CTF Research Intake

Use this lightweight intake before studying public challenge/writeup material for a Skills V2 upgrade. It organizes research; it does not claim any challenges have been collected, solved, or evaluated. The initial DEVELOPMENT target is about **30 diverse challenges**, roughly three from each of the ten primary CTF categories in the intake schema. Adjust the mix when public material or capability gaps justify it.

## Keep the pools separate

The three JSONL files beside this guide are separate registries. Each non-empty line is one record validated by `python3 scripts/validate_research_intake.py`.

- **DEVELOPMENT** — public writeups/solutions may be studied. Record exposure as `public-solution-studied`; use this pool to find reusable methods.
- **REGRESSION** — previously exposed challenges for known-behavior checks. Record exposure as `previously-exposed`. These checks catch regressions; they are not held-out performance evidence.
- **HELD-OUT** — untouched, independent evaluation material. Record exposure as `untouched`, with no known contamination, writeups, technique labels, route assessments, methodology conclusions, or validation outcomes. Keep real held-out identities, artifacts, solution material and evaluation keys outside this repository and outside development/research sessions. The tracked `held-out.jsonl` is an empty placeholder, not a place to disclose the evaluation set.

Never move an exposed item back into HELD-OUT. If held-out material is encountered or contamination is suspected, quarantine it and remove it from evaluation; do not inspect its solution to resolve uncertainty. Reclassify exposed items as REGRESSION when useful. The validator rejects pool/exposure mismatches, duplicate challenge identities or artifact hashes across registries, and answer-like strings or answer-bearing field names.

## Intake and prioritize

For each DEVELOPMENT candidate:

1. Record the challenge source and public writeup source, then pin a source revision or SHA-256 of each retained challenge artifact before interpreting it. Record difficulty only with its source/evidence; use `null` when unavailable.
2. Mark exposure before reading. Search the routing index and canonical category references for the technique family; record matching route IDs, or leave routes empty and describe the missing capability. A remembered writeup is a hypothesis, not proof that the candidate target behaves the same way.
3. Prioritize only after deduplication. Score each dimension 0–3 and sort lexicographically by `(capability_gap, novelty, generalizability, evidence_quality, -estimated_cost)`. A high score means an unexplained capability gap, a genuinely new reusable method, evidence it applies beyond one challenge, reproducible support, and manageable study cost. Do not inflate novelty because a challenge name or payload is new.
4. Study source/writeup and only the additional artifacts needed to understand the technique. Capture missing/reusable methodology, dependencies, limitations, license/attribution, and reproducible evidence. Do not copy flags, candidate answers, credentials, live tokens, challenge-specific constants, or full solution narratives into records or Skills V2.

## Convert findings into library changes

Apply the existing `ctf-skill-upgrade` gates: search the canonical owner first, skip duplicates, improve a focused reference for a reusable variation, or add one focused reference only for a coherent missing technique. Add a helper only when a deterministic, parameterized operation recurs and benefits from tests; keep challenge constants out. Add a routing signal only when a specific observable clue maps reliably to the focused method and the fast route can be tested. Update category routers/catalog only when discoverability changes.

Every accepted method change should include independent benign regression evidence: synthetic artifacts/parameters that exercise the reusable logic without copying an answer. Keep challenge-specific reproduction details in the pool record or research notes, not the canonical skill. Recheck for duplicate text/routes, run the relevant route and Skills validators, and preserve source, revision/hash, attribution and license obligations.

## Before large-scale research

The three pool files are intentionally empty. No 30-challenge set has been collected or solved. Before starting, choose public DEVELOPMENT sources across categories and difficulty levels, populate one pinned record at a time, and review the priority ordering. Establish any independent HELD-OUT set separately, preregister its handling/evaluation protocol, and do not expose it to development materials or sessions. Model-powered evaluation requires its own authorization and controls; this intake does not measure Solve Rate or model adherence.
