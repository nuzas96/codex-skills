# Web Race Conditions / State-Machine Races

Canonical V2 reference for CTF concurrency bugs where multiple requests observe or mutate shared state without the required atomicity.

## Recognition

Strong candidates:

- check-then-update logic;
- one-use coupon/token/invite;
- balance/inventory counters;
- rate/attempt limits;
- registration uniqueness;
- multi-step email/password/MFA/account-link workflows;
- temporary files/background jobs;
- endpoints that transition through hidden intermediate states.

Source pattern:

```text
read state -> validate -> separate write/action
```

If the operation is protected by one atomic DB constraint/transaction, ordinary concurrency may not help; inspect the actual persistence semantics.

## Model the invariant

Before racing, write what should always be true:

```text
coupon_uses <= 1
balance >= 0
one account per email
reset token consumed once
inventory >= 0
```

Then identify the exact operations that can both pass a check before either commits the state change.

## Establish a state oracle

For every attempt record both:

- HTTP response;
- authoritative backend/application state after the batch.

Two `200` responses are not enough if one transaction later rolls back or both responses represent the same idempotent result.

Reset to a known starting state between trials when possible.

## Synchronization strategies

From least to most precise:

1. normal concurrent async/threads — fast first test;
2. multiple warmed connections with barrier release;
3. HTTP/1.1 last-byte synchronization;
4. HTTP/2 single-packet/gated request technique where supported.

Use the simplest method that produces a stable race window. Network concurrency is not the same as backend concurrency; connection pooling/proxy serialization can eliminate the race.

## Turbo Intruder single-packet concept

A gated batch can reduce arrival jitter:

```python
for _ in range(N):
    engine.queue(target.req, gate='race')
engine.openGate('race')
```

Exact Turbo Intruder APIs/engine modes can change; verify installed extension syntax and target protocol. The important technique is synchronized request completion, not copying a historical script verbatim.

## Hidden multi-endpoint races

Some of the strongest CTF races involve different actions:

```text
change identity attribute   ||   issue token/reset based on old attribute
create object               ||   claim/check object
validate upload             ||   consume/process file
```

Draw the state machine and identify a temporary state that should never be externally usable.

## Idempotency and deduplication

Check whether requests carry:

- idempotency key;
- nonce/version number;
- transaction ID;
- CSRF/token value consumed atomically.

If the server correctly deduplicates identical requests, a race may require distinct valid IDs/objects or a different pair of endpoints.

## Measuring success

Capture per request:

```text
request id
start/release time
status/body classifier
returned object/transaction id
post-batch authoritative state
```

Run a sequential control batch. A race finding should show a state outcome impossible under equivalent sequential execution.

## Common false positives

- UI/cached balance lags but DB is correct;
- several requests say success but only one commit exists;
- retry middleware repeats one transaction;
- eventual consistency temporarily shows stale state;
- client sends requests concurrently but proxy/backend serializes them;
- operation is intentionally multi-use.

## CTF chaining

Once a race is proven, minimize to the state transition needed for the flag. Typical outcomes:

- exceed a one-time limit;
- create contradictory ownership/role state;
- spend/read/use before validation commits;
- enter a privileged hidden workflow state.

Do not flood with hundreds of requests when a precise 2–20 request batch demonstrates the primitive.

## Cross-reference

Business-logic semantics may determine the invariant; use the business-logic reference for workflow modeling. `ctf-solve/references/modern-chains.md` is useful when the race is specifically a check/commit disagreement across different services/parsers.

## Provenance

Consolidates V1 `exploiting-race-condition-vulnerabilities/SKILL.md` (Apache-2.0, author `mahipal`, blob `0ac1641b530cdf1fc7ec5996b5f1a94679d43f0f`) with race/state-machine material already present in `ctf-web`. Generic assessment-report/remediation boilerplate is omitted.