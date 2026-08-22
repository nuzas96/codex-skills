---
name: hermes-context-compression
description: Debug and tune Hermes Agent's automatic context compression. Load when the user asks why their context "suddenly" compacted, why the status bar shows one number but compression happens anyway, how to raise the compression threshold, or how tool schemas inflate token counts. Covers the two-counter system, preflight trigger, threshold defaults, and tuning knobs.
version: 1.0.0
author: agent (2026-06-19)
license: MIT
platforms: [linux, macos, windows]
---

# Hermes Context Compression

Hermes has automatic context compression that fires at TURN START, not on interrupt. The visible status bar can show "not full" while compression is about to fire. This skill explains why and how to tune it.

## When to load

- User: "kenapa context tk full tapi tiba-tiba compress?" / "why did context just compact?"
- Status bar / token count looks wrong or out of sync
- Tuning compression threshold
- Estimating room for a long session
- Repeated mid-session compaction is breaking the user's flow

## The two-counter problem (most common confusion)

Hermes has TWO independent measurements of context size:

**1. Status bar (what the user sees) — `context_percent`**
- Source: `last_prompt_tokens` from the LAST successful API response
- Updates: ONLY after a successful API call
- File: `cli.py:_get_status_bar_snapshot()` (~line 3677)
- Problem: STALE — does not reflect tool calls, memory injection, or interrupts since the last successful call

**2. Compression trigger — `estimate_request_tokens_rough`**
- Source: fresh estimate of system prompt + tool schemas + all messages + planned output
- Updates: every turn start (preflight check)
- File: `agent/conversation_loop.py:590-674`

**Symptom:** user sees "context not full" → interrupts → next turn runs preflight → fresh estimate crosses threshold → compress → user sees sudden drop and blames the interrupt.

**Root cause:** the visible counter is stale. Compression is fresh. They are not the same number.

## Preflight mechanism

`agent/conversation_loop.py:590-674`:
- Runs at the START of every turn (NOT on interrupt itself)
- Estimates: `system_prompt + tools + messages`
- Compares to `threshold_tokens` (= `context_length * threshold`)
- If estimate >= threshold → `_compress_context()` (up to 3 passes for huge sessions)
- `interruptible_api_call` only aborts the in-flight HTTP request; it does NOT directly trigger compression

## Tool schema impact (often missed)

Code comment at `conversation_loop.py:602-608`:
> "Include tool schema tokens — with many tools these can add 20-30K+ tokens that the old sys+msg estimate missed entirely."

Many toolsets enabled (terminal + file + browser + delegate + cron + ...) means a large schema floor. Disabling unused toolsets raises the floor below which preflight cannot fire.

## Default config

```yaml
compression:
  enabled: true
  threshold: 0.5        # aggressive — compress at 50% of context_length
  target_ratio: 0.2     # compress to 20% of threshold
  protect_last_n: 20
  protect_first_n: 3
  abort_on_summary_failure: false
```

For a 200K-token context window, compression fires at 100K tokens. With ~30K of tool schema on top, the conversation itself only has ~70K of room.

## Tuning knobs

| Knob | Effect | When to change |
|------|--------|----------------|
| `compression.threshold` | Fraction of context_length to fire at | Raise to 0.7-0.8 to delay compression |
| `compression.target_ratio` | Compress to this fraction of threshold | Lower = more aggressive summary |
| `compression.protect_last_n` | Messages never compressed | Raise if recent context is critical |
| `compression.protect_first_n` | Initial messages preserved | Raise if system setup matters |
| `compression.enabled` | Master switch | Disable for one long task, re-enable after |
| Toolset enablement | Reduces schema floor | Disable unused via `hermes tools` |

## Quick fixes

**"Context keeps compressing":**
1. First identify the provider route and displayed window. For `openai-codex` + `gpt-5.5`, Hermes may show ~272K context even when the direct OpenAI API advertises ~1M; this is expected because Codex OAuth/backend enforces its own `/models` cap. Do **not** paper over it with `model.context_length: 1000000` unless the backend itself reports the larger window, or Hermes will overfill requests and hit provider rejections.
2. If the user says "not even half and it compacted", compare against the configured threshold, not the full window. Example: 78.1K/272K is ~28.7%, but with `compression.threshold: 0.35`, auto-compress fires around 95K, leaving only ~17K headroom. That behavior is normal for the threshold even though the status bar looks low.
3. For Codex/gpt-5.5 users who want less early compaction while keeping safety, recommend a staged tune before disabling compression:
   ```bash
   hermes config set compression.threshold 0.55
   hermes config set compression.target_ratio 0.25
   hermes config set compression.protect_last_n 30
   ```
   If still too early, try `threshold 0.65`; reserve `0.7+` for users who accept higher overflow/compression-timeout risk.
4. `hermes tools` → disable unused toolsets if schema overhead is high.
5. `/compress` manually instead of letting it auto-fire when the user wants full control.
6. `/clear` when session is stale.

**"Compression fires too late / almost at model limit" (especially GPT-5.5 Codex):**
1. Check live config and logs first: `hermes config`, `hermes fallback list`, `hermes auth list`, and `grep -iE 'compress|compression|fallback|401|timeout' ~/.hermes/logs/agent.log* | tail -80`.
2. If `compression.codex_gpt55_autoraise: true` is present and logs show compression only near the context limit, disable the auto-raise and lower the threshold:
   ```bash
   hermes config set compression.codex_gpt55_autoraise false
   hermes config set compression.threshold 0.35
   hermes config set compression.target_ratio 0.2
   ```
3. If compression summaries time out at exactly 120s, raise the auxiliary compression timeout:
   ```bash
   hermes config set auxiliary.compression.timeout 360
   ```
4. If fallback/auth is noisy or broken, use the actual Hermes CLI syntax for this install: `hermes auth logout openrouter` then `hermes auth add openrouter`; `hermes fallback add` is interactive, then verify with `hermes fallback list`. If OpenRouter should not be used, remove/stale-fix `OPENROUTER_API_KEY` in the Hermes env instead of leaving a broken key.
5. Restart the process that matters: gateway via `systemctl --user restart hermes-gateway.service`; CLI sessions need exit/relaunch. Config changes are not guaranteed to fully affect an already-running chat.

**"Status bar says one thing, behavior says another":**
- Normal. Status bar is stale; compression is fresh.
- The next successful API call updates the bar.

**"I want full control":**
- `compression.enabled: false` for a single long task
- `/compress` for manual triggers
- `/usage` to see real token counts (CLI)

## Verification after changing threshold

1. `/clear` to start fresh
2. Send a few turns to populate context
3. Check `/usage` (CLI) for token counts
4. Watch status bar — it updates only after a successful API response, not instantly
