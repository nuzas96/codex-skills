---
name: ctf-web
description: Solve web-focused CTF challenges involving HTTP applications, APIs, browser/admin bots, authentication and authorization, SQL/NoSQL injection, SSTI, SSRF, XXE, deserialization, JWT/OAuth/OIDC, file/path handling, GraphQL/WebSockets, proxy/cache/request-smuggling behavior, prototype pollution, race/business-logic bugs, CSP/XSS/XS-Leaks, and Web3-integrated web surfaces. Use when the primary flag path crosses an application, browser, API, identity, proxy or server-side web trust boundary. Load only the specific internal references indicated by observed evidence.
license: MIT
compatibility: Requires normal web inspection tooling, Python 3 and target-specific dependencies. Install specialized tools only when the selected technique requires them.
metadata:
  user-invocable: "false"
---

# CTF Web — V2 Router

This file is a **router, not an encyclopedia**. Start with the application evidence and load only the smallest relevant reference set.

Use `ctf-solve` alongside this skill for workspace/progress/stuck-recovery lifecycle behavior.

## First pass

1. Read supplied source, dependency files, Docker/proxy config and bot runner before broad fuzzing.
2. Capture one normal request/response for each major feature.
3. Map trust boundaries: browser -> proxy/CDN -> app -> parser/template -> DB/filesystem/internal service.
4. Identify where user-controlled data crosses a boundary.
5. Choose one technique family below and load only its references.
6. Build a small primitive before chaining to flag access.
7. Test browser/parser/version-dependent behavior on the **exact target version** when possible.

## Technique router

| Signal / primitive | Load first | Add only if needed |
|---|---|---|
| SQL syntax/error/order/DB state | `sql-injection.md` | `field-notes.md` |
| Mongo/NoSQL operators or regex oracle | `server-side-advanced-4.md` | specialist NoSQL migration reference when available |
| JWT/JWE/JWKS/kid/jku/x5u | `references/jwt.md` | `auth-and-access.md`, `auth-infra.md` |
| OAuth/OIDC/SAML/CORS/IdP flow | `auth-infra.md` | `auth-and-access.md` |
| Login/session/IDOR/role/object auth | `auth-and-access.md` | `auth-and-access-2.md` |
| SSTI/template expression/rendering | `server-side.md` | `server-side-exec.md`, hard-pattern refs |
| SSRF/internal fetch/URL resolver | `server-side.md` | `server-side-advanced*.md` |
| XXE/XML/SVG/DOCX/parser | `server-side-2.md` | `server-side-advanced*.md` |
| Deserialization/object reconstruction | `server-side-deser.md` | `server-side-exec.md` |
| Traversal/LFI/wrapper/archive/path parser | `server-side-advanced.md` | `server-side*.md` |
| Upload -> parser/storage/execution | `server-side-exec.md` | `server-side-exec-2.md`, `server-side-advanced*.md` |
| Command/code execution | `server-side-exec.md` | `server-side-2.md` |
| GraphQL schema/resolver/auth path | `server-side-2.md` | hard-pattern/modern-chain refs |
| XSS/CSRF/DOM/admin bot | `client-side.md` | `client-side-advanced.md`, bot refs |
| CSP/XSSI/CSS/postMessage/browser quirks | `client-side-advanced.md` | `references/modern-xs-leaks-patterns.md` |
| XS-Leak/admin-bot side channel | `references/modern-xs-leaks-patterns.md` | other `references/bot-*.md` |
| DOMPurify/mXSS claim | `references/dompurify-3.3.1-mxss-verification.md` | exact browser test |
| Prototype pollution/Node sandbox | `node-and-prototype.md` | hard-pattern refs |
| Request smuggling/proxy disagreement | `client-side.md` + server/proxy source | `ctf-solve/references/modern-chains.md` |
| Cache poisoning/deception | `client-side.md` | proxy/cache-specific specialist source during migration |
| Race/state-machine/business logic | `server-side-deser.md` / `field-notes.md` | `ctf-solve/references/modern-chains.md` |
| CVE/version banner/dependency leak | `cves.md` | freshest official advisory + exact local version proof |
| WordPress/SvelteKit/Vite/WASM/H2 hard chain | `references/web-hard-pattern-playbook.md` | `references/sekaictf2025-hard-web-patterns.md` |
| Solidity/Web3 app integration | `web3.md` | `ctf-crypto` only if pure crypto becomes dominant |

`server-side-advanced*.md` means load the **one** file whose table of contents matches the primitive; do not read every advanced file by default.

## Core decision trees

### Authentication / token

```text
token/session observed
  -> decode structure and claims
  -> determine verification/key source
  -> determine authorization source
  -> test one minimal trust failure
  -> only then forge/escalate
```

JWT/JWE uses `references/jwt.md`; do not activate separate JWT top-level skills in V2.

### Server-side input

```text
input reaches server
  -> where is it parsed?
  -> template / SQL / XML / path / command / serializer / URL fetch?
  -> smallest syntax/behavior oracle
  -> confirm exact parser/framework
  -> derive exploit from target behavior
```

### Browser/admin bot

```text
attacker input -> sanitizer/render -> browser -> sensitive origin/action
```

Capture:

- exact browser version;
- CSP/COOP/CORP/Fetch-Metadata/SameSite behavior;
- origin/port/cookie scope;
- whether HTML hosting/exfil endpoint introduces its own CSP;
- actual raw browser requests.

Do not trust old browser tricks until reproduced on the bot version.

### Proxy/cache/parser mismatch

List each interpretation layer independently:

```text
raw request -> CDN/WAF -> reverse proxy -> framework/router -> backend parser
```

Look for disagreement in lengths, headers, URL normalization, host, cache key, method or path. Use `ctf-solve/references/modern-chains.md` when the vulnerability exists between adjacent layers.

## Empirical testing rule

Browser/library claims are hypotheses until reproduced on the actual relevant version.

Examples that require exact-version verification:

- browser URL CRLF behavior;
- DOMPurify mXSS;
- SameSite/cookie behavior;
- PNA/private-network requests;
- framework parsing quirks;
- proxy/backend desynchronization;
- recently patched CVE chains.

Prefer a minimal local harness that records raw behavior. Write the version and result to `PROGRESS.md`.

## Recon discipline

Start filtered and source-aware:

```bash
curl -sSik https://target/
curl -sS https://target/robots.txt
rg -n "route|admin|debug|secret|token|jwt|fetch|redirect|render|template|upload|graphql|websocket" .
```

Only use directory fuzzing after source/JS/routes do not expose the surface directly.

Try alternate verbs/content types when framework behavior suggests they matter; do not spray every verb blindly.

## Useful category scripts

```text
scripts/jwt_analyze.py
```

Scripts are helpers, not proof. Validate generated payloads against target behavior and keep successful/failed results in progress.

## Cross-category pivots

Switch/add a category only when the hard primitive changes:

- native memory corruption after web RCE -> `ctf-pwn`;
- WASM/native client logic -> `ctf-reverse`;
- real cryptanalysis/token math -> `ctf-crypto`;
- PCAP/memory/disk artifact recovery -> `ctf-forensics`;
- public-world identity/geolocation -> `ctf-osint`;
- malicious payload/C2 behavior becomes central -> `ctf-malware`.

Do not preload those categories speculatively.

## V1 migration note

V1 contains many standalone web technique skills. During V2 they are being deduplicated into this category's references/scripts. Until migration validation is complete, the frozen authoritative originals remain on `archive/pre-restructure-20260823`.

Canonical V2 rule: **web technique = internal `ctf-web` reference/script, not another top-level skill.**
