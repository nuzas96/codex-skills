# Web hard-pattern playbook

Use this when a web CTF looks empty/simple but has hard-challenge signals: custom plugin, SSR hook, admin bot, CSP/WASM, Hibernate/H2, or no obvious route vuln. Built from SekaiCTF 2025 zero/near-zero patterns, but written as reusable triage.

## 0. Fast routing

Ask these before fuzzing randomly:

1. Is attacker data parsed into objects/classes? -> WordPress/PHP POP, Java deserialization, template objects.
2. Is a parser hook installed before routes? -> SvelteKit/Vite/Express body parser prototype pollution.
3. Does admin bot load attacker JS/WASM on target origin? -> browser object recovery/exfil under CSP.
4. Is ORM/Hibernate used? -> HQL injection, not just SQL injection.
5. Is egress blocked? -> exfil through app state/local services, not webhook.
6. Does the secret affect search hits, frame origins, URLs, or caches? -> browser side-channel/oracle instead of direct XSS.

## 1. WordPress/PHP unserialize POP checklist

Trigger signs:
- Plugin accepts base64/JSON/POST blob and calls `unserialize()`.
- Code checks only `instanceof` or top-level class name.
- WordPress core classes are autoloadable.
- Magic methods call string/array helpers: `__wakeup`, `__destruct`, `__toString`, `ArrayAccess::offsetGet`, `Iterator`, `in_array`, `htmlspecialchars`, `preg_replace_callback`.

Workflow:
1. Locate exact unserialize site and all post-unserialize method calls.
2. Confirm class autoload scope: installed WP version, plugin includes, composer autoload.
3. Build a call graph from the first magic method to sinks:
   - file read/include: `file_get_contents`, `include`, `require`, template loading
   - write: uploads, cache, logs, transients
   - callback/code: `call_user_func`, `preg_replace /e`, hooks/actions
4. Search public core classes for controllable properties that implement `__toString`, `ArrayAccess`, iterators, or registry lookups.
5. Serialize a minimal object graph and test locally with error reporting enabled.
6. Only after one sink triggers, wrap in the remote transport/base64 format.

Payload construction notes:
- If sink is file-read only, try PHP wrappers: `php://filter`, `data://`, `phar://`, `zip://`, `glob://`, `php://temp`.
- `php://filter` can synthesize payload bytes through chained conversions when direct write/upload is unavailable.
- Preserve exact property visibility mangling for private/protected PHP properties.
- Watch for `__wakeup` resetting properties; place controlled objects in properties consumed after reset.

Minimal local harness:
```php
<?php
error_reporting(E_ALL);
require_once 'wp-load.php';
$payload = base64_decode($argv[1]);
var_dump(unserialize($payload));
```

Stop conditions:
- If no autoloaded class chain reaches a sink, pivot to plugin-specific classes and hooks.
- If wrapper is blocked by `allow_url_include` or filters, try turning read into leak rather than RCE.

## 2. `php://filter` generated-payload workflow

Use when you have a file read/include-ish sink but no writable PHP file.

Checklist:
1. Confirm the sink accepts wrapper URLs unchanged.
2. Test `php://filter/convert.base64-encode/resource=/etc/passwd` to verify wrapper execution.
3. If the sink output is interpreted later as PHP/HTML, generate controlled bytes using filter chains.
4. Prefer short payloads that write output to a known web-readable location:
   - `<?php system($_GET[0]); ?>`
   - `<?php file_put_contents('/tmp/x',shell_exec($_GET[0])); ?>`
5. If command output cannot return directly, write into uploads/cache or app state and fetch it separately.

Pitfalls:
- Filter chains are PHP-version and extension dependent. Test inside the challenge container.
- Some wrappers work for read but not include. Verify the exact sink semantics.
- Long chains may hit URL length limits; use a staged payload.

## 3. SvelteKit/Vite SSR prototype-pollution matrix

Trigger signs:
- `hooks.server.js` imports a generic body/form parser.
- Routes look empty but SSR still processes all requests.
- Dependency parses nested field names (`a.b`, `a[b]`, arrays).
- Response headers or serialized state reflect object properties.

Probe matrix:
```bash
# form-urlencoded
curl -i -X POST "$URL" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data '__proto__.pp_test=YES'

curl -i -X POST "$URL" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data 'constructor.prototype.pp_test=YES'

# multipart
curl -i -X POST "$URL" \
  -F '__proto__.pp_test=YES'

# JSON, if accepted
curl -i -X POST "$URL" \
  -H 'Content-Type: application/json' \
  --data '{"__proto__":{"pp_test":"YES"}}'
```

Where to look for proof:
- New response headers.
- SSR error stack traces.
- HTML serialized data: `__data.json`, SvelteKit payload, route data.
- Behavior changes in redirects/status codes.

Escalation ideas:
- Pollute properties consumed by framework response building: `status`, `headers`, `body`, `flag`, `source`, `transform`, `toString`.
- In Node SSR, test if `process`, `process.binding`, `child_process`, or dynamic import can be reached through polluted fields.
- If output lands in a header, base64-encode command output to avoid header-breaking bytes.

