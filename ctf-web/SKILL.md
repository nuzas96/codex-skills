---
name: ctf-web
description: Solve web-focused CTF challenges involving HTTP applications, APIs, browser/admin bots, authentication and authorization, SQL/NoSQL injection, SSTI, SSRF, XXE, deserialization, JWT/OAuth/OIDC, file/path handling, GraphQL/WebSockets, proxy/cache/request-smuggling behavior, prototype pollution, race/business-logic bugs, CSP/XSS/XS-Leaks, and Web3-integrated web surfaces. Use when the primary flag path crosses an application, browser, API, identity, proxy or server-side web trust boundary. Load only the specific internal references indicated by observed evidence.
license: MIT
compatibility: Requires normal web inspection tooling, Python 3 and target-specific dependencies. Install specialized tools only when the selected technique requires them.
metadata:
  user-invocable: "false"
---

# CTF Web — V2 Router

This file is a **router, not an encyclopedia**. Use `ctf-solve` for workspace, progress, triage, stuck recovery and multi-category lifecycle behavior. This skill owns only the web-domain decision tree.

## First pass

1. Read supplied source, dependencies, Docker/proxy config, templates, bot runner and JS bundles before broad fuzzing.
2. Capture one normal request/response for every major feature.
3. Map trust boundaries: browser -> CDN/WAF -> proxy -> app/router -> parser/template -> DB/filesystem/internal service.
4. Identify exactly where attacker-controlled data crosses a boundary.
5. Load **one focused reference** below from observed evidence.
6. Prove the smallest useful primitive before chaining to the flag.
7. Reproduce parser/browser/version-dependent claims on the exact target version whenever possible.

## Technique router

| Evidence / primitive | Load first | Add only if needed |
|---|---|---|
| SQL syntax/error/order/DB state | `sql-injection.md` | `field-notes.md` |
| Mongo/NoSQL operators, object-vs-string input, regex/$where oracle | `references/nosql-injection.md` | `server-side-advanced-4.md` |
| JWT/JWE/JWKS/kid/jku/x5u | `references/jwt.md` | `auth-and-access.md` |
| OAuth/OIDC/SSO/PKCE/state/redirect URI | `references/oauth-oidc.md` | `auth-and-access.md`, `auth-infra.md` |
| Login/session/IDOR/BOLA/role/object authorization | `auth-and-access.md` | `auth-and-access-2.md` |
| SSTI/template expression/rendering | `references/ssti.md` | relevant `server-side*.md` only after engine fingerprint |
| SSRF/internal fetch/URL resolver | `server-side.md` | one matching `server-side-advanced*.md`, modern chains |
| XXE/XML/SVG/DOCX/SOAP/parser | `references/xxe-xml.md` | relevant advanced XML/parser note |
| Deserialization/object reconstruction | `references/deserialization.md` | `server-side-deser.md` for historical CTF patterns |
| Traversal/LFI/file include/path canonicalization | `references/path-traversal-lfi.md` | one relevant `server-side-advanced*.md` |
| Upload -> parser/storage/execution | `server-side-exec.md` | `server-side-exec-2.md` / relevant advanced note |
| Command/code execution through backend parser | `server-side-exec.md` | `server-side-2.md` |
| GraphQL schema/resolver/auth path | `references/graphql.md` | modern chains for alternate resolver paths |
| WebSocket/Socket.IO/SignalR | `references/websockets.md` | auth/injection/race ref matching the message primitive |
| XSS/CSRF/DOM/admin bot | `client-side.md` | `client-side-advanced.md`, bot refs |
| CSP/browser restriction/scriptless exfil | `references/csp-browser.md` | `references/modern-xs-leaks-patterns.md`, `bot-*.md` |
| XS-Leak/admin-bot side channel | `references/modern-xs-leaks-patterns.md` | matching `bot-*.md` |
| DOMPurify/mXSS claim | `references/dompurify-3.3.1-mxss-verification.md` | exact-browser harness |
| Prototype pollution/Node merge/gadget | `references/prototype-pollution.md` | `node-and-prototype.md`, hard-pattern refs |
| Request smuggling/desync/proxy framing | `references/request-smuggling.md` | `ctf-solve/references/modern-chains.md` |
| WAF/filter blocks a proven primitive | `references/waf-parser-differentials.md` | underlying technique reference |
| Cache poisoning/deception/cache-key mismatch | `references/cache-attacks.md` | browser or parser ref for the resulting sink |
| Race/TOCTOU/concurrent state transition | `references/race-conditions.md` | `references/business-logic.md` |
| Workflow/state/price/balance/reward/step bypass | `references/business-logic.md` | race/auth refs as evidence demands |
| CVE/version banner/dependency leak | `cves.md` | current official advisory + exact-version proof |
| WordPress/SvelteKit/Vite/WASM/H2 hard chain | `references/web-hard-pattern-playbook.md` | `references/sekaictf2025-hard-web-patterns.md` |
| Solidity/Web3 app integration | `web3.md` | `ctf-crypto` only if pure cryptanalysis becomes dominant |

