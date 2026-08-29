# Cross-Chain Bridge Relayer Races, Attestation Binding, and Replay Windows

Use this reference when a challenge has two chains or ledgers connected by an off-chain relayer that watches source events, signs an attestation, and submits a completion transaction on the destination chain.

This playbook is for **state-machine and trust-boundary bugs**, not signature cryptanalysis. If the decisive problem becomes breaking Ed25519/ECDSA/BLS itself, pivot to `ctf-crypto`.

## Recognition

Strong signals:

- source-chain `deposit` event followed by destination-chain `complete` or `release`;
- relayer-generated signatures/attestations;
- a `message_id`, nonce, event digest, or processed-message table;
- completion arguments that include fields not covered by the signed message;
- public pending-transaction or attestation endpoints;
- relayer delays, retries, failed-attestation records, or destination-RPC health checks;
- per-user receive caps, release buffers, delayed withdrawals, or retry queues;
- a failure path that mutates bookkeeping but does **not** consume replay protection;
- the same economic asset existing on two chains with independent accounting;
- cross-chain operation limits such as a global bridge-close counter.

Do not start by looking for a signature forgery. First determine exactly what a valid signature authorizes and what state transitions happen before, during, and after relayer submission.

## Model the bridge as five components

Write the actual pipeline before testing:

```text
source contract
  -> source event/log
  -> off-chain relayer watcher
  -> signed attestation / pending transaction
  -> destination completion call
  -> destination state + asset release
```

Track five independent state domains:

1. source-chain asset state;
2. source event identity;
3. relayer memory / pending queue / published attestation state;
4. destination replay-protection and accounting state;
5. destination asset state.

A bridge bug often exists because two of those domains disagree about whether a transfer is pending, failed, completed, or replayable.

## Step 1: reconstruct the exact signed message

Do not trust function signatures or field names. Rebuild the byte string exactly as the relayer and destination contract do.

Record:

```text
signed fields
unsigned execution fields
encoding
endianness
fixed-width vs variable-width fields
message-id derivation
source event identifier
```

Example structure:

```text
signature = Sign(
    recipient || amount_le || message_id
)

completion(
    recipient,
    amount,
    message_id,
    signature,
    fee_recipient   # not signed
)
```

If an economically meaningful field is accepted by the destination contract but omitted from the signed bytes, that field is attacker-selectable after the attestation is created.

High-value unsigned fields include:

- fee recipient;
- refund recipient;
- relayer/reward address;
- destination hook/callback;
- token/asset selector;
- gas/refund parameters;
- execution mode;
- auxiliary destination address.

### Minimal test

Take one valid attestation and change exactly one completion argument that is not present in the signed preimage. If verification still succeeds and economic state changes, the authorization boundary is incomplete.

## Step 2: distinguish attestation creation from attestation consumption

A valid attestation may exist before the official relayer submits it.

Look for:

- `/pending_transactions`;
- `/attestations`;
- relayer logs or status APIs;
- mempool-visible destination calls;
- retry queues;
- failed completion records;
- delayed submission windows;
- source-event-to-destination timers.

Construct a timeline:

```text
t0 source event committed
t1 relayer observes event
t2 relayer derives message_id
t3 relayer signs attestation
t4 attestation becomes externally observable
t5 official destination transaction submitted
t6 destination marks message processed
```

The exploitable race is usually between `t4` and `t6`.

If the attacker can obtain the valid attestation in that window, submit the destination completion directly with attacker-controlled unsigned fields.

## Step 3: treat liveness failures as state transitions

Do not assume relayer transport failure is harmless.

A common pattern is:

```text
source event
-> relayer signs
-> destination RPC becomes unavailable
-> official submit fails
-> relayer records/publishes the failed attestation
-> replay bit remains unset
```

This converts a transport failure into a **signed-but-unconsumed capability leak**.

When the challenge exposes deterministic node lifecycle behavior, test whether a destination outage can be induced after the source event but before official completion.

Useful discriminating questions:

- Is the signature created before the delay or after it?
- Does the relayer retain/publish the signature on transport failure?
- Does a failed submission leave the destination `processed` state untouched?
- Does the source event remain final after destination failure?
- Can the attacker submit the recorded attestation once the destination recovers?

### Important scope rule

The reusable lesson is **liveness manipulation of the bridge state machine**, not a specific node-crash payload. Do not copy real-world node 0day machinery into the skill. If a challenge supplies a deterministic crash/restart primitive, treat it as a challenge-local transport-failure mechanism.

