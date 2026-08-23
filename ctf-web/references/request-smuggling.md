# HTTP Request Smuggling / Desync

Canonical V2 reference for CTF HTTP request-boundary disagreement. Use only after the target evidence shows two or more HTTP processors (CDN/proxy/load balancer/app server) can interpret a request differently.

## Recognition

Strong signals:

- front-end proxy/CDN plus a separate origin/app server;
- HTTP/2 or HTTP/3 client side downgraded to HTTP/1.1 upstream;
- source/config reveals different parsers or normalization;
- ambiguous `Content-Length` / `Transfer-Encoding` handling;
- one request changes the next request on a reused connection;
- reproducible timeout/differential behavior caused by incomplete framing.

Response headers (`Server`, `Via`, cache/CDN headers) are hints, not proof of parser precedence.

## Model the parser chain first

Write the actual chain:

```text
client -> CDN/WAF -> reverse proxy/load balancer -> framework/server -> application
```

For each hop determine:

- protocol version in/out;
- connection reuse;
- whether CL/TE is normalized/stripped;
- header canonicalization;
- body framing rules;
- upgrade/downgrade behavior.

The vulnerability exists at a **boundary where adjacent hops disagree**.

## Classic families

### CL.TE

Front end uses `Content-Length`; backend honors chunked `Transfer-Encoding`.

Conceptual probe:

```http
POST / HTTP/1.1
Host: target
Content-Length: <covers bytes differently>
Transfer-Encoding: chunked

0

<suffix>
```

A useful detection variant makes one parser believe the body is complete while the other waits for more bytes. Measure against a baseline and a control request; a timeout alone is not proof.

### TE.CL

Front end honors chunking; backend uses `Content-Length`. Again, craft a boundary where the two parsers consume different byte counts and observe whether the subsequent backend parse is affected.

### TE.TE / header obfuscation

Both sides conceptually support TE but disagree on whether an obfuscated/duplicated header is valid. Modern infrastructure often normalizes or rejects historical tricks. Derive accepted syntax from the exact parser/version rather than cycling old payload lists blindly.

### H2/H1 downgrade / tunneling

When a front end accepts HTTP/2 but constructs HTTP/1.1 upstream, inspect how:

- `Content-Length` is synthesized;
- forbidden hop-by-hop headers are handled;
- `:path`, host/authority and header values are translated;
- CR/LF or duplicated pseudo/ordinary headers are validated;
- request bodies are delimited after downgrade.

Do not assume end-to-end HTTP/2 eliminates parser disagreement; inspect the actual backend protocol.

## Safe CTF detection workflow

1. Capture normal request/response latency and connection behavior.
2. Use raw bytes; disable client auto-recalculation of CL/chunk framing.
3. Send one minimal ambiguous probe.
4. Compare with a control that differs only at the framing ambiguity.
5. Repeat enough to rule out ordinary network delay.
6. If the server reuses connections, test whether a **second request** receives a reproducible parse anomaly.
7. Record raw bytes and timing/status evidence in `PROGRESS.md`.

Automated scanner output is a lead, not confirmation.

## Impact / CTF chaining

After confirming desync, look for the smallest intended second-stage effect:

- bypass a front-end-only path/host/method restriction;
- reach an origin-only route;
- poison a cache key/response association;
- cause a bot/next internal request to consume controlled prefix/suffix;
- exploit another parser/auth difference at the backend.

Do not jump directly to cross-user request capture in a shared environment when the CTF offers a deterministic self-contained oracle.

## Tooling

Useful tools depending on the challenge:

- Burp Repeater with automatic content-length updates disabled;
- HTTP Request Smuggler / Turbo Intruder;
- raw Python sockets/TLS for exact bytes;
- protocol-specific H2 tooling when downgrade behavior matters.

Prefer a tiny target-specific raw sender over a generic scanner once the primitive is understood.

## Pitfalls

- `curl -d '0\r\n\r\n'` may not send the raw bytes you think it does; verify wire representation.
- A 5–10 second response is not automatically CL.TE/TE.CL; compare controls.
- Closing the TCP connection after every probe can hide a queue-poisoning primitive.
- Front-end banners do not reveal which parser wins.
- Modern proxies patch well-known TE obfuscations; exact versions/config matter.
- HTTP/2 tests must distinguish true H2 parsing from H2->H1 translation.

## Cross-reference

If the confirmed desync only matters because it poisons a cache, use the cache-poisoning reference for the second stage. If the main vulnerability is URL/host normalization rather than message framing, use the relevant server-side/modern-chain reference instead.

## Provenance

Consolidates the high-signal CTF workflow from V1 `exploiting-http-request-smuggling/SKILL.md` (Apache-2.0, author `mahipal`, blob `6507b2217ef3fd897c1bda7a6b15cf04f732fb24`) plus existing `ctf-web` request-smuggling notes. Generic assessment-report/remediation boilerplate is intentionally not loaded into the active CTF reference.