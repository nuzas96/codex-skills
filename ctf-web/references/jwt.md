# JWT / JWE CTF Reference

Canonical owner for JWT/JWE token weaknesses in V2. Load this when the web challenge exposes compact tokens, JWKS/OIDC key discovery, token-carried authorization claims, or custom token verification.

## First classify the token

```text
3 dot-separated segments -> usually JWS/JWT
5 dot-separated segments -> usually compact JWE
```

Decode the protected header and claims **without assuming verification**. Record:

- `alg`, `typ`, `kid`, `jwk`, `jku`, `x5u`;
- `iss`, `aud`, `sub`, `exp`, `nbf`, roles/admin/balance/state claims;
- where the verifier obtains its key;
- whether the application trusts claims for authorization/state decisions.

Quick helper:

```bash
python3 scripts/jwt_analyze.py --token "$TOKEN"
```

## Decision tree

### 1. Is signature verification missing?

Some applications decode claims but never verify the signature. Modify one harmless claim first while retaining or replacing the signature. If accepted, the crypto layer is irrelevant; focus on the authorization claim needed for the flag.

### 2. Is `alg:none` accepted?

Test only when the verifier/library behavior makes it plausible. Generate a minimal variant:

```bash
python3 scripts/jwt_analyze.py \
  --forge-none \
  --payload '{"sub":"admin","role":"admin"}'
```

Case variants or malformed signatures are secondary tests, not separate attack classes. A strict algorithm allow-list rules this family out.

### 3. RS/ES asymmetric -> HS symmetric confusion

If the original token uses an asymmetric algorithm and the verifier trusts the header-selected algorithm, it may incorrectly use a public key as an HMAC secret.

Workflow:

1. obtain the exact public key bytes/format used by the verifier;
2. switch the header to the symmetric algorithm the library accepts;
3. HMAC-sign with those public-key bytes;
4. keep claims unchanged for the first acceptance test;
5. only then modify the minimum privileged claim.

```bash
python3 scripts/jwt_analyze.py \
  --forge-hs256 public.pem \
  --payload '{"sub":"admin","role":"admin"}'
```

Key formatting matters: PEM newlines/header form may need to match verifier input exactly. Derive this from source/library behavior rather than brute-forcing arbitrary representations first.

### 4. Embedded `jwk`

If the verifier accepts a public JWK supplied inside the token header, generate your own key pair, embed the matching public JWK and sign with your private key. The vulnerability is verifier trust in attacker-controlled key material.

Confirm whether `kid` or expected key type/algorithm must match an existing value.

### 5. Remote key URLs: `jku` / `x5u`

These headers can turn token verification into a key-fetch trust problem.

Check:

- whether arbitrary origins are allowed;
- redirect handling;
- DNS / resolved-IP validation;
- userinfo/parser mismatches;
- scheme restrictions;
- caching of fetched keysets/certificates;
- whether `kid` selects an attacker-controlled key from the fetched set.

Host only the minimal expected JWKS/certificate structure and prove the server fetches it before attempting privileged claims.

Treat this as a potential SSRF boundary as well, but keep JWT as the primary owner until internal-network access becomes the actual flag path.

### 6. `kid` injection / key lookup abuse

Determine how `kid` is resolved:

```text
filesystem path -> traversal/predictable file content
SQL/database lookup -> injection / alternate-row selection
URL/object lookup -> parser/SSRF behavior
map/dictionary lookup -> collisions/default-key behavior
```

Historical CTF patterns include using predictable empty or host files as HMAC key material, but verify the target's exact lookup code. Do not assume `/dev/null` or path traversal is available.

### 7. Weak symmetric secret

If the token genuinely uses HS256/HS384/HS512 with a human/config-derived secret, extract the token and test a targeted wordlist before large cracking jobs.

```bash
hashcat -m 16500 jwt.txt wordlist.txt
```

Use leaked config, challenge theme and source strings to build a high-signal candidate list first.

### 8. Replay / stale token state

A correctly signed token can still be vulnerable if mutable business state is trusted from old claims.

Test whether replaying an older valid token restores:

- balance/credits;
- inventory state;
- privilege/role;
- completion markers;
- nonce/version counters.

The important question is whether the server cross-checks current authoritative state.

### 9. JWE

JWE provides encryption, not automatically authorization semantics. If the server accepts any claims it can decrypt and exposes the encryption public key, determine whether an attacker can construct a new encrypted token with arbitrary claims.

Workflow:

1. identify `alg` and `enc` from the protected header;
2. obtain the exact public encryption key/JWKS;
3. reproduce a benign JWE first;
4. change one authorization/state claim;
5. send through the same cookie/header path.

If an additional signature/MAC or server-side state check exists, public-key encryption alone may not yield forgery.

## Authorization still matters

Token forgery is only one chain link. After creating an accepted token, verify how authorization is actually enforced:

- route decorator/middleware;
- object-level ownership;
- nested GraphQL resolver;
- role string vs numeric permission;
- server-side database state.

Do not equate `token accepted` with `admin access achieved`.

## Useful discovery paths

Common but source-dependent locations:

```text
/.well-known/openid-configuration
/.well-known/jwks.json
/jwks.json
/public-key
/oauth/token_key
```

Inspect application JS/config before blind path guessing.

## Testing discipline

For every token variant, keep the request otherwise identical and record:

- HTTP status;
- body/JSON difference;
- redirect behavior;
- server error that identifies verifier stage;
- whether the route reached authorization/business logic.

A 401/403 change can distinguish parsing, signature and authorization failures.

## Related references

- General session/authz/IDOR -> `../auth-and-access.md` during migration, later canonical auth reference.
- OAuth/OIDC trust flows -> `oauth-oidc.md` once migrated.
- SSRF caused by JKU/X5U fetch -> server-side/SSRF reference if network reach becomes primary.
- Business-state replay -> business-logic reference.

## Provenance

Canonical V2 consolidation of the former `ctf-web/auth-jwt.md` handbook plus the archived JWT algorithm-confusion / none-algorithm specialist material and reusable analyzer. A 2026-09-05 duplicate audit confirmed that signature-verification bypass, `alg:none`, asymmetric-to-HMAC confusion, JWK/JKU/X5U trust, `kid` lookup abuse, weak symmetric secrets, replayed state, and JWE public-key claim construction are represented here.

The one non-JWT legacy item — a custom encrypted session with attacker-controlled framing plus an unkeyed checksum — belongs to `../auth-and-access.md` and was migrated there before the redundant handbook was retired.

The untouched V1 source remains recoverable from `archive/pre-restructure-20260823` and Git history.