`server-side-advanced*.md` means read **one file whose table of contents matches the observed primitive**. Never load the whole advanced series by default.

## Core decision trees

### Authentication / token

```text
token/session observed
  -> decode representation
  -> determine verification/key source
  -> determine authorization source
  -> identify server-authoritative vs client-authoritative claims
  -> test one minimal trust failure
  -> forge/escalate only after the trust boundary is proven
```

### Server-side input

```text
user input
  -> which parser receives it?
  -> SQL / NoSQL / template / XML / path / command / serializer / URL fetch?
  -> harmless syntax or behavior oracle
  -> exact framework/parser/version
  -> smallest read/bypass/state primitive
  -> flag chain
```

### Browser / admin bot

```text
attacker input -> sanitizer/render -> browser -> sensitive origin/action/data
```

Capture exact browser version, CSP/COOP/CORP/Fetch-Metadata/SameSite/PNA behavior, origin/port/cookie scope, hosting CSP, and raw browser requests. Old browser tricks remain hypotheses until reproduced on the bot version.

### Proxy / cache / WAF

```text
raw request
 -> CDN/cache/WAF interpretation
 -> reverse-proxy interpretation
 -> framework/router interpretation
 -> backend parser interpretation
```

Look for disagreement in request boundaries, decode count, headers, URL/path normalization, Host, cache key, method, body/content type or duplicated parameters. If the bug lives between adjacent layers, use `ctf-solve/references/modern-chains.md`.

## Evidence-first web loop

For each hypothesis record:

1. normal baseline;
2. one controlled mutation;
3. exact observable difference;
4. server/browser state change;
5. whether the primitive survives local/exact-version reproduction;
6. next cheapest discriminating test.

Do not repeat payload families that already failed for a proven structural reason.

## Recon discipline

Start source-aware and filtered:

```bash
curl -sSik https://target/
curl -sS https://target/robots.txt
rg -n "route|admin|debug|secret|token|jwt|oauth|fetch|redirect|render|template|upload|graphql|websocket|cache" .
```

Only directory-fuzz when source/JS/routes do not expose the surface directly. Try alternate verbs/content types when the framework or intermediary behavior suggests a parser difference; do not spray them blindly.

## Useful category scripts

```text
scripts/jwt_analyze.py
```

Helpers accelerate testing; they do not prove exploitability. Save exact successful/failed evidence to `PROGRESS.md` through `ctf-solve`.

## Cross-category pivots

Add another category only when the **hard primitive changes**:

- native memory corruption after web foothold -> `ctf-pwn`;
- WASM/native client logic -> `ctf-reverse`;
- real cryptanalysis/custom MAC math -> `ctf-crypto`;
- PCAP/memory/disk artifact recovery -> `ctf-forensics`;
- public-world identity/geolocation -> `ctf-osint`;
- malicious payload/C2 behavior becomes central -> `ctf-malware`.

Do not preload categories speculatively.

## V2 ownership rule

A web vulnerability technique belongs under `ctf-web/references/` or `ctf-web/scripts/`, **not in another top-level skill**. Historical broad references remain for depth, but new upgrades should patch the most focused canonical reference and update this router only when a new technique family appears.

The complete V1 source remains recoverable from `archive/pre-restructure-20260823`.
