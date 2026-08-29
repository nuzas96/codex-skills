# Browser Response Desync + Service-Worker Range Oracles

Use this reference for hard web/admin-bot challenges where the blocker is not a classic request-smuggling primitive, but a **browser-visible response-framing mismatch** created by a proxy/rewrite layer, optionally followed by an XS-Leak that depends on HTTP Range behavior.

This playbook was generalized from SekaiCTF 2026 `EnD`. Keep the method; do not reuse challenge-specific hosts, keys, flags, offsets, or timing constants.

## Strong recognition signals

Load this reference when several of these appear together:

- a reverse proxy rewrites response framing headers such as `Content-Length` or `Transfer-Encoding`;
- the proxy still streams/pipes the upstream body after claiming a different downstream length;
- filtering is conditional on browser metadata such as `Sec-Fetch-Dest: script`;
- attacker-controlled upstream content is exposed under the sensitive origin through a read/proxy feature;
- an admin bot uses Chromium and makes many same-origin subresource requests;
- direct script execution is blocked by CSP/filtering, but HTTP/1.1 keep-alive remains enabled;
- the sensitive API is cross-origin only by port/host and CORS/PNA prevents ordinary `fetch` reads;
- the API supports conditional/range responses such as `206 Partial Content` and `416 Range Not Satisfiable`;
- a prefix/search endpoint changes response length depending on whether a candidate matches secret data.

Do not route here merely because CSP exists or because a proxy exists. The key evidence is **response framing disagreement** or a **Range-based browser oracle**.

---

## Part A — Response-side browser desynchronization

### 1. Distinguish request desync from response desync

Classic request smuggling asks:

```text
front end consumes request bytes differently from backend
```

This pattern asks:

```text
proxy/upstream emits one body length
browser is told a different body length
```

Example vulnerable shape:

```js
const h = { ...upstream.headers }

if (req.headers['sec-fetch-dest'] === 'script') {
    h['content-length'] = '0'
    delete h['transfer-encoding']
}

res.writeHead(upstream.statusCode, h)
upstream.pipe(res) // body still goes out
```

The proxy has told the browser the response ends immediately, but extra bytes still arrive on the same persistent HTTP/1.1 connection.

That is a **downstream response boundary bug**.

### 2. First discriminating test

Before building a full bot exploit, verify all four facts:

1. the downstream client receives `Content-Length: 0` or another shortened boundary;
2. the upstream body is still physically written after that boundary;
3. the client connection remains reusable;
4. another request is queued or later sent on that same connection.

If any one is false, response queue poisoning may not be viable.

Use a raw client, packet capture, Node/Python socket harness, or browser DevTools-equivalent logging. Do not infer this only from source.

### 3. Why multiple subresources matter

Modern browsers use a bounded number of concurrent HTTP/1.1 connections per origin. A page with more simultaneous subresources than available sockets creates a queue.

Conceptual setup:

```html
<script async src="r1.js"></script>
<script async src="r2.js"></script>
<script async src="r3.js"></script>
...
<script async src="rN.js"></script>
```

If one response is framed downstream as empty, Chromium may consider that connection free and assign a queued request to it. Extra bytes arriving after the fake end boundary can then be parsed as the **next HTTP response**.

This is the browser-side analogue of response queue poisoning.

### 4. Smuggled response structure

The attacker-controlled upstream body can begin with a complete HTTP response:

```text
HTTP/1.1 200 OK\r\n
Content-Type: application/javascript\r\n
Content-Length: <len>\r\n
Connection: keep-alive\r\n
\r\n
<javascript bytes>
```

The outer upstream response length must be large enough for the proxy to accept and forward these bytes as body data.

The vulnerable proxy rewrites only the **outer downstream framing**. The browser then parses the body bytes as a fresh response for a queued request.

### 5. Turning a metadata block into script execution

A common CTF pattern is:

```text
if request destination == script:
    return empty body
```

Direct script requests are therefore useless.

Response desync changes the question from:

```text
Can I make the proxy return JavaScript for this script request?
```

to:

```text
Can I make the browser associate an injected response with a later script request?
```

The injected response bypasses the proxy's response-rewrite logic because the proxy does not parse it as a second response; only the browser does.

