# Hermes Context Compression — Why "Context Not Full" Can Still Compact

CTF work depends on long, coherent context: hypotheses, dead-ends, oracle observations, exploit iterations. Losing it mid-solve is the most common reason a challenge gets abandoned and re-started. This file explains the exact mechanism Hermes uses to compact context, why the visible "context full" indicator is unreliable, and the knobs you can pull to make compression less aggressive.

## The two counters (the core confusion)

Hermes tracks context in two different ways that disagree:

1. **Visible status bar (`context_percent`)** — `cli.py:3677` `_get_status_bar_snapshot()`. This is `last_prompt_tokens / context_length` from the **last successful API response**. It only updates when an API call completes cleanly. After an interrupt, error, or compression, the bar is stale.

2. **Preflight compression trigger** — `agent/conversation_loop.py:590-674`. At the start of every new turn, Hermes runs `estimate_request_tokens_rough(messages, system_prompt, tools=...)` and compares against `compressor.threshold_tokens = int(context_length * threshold_percent)`. If the estimate is over, it compresses before the model is even called.

The preflight estimate **includes** system prompt + tool schemas + all messages. With many tools enabled, the tool-schema token cost alone is 20-30K+. This is in the source code comment at `conversation_loop.py:602-603`: "Include tool schema tokens — with many tools these can add 20-30K+ tokens that the old sys+msg estimate missed entirely."

So a session can show "60% full" in the status bar (only counting what the last API call sent) while the preflight check sees the real total of 90%+ (counting the system prompt and tool schemas that the bar ignores) and triggers compression.

## What this means in practice

The user observation "context tak full lagi tapi tiba-tiba compact" is real and reproducible. It is not a bug — it is the preflight check correctly using a more accurate estimate than the status bar displays. The bar is for the user, the preflight is for the model, and they measure different things.

Three concrete consequences:

- **The status bar cannot be trusted as "we have room".** Trust the file system, not the bar.
- **Interrupts do not directly cause compression.** The interrupt aborts the API call; the compression happens at the start of the next turn when preflight runs. The visual story of "interrupt → context drop" is two separate events back-to-back, not one.
- **Tool count is a hidden tax.** Every enabled toolset (terminal, file, browser, delegate, kanban, etc.) adds thousands of tokens to every single API call, regardless of whether you use it. The same conversation with 5 vs 15 toolsets has a very different compression behaviour.

## The knobs (in priority order)

### 1. Raise `compression.threshold` (biggest lever)

Default is `0.5` (50% of context_length). This is aggressive. Most users with a 32K+ context window can safely raise to `0.7` or `0.75` and still have enough headroom for the model's response.

```bash
hermes config set compression.threshold 0.7
```

Restart the session for it to take effect. Roll back to `0.5` if you start hitting actual context-limit errors (different signal: an API 4xx, not a compression event).

### 2. Disable unused toolsets

```bash
hermes tools
```

Interactive picker. Each removed toolset drops a few thousand tokens from every API call. The compression trigger ratio is the same, but the absolute threshold in tokens is lower because the total is lower — so reducing the total can either help or hurt depending on direction. Empirically, fewer tools = less aggressive compaction because there's more headroom relative to the new, smaller total.

### 3. Manual compression control

- `/compress` — manually trigger compression
- `/clear` — fresh start, drops all history
- `/undo` — remove the last exchange

Use `/compress` when you know a long stretch of the conversation is no longer needed (e.g., after a phase of the solve is done).

### 4. Fresh session per phase

For multi-day challenges, consider `/new` between phases. Each new session starts at 0% context and you control the trade-off explicitly.

## Why this matters specifically for CTF work

The PROGRESS.md discipline (see `progress-discipline` skill) exists because of this mechanism. If the agent has been writing to PROGRESS.md continuously, a compression event is recoverable: re-read the file, pick up the strongest branch, continue. If the agent has been batching writes at session end, a compression event in the middle loses everything that was in chat only.

The compression trigger is also a forcing function for **keeping notes external**. Anything important that lives only in chat context is a single compaction event away from being lost. The discipline is: write the finding to PROGRESS.md, then say it in chat. The chat is ephemeral; the file is durable.

## Quick diagnostic if the user reports "context compacts too early"

1. `grep -E "compression|threshold" ~/.hermes/config.yaml` — show the current threshold.
2. `hermes tools list` — show which toolsets are enabled.
3. Read `agent/conversation_loop.py:590-674` (preflight logic) to confirm the mechanism.
4. Read `cli.py:3677` (`_get_status_bar_snapshot`) to confirm the visible counter is `last_prompt_tokens`, not preflight estimate.
5. Recommend `hermes config set compression.threshold 0.7` as the first fix; explain the trade-off (less proactive safety net, but fewer mid-solve compressions).

## See also

- `progress-discipline` skill — the pre-reply gate that makes PROGRESS.md updates continuous.
- Hermes `agent/context_compressor.py` — full compression logic and `should_compress()` decision tree.
- Hermes `agent/conversation_loop.py:585-690` — preflight check, including the tool-schema accounting comment.