## Step 4: audit replay protection placement

The key question is not only "is there a processed-message set?" but **when is it updated?**

Safe conceptual ordering:

```text
verify attestation
check replay
mark message consumed atomically with effects
perform destination accounting/release
```

Dangerous ordering:

```text
verify attestation
check replay
mutate buffer/accounting
external transfer fails
return success/error without marking processed
```

If failure mutates state while replay protection remains unset, replay the same signed message and measure the accumulated side effect.

Potential replay-amplified state:

- release buffer;
- credit/debt counter;
- retry allowance;
- claim quota;
- receive-cap headroom;
- refund balance;
- fee accounting;
- rate-limit bucket.

Do not call it replay exploitation until the same `message_id` is accepted more than once **and** the repeated attempt causes an additional state change.

## Failure-side-effect primitive

A particularly strong bridge primitive is:

```text
valid signed message
+ destination action intentionally forced to fail
+ failure updates bookkeeping
+ message remains unprocessed
= repeatable state mutation
```

This is stronger than a normal failed withdrawal because the attacker does not need new signatures for each bookkeeping mutation.

### Receiver-capability toggles

Some asset systems let the recipient temporarily become unable to receive an asset, for example through:

- removing a trustline;
- changing token authorization;
- closing an associated token account;
- deleting a receiver object;
- temporarily violating a receiver-side invariant.

If the bridge checks the attestation and updates buffer state before or around a transfer attempt, a receiver-capability toggle can deliberately drive execution into the failure branch.

Generic test:

```text
1. obtain valid attestation for attacker-controlled recipient
2. make recipient unable to receive
3. call completion
4. verify buffer/accounting changed
5. verify message_id is still unprocessed
6. repeat once
7. restore receiver capability
8. replay and observe successful release
```

The first two failed attempts are especially useful because they prove both replayability and accumulated state.

## Receive-cap and buffer accounting

If a destination enforces a limit like:

```text
received + amount <= base_cap + buffered
```

then `buffered` is security-sensitive state.

Audit every transition that changes:

```text
received
buffered_per_user
buffered_per_message
processed(message_id)
```

Write the transition table explicitly:

| Path | received | user buffer | message buffer | processed |
|---|---:|---:|---:|---|
| successful completion | +amount | maybe -consumed | maybe -consumed | true |
| failed transfer | unchanged | +amount | +amount | ? |
| outbound deposit | -amount or clamp | unchanged | unchanged | unchanged |

A replayable failure that adds to `buffered` can raise the effective receive cap without creating a new source-chain deposit.

## Relayer retry can amplify the bug for you

Do not model only attacker calls. The official relayer may retry or submit the same attestation independently.

Possible sequence:

```text
relayer attempt -> failure side effect #1
attestation becomes visible
attacker replay -> failure side effect #2
receiver restored
attacker replay -> success
```

That means a single source event may create multiple buffer increments before one final successful release.

Track actor identity for each state transition:

```text
relayer
attacker
honest user
node supervisor/retry worker
```

## Step 5: model the economics before automating

For every strategy compute the maximum attainable value.

Track balances as a ledger:

```text
player_chain_A
player_chain_B
bridge_pool_A
bridge_pool_B
honest_chain_A
honest_chain_B
fees_stolen_A
fees_stolen_B
```

For fee `floor(amount / d)`:

```text
recipient_amount = amount - floor(amount/d)
fee = floor(amount/d)
```

Repeated back-and-forth bridging produces a geometric decay plus integer rounding. Calculate the exact sequence instead of estimating.

A nearly sufficient strategy is evidence, not a solve. If claims + redirectable fees reach 245 but the flag threshold is 250, the missing 5 proves another primitive is required.

### Conservation check

Ask after every proposed exploit:

```text
Did I create value?
Did I merely move my own value between chains?
Did I steal a fee?
Did I duplicate a release without burning/locking a corresponding source asset?
Did a rollback restore source-chain spendable state after destination release?
```

This prevents wasting time on bridge loops that only reshuffle the same tokens.

## Step 6: include bridge-wide operation budgets

Hard bridge challenges often add a global counter to prevent unlimited probing.

Examples:

```text
bridge_close
processed count
nonce window
rate-limit epoch
maximum deposits
```

Before executing a multi-stage plan, budget every operation:

```text
honest traffic
attacker claim
attacker deposits
manual completions
relayer completions
retries that consume the counter
```