If the later request is same-origin and CSP allows `'self'`, the smuggled JavaScript executes in the sensitive origin.

### 6. Reliability choreography

The exploit usually needs deterministic connection reuse, not random spraying.

Useful controls:

- create more concurrent subresources than the browser's per-origin HTTP/1.1 socket budget;
- delay normal responses so queued requests stay pending;
- make the desync response complete earlier so its socket becomes the preferred reusable connection;
- keep the target connection alive;
- use `async` resources when parser blocking would otherwise serialize requests;
- make successful execution self-report to an attacker callback.

Do not hardcode "six browser connections" as a universal invariant. Confirm the exact Chromium/version/network behavior.

### 7. Validation after execution

A good proof script should record:

```text
smuggled response sent
-> callback from same-origin JS
-> authenticated same-origin fetch succeeds
-> sensitive page length/marker observed
```

Do not call the primitive solved merely because malformed bytes were sent.

---

## Part B — Same-origin foothold to admin data

Once arbitrary JavaScript executes in the protected web origin, prefer a direct same-origin read:

```js
const html = await fetch('/admin', {
    credentials: 'include'
}).then(r => r.text())
```

This can recover non-cookie secrets rendered into authenticated HTML even when the session cookie is `HttpOnly`.

Important distinction:

```text
HttpOnly blocks JavaScript from reading the cookie value.
It does NOT stop same-origin JavaScript from making authenticated requests with that cookie.
```

If the page exposes an internal API endpoint/key pair, parse the smallest required values and move to the API oracle rather than trying to steal the session token itself.

---

## Part C — Service Worker interception of cross-origin subresources

A Service Worker controls **requests initiated by a controlled client**, including cross-origin subresource requests. This is more powerful than treating Service Workers as same-origin fetch caches only.

A controlled page can therefore observe/interpose on a cross-origin media request even though the page cannot read the cross-origin response body directly.

Conceptual service worker:

```js
self.addEventListener('fetch', event => {
    const req = event.request
    // inspect destination / Range header / URL
    // optionally synthesize a response
    // optionally fetch(req) and retain a clone
})
```

Verify this on the exact browser version. Service Worker response-type restrictions are part of the exploit surface.

---

## Part D — Media-generated Range requests as an oracle

### 1. Why media elements are useful

`<audio>` and `<video>` commonly issue byte-range requests. This gives the attacker browser-generated requests with `Range` headers without needing forbidden custom headers in page JavaScript.

A useful controlled sequence is:

```text
Range: bytes=0-
then
Range: bytes=T-
```

where `T` is an attacker-chosen threshold.

### 2. Force the second range request

The Service Worker can answer the initial `bytes=0-` request with a synthetic partial media response:

```http
HTTP/1.1 206 Partial Content
Content-Type: audio/mpeg
Content-Range: bytes 0-(T-1)/<large-total>
Accept-Ranges: bytes

<T bytes>
```

Chromium then has reason to request the next range beginning at `T`.

The Service Worker can let that second request go to the real cross-origin API:

```js
const response = await fetch(event.request)
stashed = response.clone()
return response
```

Even when the response is opaque to page JavaScript, the Service Worker can often retain/relay the `Response` object subject to Fetch/Service Worker rules.

### 3. Convert response length into 206 vs 416

Suppose an endpoint returns:

```json
{"results":[]}
```

for a wrong secret prefix, but includes a long secret value for a correct prefix.

Pick threshold `T` such that:

```text
wrong-prefix body length <= T
correct-prefix body length > T
```

Then a request with:

```http
Range: bytes=T-
```

naturally separates the cases:

```text
correct prefix -> satisfiable range -> 206
wrong prefix   -> unsatisfiable range -> 416
```

This is much stronger than noisy timing: the application itself becomes a deterministic length oracle.

### 4. Response laundering into a same-origin request

The page still cannot inspect the cross-origin status directly.

A useful Service Worker trick is to stash the cross-origin response and later return it for a controlled same-origin `no-cors` request:

```js
fetch('/probe.css', { mode: 'no-cors' })
```

The Service Worker answers `/probe.css` with the previously stashed response.

Browser response validation can then create a boolean signal. In the harvested pattern:

