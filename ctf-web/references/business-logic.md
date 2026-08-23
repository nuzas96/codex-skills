# Business Logic and Workflow Abuse

Use when the vulnerability is in application rules/state transitions rather than a parser memory or injection bug: prices, balances, rewards, approvals, one-time actions, ownership, checkout/payment, MFA/reset flows, referral systems, or game state.

## Model the State Machine

Do not begin with random parameter tampering. Write the intended transition first:

```text
state A --request/condition--> state B --request/condition--> state C
```

For each step record:

- required server-side state;
- client-supplied fields;
- invariant that should hold;
- identifier/owner used;
- whether the action should be one-time/idempotent;
- whether another endpoint can reach the same state.

Then test **missing, repeated, reordered, stale, cross-account, and concurrent** transitions.

## High-Value Mutation Classes

### Client-authoritative values

Compare UI-calculated values with backend-derived values: price, total, quantity, discount, balance, role, status, owner, currency, shipping, reward amount. Remove fields as well as changing them; defaults can be more interesting than extremes.

### Boundary / representation values

Test zero, negative, fractional, very large, duplicate, empty/null, alternate currency/unit, and integer-boundary inputs only where the backend type/logic makes them meaningful.

### Step skipping / replay

Attempt direct access to later states, repeat one-time requests, replay old signed/client state, reorder steps, reuse tokens/codes, and call alternate endpoints implementing the same transition.

### Cross-account state

Use two controlled accounts. Swap object IDs, cart/order/payment/customer IDs, referral codes, reset tokens, or parent relationships. This often overlaps IDOR/BOLA.

## Race Conditions

If the invariant is checked then updated separately, route to `race-conditions.md`. Synchronize at the server-side check/commit boundary. A concurrency bug is stronger evidence than simply sending many requests quickly.

## Common CTF Patterns

- save an old token containing client-trusted balance/state, spend it, restore token, then trigger a refund/return;
- negative quantity or refund adds credit;
- apply/redeem/claim can be repeated via alternate endpoint or stale state;
- payment/approval step can be skipped while confirmation endpoint trusts prior client state;
- cancel/return reverses one ledger but not reward/secondary ledger;
- account linking trusts email/provider identity incorrectly;
- hidden API fields override UI-restricted role/status/price;
- server validates object existence but not ownership.

## Evidence Discipline

For every mutation capture state **before and after** from a server-authoritative source. A response saying "success" is not enough. Check actual balance, inventory, order state, permissions, or flag eligibility.

Maintain a table:

| Hypothesis | Request change | Expected invariant | Observed state | Verdict |
|---|---|---|---|---|

This prevents repeating cosmetic mutations that never affect backend state.

## Common Failure Modes

- Fuzzing hundreds of values without modeling the workflow.
- Trusting client/UI behavior instead of backend state.
- Testing only one account when ownership is the real issue.
- Calling every repeated-request bug a race without synchronization evidence.
- Missing alternate endpoints that perform the same business action.
- Not replaying stale tokens/state after a transaction changes server data.

## Provenance

Consolidated from the original `testing-for-business-logic-vulnerabilities` Apache-2.0 skill, the repository's race-condition material, and existing CTF state-machine notes. Original source remains frozen on `archive/pre-restructure-20260823`.
