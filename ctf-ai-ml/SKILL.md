---
name: ctf-ai-ml
description: "Solve CTF AI/ML challenges involving adversarial examples, model weights/adapters, extraction/inversion/membership inference, poisoning/backdoors, neural-network collisions, prompt injection/jailbreaking, token/context manipulation, and tool-using LLM agents. Use when the model or AI agent is the primary solve surface."
---

# CTF AI/ML — V2 Router

Use `ctf-solve` for lifecycle/progress. First identify whether the challenge is a numerical ML model, model artifact/weights problem, or LLM/agent trust problem.

## Reference router

| Surface | Load first | Add only if needed |
|---|---|---|
| adversarial image/input/evasion/poison/backdoor | `adversarial-ml.md` | `model-attacks.md` |
| weights, LoRA, extraction, inversion, collision, membership | `model-attacks.md` | `adversarial-ml.md` |
| prompt injection, jailbreak, token/tool/context attack | `llm-attacks.md` | `ctf-web` if HTTP/auth becomes primary |

## First pass

1. Identify model/framework, input/output shape and exact evaluation/flag condition.
2. Determine what feedback is exposed: class, probability, logits, embedding, gradient, generated text, tool results or binary success/failure.
3. Identify attacker control: input only, model weights, adapter, training data, system/user prompt, retrieved data or tool arguments.
4. Build a local/equivalent scoring function whenever possible.
5. Optimize against the actual server preprocessing and acceptance rule, not a convenient local approximation.

## Adversarial ML discipline

Capture:

- preprocessing/normalization;
- allowed norm/distance/perturbation bound;
- clipping/quantization/file re-encoding;
- target vs untargeted condition;
- model ensemble/randomization;
- exact accepted file/data representation.

An adversarial tensor that succeeds before PNG/JPEG serialization may fail after quantization. Always validate through the same encode/decode pipeline as the challenge.

Use simple gradient/sign attacks first when gradients are available; escalate to iterative/optimization attacks only when the acceptance margin requires it.

## Model extraction / inversion

For query APIs, record what output granularity leaks:

```text
label only < confidence < logits < embeddings/gradients
```

Exploit the simplest model structure first. Linear models can often be recovered from carefully chosen basis/zero queries; more complex models may need distillation or boundary probing.

For inversion or gradient leakage, define the loss/regularization and verify reconstructed data against the challenge's actual criterion rather than visual similarity alone.

## Weight / adapter challenges

When weights or LoRA adapters are supplied:

1. compare architecture/config/state-dict keys;
2. inspect unusual tensors/scales/ranks;
3. diff clean/reference weights if available;
4. reproduce merge/application order exactly;
5. test whether small targeted parameter changes create the required collision/output.

Do not load an entire training stack if the flag depends on a small deterministic layer relation.

## LLM / agent decision tree

```text
input/control surface
  -> model-only prompt behavior?
  -> retrieved/untrusted content?
  -> hidden secret in context?
  -> tools with stronger privileges?
  -> output/validator parsing?
```

For tool-using agents, map:

- available tools and argument schemas exposed by the challenge;
- what authorization is enforced outside vs inside the model;
- whether tool output/retrieved data can inject instructions;
- multi-step tool chains;
- output parser/flag checker assumptions.

Treat the LLM as a probabilistic planner, not a security boundary. The exploitable primitive is usually a trust/authorization mismatch around model input, retrieved data, tool invocation or result handling.

## Prompt-injection discipline

Test categories systematically instead of sending random jailbreak prose:

- direct instruction conflict;
- delimiter/role confusion;
- encoding/token smuggling;
- indirect injection via files/pages/tool output;
- context-length/truncation behavior;
- output-format/parser confusion;
- tool-argument injection.

Keep prompts minimal so you can identify which mechanism changed behavior.

## Query budget / randomness

For remote stochastic models:

- establish baseline variance;
- reuse seeds/temperature controls when exposed;
- repeat only enough to estimate success probability;
- cache query/result pairs;
- avoid large blind searches until a scoring signal exists.

## Cross-category pivots

- web/API auth/session/proxy behavior becomes the blocker -> `ctf-web`;
- supplied native/serialized model loader must be reversed -> `ctf-reverse`;
- hidden model artifacts must be extracted from memory/disk -> `ctf-forensics`;
- mathematical crypto around model outputs becomes primary -> `ctf-crypto`.

## Completion criteria

- model/agent surface and attacker control are explicit;
- attack is evaluated through the challenge's exact preprocessing/validator;
- query randomness/budget is accounted for;
- final adversarial input/model/prompt is reproducible when possible;
- `PROGRESS.md` records model version/config, scoring condition and decisive result.

## V1 migration rule

AI/ML remains one top-level domain skill with three internal families: adversarial ML, model attacks and LLM/agent attacks. New techniques update those references instead of creating separate top-level skills.
