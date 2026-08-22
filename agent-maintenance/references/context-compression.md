# Hermes Context Compression

Use when Hermes context appears to compact unexpectedly or the user wants to tune compression behavior.

## Two measurements can disagree

V1 investigation identified two conceptually different counters:

1. a visible/status value based on the last successful API request;
2. a fresh preflight estimate that can include system prompt, tool schemas, messages and planned output.

This means the visible bar can be stale while a new turn's preflight estimate crosses the compression threshold.

Do not conclude that an interrupt itself caused compression merely because compaction appeared on the next turn.

## Tool schema floor

Large enabled toolsets can contribute substantial context before conversation content is counted. If a session enables many unused tools, disabling unnecessary toolsets can create more usable message headroom.

## Important knobs

Common Hermes configurations have included:

```yaml
compression:
  enabled: true
  threshold: 0.5
  target_ratio: 0.2
  protect_last_n: 20
  protect_first_n: 3
```

Treat these as example/default values from the V1 environment, **not universal constants**. Inspect the live installed configuration first.

Conceptually:

- `threshold`: fraction of effective context at which auto-compression begins;
- `target_ratio`: how aggressively the compressed conversation is reduced;
- `protect_last_n`: recent messages kept verbatim;
- `protect_first_n`: early messages preserved;
- `enabled`: master switch.

## Diagnostic workflow

1. Inspect current Hermes/model/provider config.
2. Check the actual model/backend context limit exposed to this route.
3. Compare visible usage against configured compression threshold, not merely the full model window.
4. Inspect logs for compression, timeout, provider/fallback/auth failures.
5. Check enabled toolsets and schema overhead.
6. Make one setting change at a time.
7. Restart/relaunch the relevant process when required.
8. Verify with a fresh session/usage reading.

## Backend vs advertised model limits

Provider routes may expose a smaller effective window than a model supports elsewhere. Do not override local context length to a larger marketing/API number unless the active backend reports/supports it; otherwise requests may overfill and fail.

## Safer tuning sequence

When automatic compression is too early, prefer staged tuning rather than immediately disabling it:

```text
verify active limit/config
-> raise threshold moderately
-> adjust target ratio / protected recent messages if needed
-> disable unused toolsets
-> verify
```

V1 environments used examples around threshold `0.55` then `0.65` when more room was desired, but live-version behavior must be checked before applying those numbers.

When compression fires too late or summary generation times out, inspect any model-specific auto-raise setting, auxiliary compression timeout and fallback/auth errors before changing thresholds blindly.

## CTF continuity

Even perfect compression tuning does not replace `PROGRESS.md`. During active CTF work, persist findings before replies so a compression/error/provider switch cannot erase the solve state.

## Provenance

Consolidated from V1 `hermes-context-compression` (`SKILL.md` blob `94214c2d25ddde98fe9194193d9b3a32aad36d80`). Exact source-code paths and CLI syntax in V1 are environment/version-specific and should be revalidated before future upgrades.