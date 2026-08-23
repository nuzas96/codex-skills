# Web Cache Poisoning and Cache Deception

Use when a CDN/reverse proxy/cache sits in front of the application and the flag path may depend on cache-key disagreement, unkeyed inputs, or private content being cached as public.

## Establish Cache Behavior First

Record `Age`, `X-Cache`, `CF-Cache-Status`, `Via`, `Vary`, `Cache-Control`, and repeated-request behavior. Use a unique cache buster until you understand the key; do not poison a shared key during reconnaissance.

Questions:

1. Is the response actually cached?
2. What request components are keyed?
3. Which components alter the origin response but are not keyed?
4. Does authentication/session state bypass or vary the cache?
5. How are path/query components normalized by cache vs origin?

## Cache Poisoning

Core primitive:

```text
attacker-controlled input affects origin response
        +
that input is absent/normalized differently in cache key
        =
shared poisoned representation
```

Common candidates include forwarded host/proto headers, override headers, unusual query parameters, duplicate parameters, host/port differences, fat GET bodies, and cache/origin parser discrepancies.

Do not blindly test every header. Source/proxy config or Param Miner-style discovery can narrow the search.

## Safe CTF Workflow

1. Choose unique cache-busting key.
2. Send baseline twice; prove MISS -> HIT or equivalent.
3. Add one candidate unkeyed input.
4. Verify the origin response changes.
5. Request the same cache key **without** the candidate input and see whether the change persists.
6. Only remove the cache buster when the challenge requires affecting a shared/admin request and scope permits it.

## Cache Deception

This is a different primitive: private/dynamic content is stored under a URL the cache believes is static/cacheable.

Typical mismatch:

```text
cache sees: /account/profile/x.css   -> static/cacheable
origin sees: /account/profile        -> dynamic/private
```

Test path suffixes, delimiters, encoded separators, extension rules, and normalization only when cache and app routing behavior suggest a mismatch.

## Cache Key Normalization

Compare:

- query parameter inclusion/exclusion/order;
- duplicate parameter policy;
- URL decoding;
- path dot-segment/slash normalization;
- case and port handling;
- Host vs forwarded host;
- `Vary` behavior;
- cookies/auth headers;
- method/body handling.

The exploitable bug is often the disagreement between two parsers rather than "bad caching" alone.

## Cache + XSS / Redirect / Host Injection

If an unkeyed value reaches an HTML/JS/location sink, prove the sink independently first. Then determine whether the resulting response becomes shared. Route browser execution constraints to `csp-browser.md`.

## Common Failure Modes

- Treating one `X-Cache: HIT` as proof of the key composition.
- Poisoning a non-isolated shared URL during discovery.
- Confusing cache poisoning with cache deception.
- Not checking whether authenticated responses are excluded from caching.
- Assuming all query parameters are keyed equally.
- Measuring only response status instead of persistence across a second request.

## Provenance

Consolidated from the original `performing-web-cache-poisoning-attack` Apache-2.0 skill and `ctf-web/client-side.md` cache notes. Original source remains frozen on `archive/pre-restructure-20260823`.