- relaying an underlying `206 Partial Content` to a request that did **not** ask for a range causes the controlled fetch to fail with a network error;
- relaying the non-partial error response remains a resolvable fetch.

Thus:

```text
fetch resolves -> candidate false
fetch rejects  -> candidate true
```

Do not assume these exact success/failure semantics across browsers. Reproduce them on the target Chromium version.

### 5. Prefix extraction loop

Once `oracle(prefix + candidate)` is deterministic:

```text
known = initial_prefix
for each position:
    for c in charset:
        if oracle(known + c):
            known += c
            break
```

Keep the charset target-derived. Include punctuation/braces only when evidence supports them.

Checkpoint recovered prefixes externally so a bot timeout/restart does not lose progress.

---

## Full generalized chain

```text
attacker-controlled public upstream
        ↓
proxy exposes it under protected origin
        ↓
script destination causes downstream CL rewrite
        ↓
proxy still pipes upstream body
        ↓
HTTP/1.1 browser response boundary desync
        ↓
queued script request consumes smuggled JS response
        ↓
same-origin JavaScript executes
        ↓
authenticated /admin read
        ↓
recover internal API metadata/key
        ↓
open attacker-controlled Service-Worker page
        ↓
media-generated Range requests to cross-origin API
        ↓
secret prefix changes body length
        ↓
206 vs 416
        ↓
Service Worker response laundering
        ↓
resolve/reject boolean oracle
        ↓
prefix extraction
```

---

## First tests to rank highly

When the fingerprint matches, try these before generic XSS spraying:

1. **Framing audit** — search for code that changes `Content-Length`, deletes `Transfer-Encoding`, or pipes after `writeHead`.
2. **Fetch-Metadata audit** — identify whether blocking is tied only to `Sec-Fetch-Dest`, `Sec-Fetch-Mode`, or `Sec-Fetch-Site`.
3. **Connection-reuse test** — prove extra body bytes affect the next response on the same browser connection.
4. **Protected-origin content test** — confirm attacker upstream is rendered/fetched under the target origin.
5. **Range semantics test** — send satisfiable/unsatisfiable ranges to the internal endpoint and record `206`/`416` behavior.
6. **Service Worker harness** — verify cross-origin media requests hit the worker and verify which stashed response types can be replayed onto a same-origin no-cors fetch.

These tests provide much more information than trying dozens of CSP payloads.

---

## Negative knowledge / dead ends

Do not waste time on these once source proves the structural blocker:

- ordinary `<script src>` when every script-destination response is deterministically emptied;
- old inline-event CSP bypasses when `script-src` excludes `'unsafe-inline'`;
- stealing an `HttpOnly` cookie directly when authenticated same-origin fetch is enough;
- generic DNS rebinding when the proxy resolves once, validates the resulting address, and connects directly to that address;
- generic CORS payloads when the internal API intentionally rejects preflights;
- cache/timing guesses when a deterministic Range status/length oracle exists;
- classic CL.TE/TE.CL payload lists when the bug is **response-side** framing, not request parser disagreement.

---

## Implementation discipline

- Keep an attacker HTTP server script deterministic and instrumented.
- Log every callback stage: page open, smuggled execution, admin read, Service Worker ready, oracle start, recovered prefix.
- Parameterize target origin, bot endpoint, callback host, known prefix, charset, threshold, and max rounds.
- Preserve exact raw response bytes for the desync stage.
- Validate on the exact browser/HTTP version; HTTP/2 multiplexing changes the connection model substantially.
- Prefer a small self-contained browser harness over speculative manual payload tweaking.

---

## Routing / cross-reference

- If the mismatch is between **request** parsers, use `request-smuggling.md`.
- If the mismatch is a **response boundary** seen by the browser, stay here.
- If the browser primitive is a simpler timing/window/frame oracle, use `modern-xs-leaks-patterns.md`.
- If the main problem is only CSP policy analysis, use `csp-browser.md`.
- If a cache layer, rather than the browser connection, owns the poisoned association, use `cache-attacks.md`.

## Provenance

Generalized from the official SekaiCTF 2026 `EnD` challenge materials and solver after a blind V2 evaluation identified a missing browser-response-framing and Range-oracle playbook. Challenge-specific flag material, credentials, fixed hosts, fixed page names, and timing constants are intentionally excluded.