# GraphQL CTF Playbook

Use when an HTTP/API challenge exposes GraphQL, GraphiQL/Playground, Apollo, Hasura, Relay-style object graphs, or a JSON body containing `query`/`variables`.

## First Pass

1. Locate the real endpoint from source/JS/config before path brute force when source exists.
2. Send `{ __typename }` to confirm GraphQL behavior.
3. Test both GET and POST only if the server/router plausibly supports both.
4. Determine authentication context before schema analysis.
5. Build an object graph, then look for every resolver path to sensitive data/actions.

## Introspection

If enabled, introspection is a map, not automatically the vulnerability. Extract:

- query/mutation/subscription roots;
- object/input/interface/union types;
- arguments and nullability;
- deprecated or debug/admin fields;
- relationships that reach the same sensitive object through different parents.

Save the schema once rather than repeatedly running full introspection.

## When Introspection Is Disabled

Use GraphQL's validation errors as a targeted oracle. Misspelled fields/types may reveal suggestions. Tools such as Clairvoyance can help, but source/JS bundles/generated TypeScript clients and persisted-query manifests are often cheaper and more accurate in CTFs.

## Authorization: Highest-Value CTF Pattern

Authorization frequently differs by resolver path.

```text
protected direct resolver
    X user(id: secret)

unguarded nested path
    parent -> relation -> user -> secretField
```

Enumerate direct lookup, list/search, parent-child, reverse relation, nested object, mutation return objects, and subscription payloads. Test **field-level** authorization separately from object-level authorization.

## Mutations / Mass Assignment

Inspect mutation input types for fields the UI never sends: role, owner, status, price, balance, verified, permissions, internal IDs, or nested objects. Compare server acceptance with client-side restrictions.

## Batching / Aliases

Aliases and batched requests can change rate-limit/auth behavior or turn a single request into many logical operations. Use them only after identifying a meaningful per-operation constraint. A large query by itself is not useful unless the challenge depends on a limit bypass or side channel.

## Query Depth / Complexity

Resource-exhaustion techniques are usually secondary in CTFs. Prefer flag-path primitives first. Deep recursion can still matter when complexity limits or expensive nested resolvers reveal a side channel, but avoid noisy DoS-style probing without evidence.

## Variables, Directives, and Parser Differences

Test whether validation/filtering occurs on raw query text while dangerous values arrive through variables, fragments, directives, aliases, or persisted queries. Map which layer sees which representation.

## GraphQL + Other Categories

- JWT/OAuth auth -> `jwt.md` / `oauth-oidc.md`.
- SQL/NoSQL inside resolver -> relevant injection reference.
- Upload scalar -> upload/server-side references.
- WebSocket subscriptions -> `websockets.md`.
- Alternate resolver path / cross-layer mismatch -> `ctf-solve/references/modern-chains.md`.

## Common Failure Modes

- Calling introspection itself the exploit.
- Testing only top-level queries and missing nested authorization gaps.
- Brute-forcing names despite schema fragments in JS/source.
- Ignoring mutation input fields the UI hides.
- Sending giant recursive queries before understanding the flag path.

## Provenance

Consolidated from the original `performing-graphql-introspection-attack` Apache-2.0 skill plus existing `ctf-web/server-side-2.md` and modern-chain GraphQL notes. Original source remains frozen on `archive/pre-restructure-20260823`.
