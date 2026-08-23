# OAuth 2.0 / OpenID Connect CTF Reference

Canonical V2 reference for OAuth/OIDC login, authorization-code, token and account-linking weaknesses. Treat the protocol as a sequence of trust bindings rather than a parameter fuzzing exercise.

## Map the flow first

Record:

```text
client/app
authorization server / IdP
resource server / API
redirect URI
client_id
response_type / grant
scope
state
nonce
PKCE challenge/method
code -> token exchange
ID token / access token validation
account-linking rule
```

Useful discovery:

```text
/.well-known/openid-configuration
/.well-known/oauth-authorization-server
```

Read source/client JavaScript/config when supplied. Do not assume endpoint paths from generic examples.

## Core trust bindings

For each flow ask whether the server correctly binds:

- authorization code -> client;
- code -> exact redirect URI;
- code -> PKCE verifier where required;
- response -> initiating browser session (`state`);
- ID token -> issuer + audience/client;
- login identity -> verified provider subject, not only mutable/unverified email;
- refresh token -> original scope/client;
- account-linking action -> already authenticated account + CSRF/session intent.

CTF bugs usually break one of these bindings.

## Redirect URI validation

Determine whether validation is:

```text
exact registered URI
origin only
host suffix/prefix
path prefix
wildcard subdomain
open-redirect aware
```

Normalize candidate URIs using the **provider's actual URL parser**. Relevant discrepancy classes include:

- userinfo (`trusted@evil`);
- suffix/prefix hostname matching;
- alternate scheme/port;
- path normalization/traversal;
- registered-domain open redirect;
- wildcard subdomain with takeover/attacker-controlled route;
- parser differences around encoding/case.

A redirect endpoint controlled under an otherwise allowed origin may be enough to forward a code/token.

## `state` / login CSRF

Check whether `state`:

- exists;
- is unguessable;
- is tied to the browser session/flow;
- is verified exactly once;
- cannot be substituted across accounts/clients.

Missing state can cause **login CSRF/account confusion** even when it does not directly reveal a token. Model which account becomes bound to whose session.

## Authorization code handling

Test bindings, not just reuse:

- one-time use;
- short lifetime;
- client binding;
- redirect URI binding at token endpoint;
- PKCE verifier binding;
- code substitution between users/clients.

A captured code is only useful if the token endpoint accepts it under attacker-controlled conditions.

## PKCE

For public clients, determine whether:

- PKCE is required;
- `S256` is required/used;
- token endpoint checks the verifier against the original challenge;
- code can be exchanged without verifier or with a different client/session.

Do not label `PKCE absent` as the intended exploit unless code interception/substitution is actually possible in the challenge.

## OIDC token validation

For ID tokens verify:

- trusted issuer (`iss`);
- correct audience/client (`aud`, `azp` when relevant);
- signature/key source;
- nonce when used;
- expiration/time claims;
- provider subject (`sub`).

JWT/JWKS implementation bugs are owned by `references/jwt.md`; use this reference for protocol-level identity binding.

## Account linking / email trust

High-value CTF patterns:

- target links accounts using email rather than stable provider subject;
- provider email is not verified but app trusts it;
- attacker can pre-create/link an account to victim identifier;
- linking endpoint lacks CSRF/reauthentication;
- OAuth identity from one provider/client can be substituted into another path.

Follow the full mapping:

```text
provider identity -> target local account -> privilege/flag
```

## Scope / token confusion

Check whether:

- requested scopes are allowlisted for the client;
- refresh can escalate scope;
- an access token minted for one audience/resource is accepted by another;
- ID token is incorrectly accepted as API access token;
- tokens from another client/issuer are accepted.

The actual authorization check matters more than a decoded token containing an interesting scope string.

## Leakage

Look for code/token exposure through:

- callback open redirects;
- third-party resources/referrer behavior;
- browser history/logging;
- frontend JS/storage;
- error pages;
- attacker-controlled callback routes.

Remember URL fragments are normally not sent in HTTP `Referer`; model the browser flow precisely rather than relying on outdated generic leakage claims.

## Testing discipline

Use two controlled accounts where possible and label every code/token by:

```text
user, client_id, redirect_uri, state, PKCE verifier, issuer, audience, time
```

Then perform one substitution at a time. This makes account-confusion bugs far easier to reason about.

## Cross-category links

- JWT/JWK/JKU/signature confusion -> `references/jwt.md`.
- open redirect / URL parser primitive -> relevant Web server/client reference.
- IDOR after successful OAuth login -> auth/access reference.
- browser side-channel around callback -> client-side/XS-Leak references.

## Provenance

Consolidates V1 `exploiting-oauth-misconfiguration/SKILL.md` (Apache-2.0, author `mahipal`, blob `10e82ec8bd1f238d9f320d95073521e0738ac533`) with existing `ctf-web/auth-infra.md`. V2 removes generic assessment-report boilerplate and keeps the protocol trust-binding workflow.