Pitfalls:
- `allowedHosts`/Vite preview restrictions are often a distraction; exploit the actual request parser.
- Different parsers use different nesting grammar. Try dot, bracket, and array forms.
- Prototype pollution might be one-request only if the server forks/reloads; send exploit and read output in same request where possible.

## 4. WASM/admin-bot under CSP checklist

Trigger signs:
- Admin bot visits target origin with attacker-controlled WASM or module URL.
- CSP blocks normal JS but allows `wasm-unsafe-eval` or WASM instantiation.
- Browser flags disable classic JIT/WASM exposure but page still instantiates WASM internally.
- Imports look harmless (`env.renderPixel`) but WASM can declare arbitrary JS builtins as imports.

Triage workflow:
1. Read bot flags and CSP exactly.
2. Confirm attacker WASM executes on protected origin with a visible side effect.
3. Enumerate allowed imports/modules and whether `externref`/reference types are supported.
4. Try importing JS builtins via module/name pairs: `Object`, `constructor`, `Reflect`, `Array`, prototype descriptors.
5. Seek a JS object reference primitive:
   - thrown exception -> `Error.prepareStackTrace` / callsites
   - descriptor getter/setter side effects
   - `Object.groupBy`, `Object.assign`, `Object.getOwnPropertyDescriptor`
6. Once any object reference is recovered, target `window`, `document.cookie`, `navigator.sendBeacon`, `fetch`, or image beacons.

Receiver-sensitive API rule:
- Some browser APIs require the correct `this` value. `navigator.sendBeacon.call(navigator, url, data)` works; detached `sendBeacon(url,data)` may fail.
- If WASM cannot call with a receiver directly, install a getter/setter on a prototype and trigger assignment/copy with the desired receiver.

Pitfalls:
- Promise-based `_start` timing may not have useful stack frames; trigger from later page callbacks.
- `fetch`/`sendBeacon` may reject wrong argument types; convert WASM strings carefully.
- Test in the exact bot browser; WASM GC/reference-types behavior changes between Chrome versions.

## 5. Hibernate/H2/JShell local-pivot checklist

Trigger signs:
- Java service builds HQL/JPQL strings with `%s` or concatenation.
- SQL payloads fail but error messages mention Hibernate/HQL.
- H2 database is embedded or reachable behind Hibernate.
- Egress is blocked but multiple local services exist.

HQL-specific probes:
```text
" or 1=1 or "a"="a
') or 1=1 or ('a'='a
function('database', '')
function('CSVWRITE','/tmp/probe','select 1')
```

Escalation path:
1. Confirm injection context: string literal, identifier list, field selector, `where`, `order by`.
2. Check if HQL `function(...)` can invoke database-native functions.
3. For H2, attempt file write/read primitives first (`CSVWRITE`, `CSVREAD`) before RCE.
4. If alias creation is possible, create a Java alias that runs a command or writes output into DB/app state.
5. If outbound network is blocked, pivot locally:
   - write output into an existing table/session/user field,
   - call another loopback service with `curl/wget`,
   - use `jdk.jshell`/JDI/jlink tricks if shell execution is constrained.

Pitfalls:
- ORM query language != SQL. Payload syntax and escaping differ.
- Egress blockers make reverse shells misleading; prefer output-in-app-state.
- H2 versions differ; test alias syntax and function availability locally.

## 6. Browser oracle / side-channel checklist

Use this when an admin bot clearly has the secret, but direct XSS/cookie theft is blocked by CSP, HttpOnly cookies, sandboxing, or request interception.

Trigger signs:
- The admin creates or views secret content before visiting attacker content.
- A search/filter endpoint can be queried with guessed prefixes/substrings.
- The secret changes URLs, subdomains, iframe origins, cache keys, rendered resources, or process state.
- Sanitized markup still allows CSS/SVG/HTML that can cause measurable browser differences.

Oracle workflow:
1. Identify a boolean predicate over the secret: `record matches query`, `origin exists`, `resource cached`, `frame already loaded`, `CSS/rendering path hit`.
2. Find any observable difference available cross-origin:
   - popup/window access exception vs no exception,
   - crash/hang/navigation timing,
   - `performance.memory.usedJSHeapSize`, resource counts, cache warmth,
   - load/error events, history length, focus/close behavior.
3. Build a local harness with the same bot flags and browser version. Browser-version-specific CSS and process-state oracles are fragile.
4. Brute-force in small batches with baseline calibration; reset alphabet/order after every confirmed prefix.
5. Exfil progress through same-origin beacons, URL paths, or server logs if direct external requests are blocked.

Pitfalls:
- Do not require reading the private page. Many hard bot solves only need to distinguish “candidate caused special browser state”.
- Reproduce the exact navigation choreography: popup reuse, `about:blank`, hash reloads, iframe batching, and opener relationships can be the primitive.
- Treat sanitizer-allowed CSS as active attack surface; “no script” is not “no side channel”.

## 7. Reporting template for future solves

When a hard web path works, record:
- Entry parser/sink and exact version.
- First primitive proof: leak/header/write/object reference.
- Chain step that converts primitive into flag access.
- Browser/runtime version if client-side.
- One failed tempting path, to avoid repeating it later.