Do not discover at the final stage that the global operation budget has been exhausted.

## Cross-chain event identity

Relayers often derive message IDs from source event IDs:

```text
message_id = H(chain_name || source_event_id)
```

Record exactly what makes the source event unique:

- transaction digest;
- event sequence;
- ledger/event ID;
- log index;
- block/checkpoint height.

If a chain rollback/restart can recreate economically equivalent state under a **different event ID**, test whether the relayer treats it as a new bridge message.

Conversely, if the same event ID survives a restart, test whether relayer in-memory deduplication is lost while on-chain `processed` state remains authoritative.

## Soroban / Stellar notes

When the destination uses Soroban and a Stellar Asset Contract (SAC), record:

- whether the recipient has the required trustline;
- whether the trustline is authorized;
- whether `try_transfer` failure is caught or propagated;
- whether failure branches still update persistent storage;
- whether `Address::require_auth()` protects the relevant function;
- whether replay state uses instance or persistent storage;
- whether amount encoding is signed/unsigned and fixed-width;
- whether the fee recipient is covered by the attestation.

A missing trustline can be more than an error condition: it may be a controllable way to enter a bridge buffering branch.

## Sui / Move notes

For Sui bridge contracts, record:

- shared-object IDs and package ID;
- exact `MoveEventType` consumed by the relayer;
- BCS encoding of recipient and amount;
- coin object ownership and coin splitting/merging;
- which entry functions increment global operation counters;
- whether public JSON-RPC allows transaction construction/submission;
- whether a failed relayer submission is recorded with its attestation;
- whether node restart restores a checkpointed snapshot.

Do not assume EVM transaction/mempool semantics apply to Sui.

## Practical attack workflow

```text
1. map both contracts and relayer
2. reconstruct signed bytes in each direction
3. diff signed fields vs completion arguments
4. locate pending/failed attestation visibility
5. calculate baseline claims and fee-theft ceiling
6. identify any liveness window before official completion
7. test one unsigned-field front-run
8. inspect failure paths for state mutation without replay consumption
9. deliberately trigger one safe failure on attacker-owned state
10. replay same message_id and measure accumulation
11. calculate final cross-chain balance path
12. execute only after operation-budget math works
13. verify destination balance and flag condition
```

## High-value evidence to preserve

Record in `PROGRESS.md`:

- exact signed preimage layout;
- fields omitted from the signature;
- message-id derivation;
- source event ID and timestamp/order;
- relayer delay/retry behavior;
- pending/failed attestation JSON minus secrets unrelated to the challenge;
- destination `processed` state before/after failures;
- buffer/received values after each replay;
- fee sequence and balance projection;
- operation-budget consumption;
- final deterministic replay sequence.

## Common dead ends

### Trying to forge Ed25519 first

If the relayer already exposes valid signatures or has an unsigned completion field, signature cryptanalysis is the wrong first move.

### Assuming every completion argument is authenticated

Verification can be cryptographically correct while authorization is incomplete because execution fields are omitted from the signed preimage.

### Treating failed completion as "no state change"

Inspect persistent storage and events after failure. A caught transfer error may leave buffers or counters mutated.

### Ignoring the official relayer after front-running

Its later retry may create another state mutation or race with the attacker. Model both calls.

### Stopping at a profitable but insufficient fee theft

Compute the exact flag threshold. Near-miss economics are often a deliberate clue for a second primitive.

### Copying an EVM bridge playbook to Soroban/Sui

Rebuild serialization, ownership, event, RPC, and replay semantics from source. EVM assumptions about ABI, mempools, revert atomicity, and token receivers may not transfer.

## Completion criteria

A cross-chain bridge challenge is solved only when all of the following are reproduced:

- exact attestation bytes are understood;
- the authorization gap or replay primitive is independently demonstrated;
- relayer timing/state is accounted for;
- cross-chain balance math reaches the required threshold;
- replay/processed state is verified on the destination;
- the final balance/flag condition is reproduced from the live or supplied challenge.

## Provenance

Generalized from a SekaiCTF 2026 cross-chain bridge challenge using a Soroban/Stellar side, a Sui Move side, and an off-chain Ed25519 relayer. The reusable lessons are attestation-field binding, pending/failed-attestation races, liveness-induced signed-capability disclosure, replayable failure-side effects, receive-buffer amplification, and cross-chain economic accounting. Challenge flags, concrete account keys, fixed addresses, deployment IDs, node-crash payloads, and challenge-specific timing constants are intentionally omitted.