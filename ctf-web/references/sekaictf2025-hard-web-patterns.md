# SekaiCTF 2025 hard web patterns

Source: `project-sekai-ctf/sekaictf-2025` second pass, focused on 0-3 solve web challenges.

## Fancy Web — PHP object injection into WordPress POP + `php://filter` generated webshell

Observed files: `web/fancy-web/challenge/challenge-custom/fancy/fancy.php`, `web/fancy-web/solution/solve.php`, `filter_chain.py`, `solve.py`.

Pattern:
- A custom plugin accepts base64 data and calls `unserialize()`; the expected class is `SecureTableGenerator`, but the object graph can embed core WordPress classes.
- The solution builds a POP chain through:
  `SecureTableGenerator->__wakeup` -> `resetSecurityProperties` -> `in_array` string conversion -> `WP_HTML_Tag_Processor->__toString` -> `WP_Block_List->offsetGet` -> `WP_Block->__construct` -> `WP_Block_Patterns_Registry->get_content`.
- The final sink reads a `filePath`. Instead of needing an existing writable PHP file, the exploit supplies a `php://filter/.../resource=php://temp` chain generated character-by-character to synthesize PHP code.
- The synthesized code writes command output into a web-readable uploads path, then the exploit fetches it.

Recognition checklist:
1. WordPress plugin unserializes attacker data and checks only top-level class.
2. A magic method calls generic array/string helpers (`in_array`, `htmlspecialchars`, `__toString`) on attacker-controlled nested objects.
3. WordPress core classes with public-ish properties are autoloadable inside the plugin context.
4. A file-read sink exists but no direct write sink exists; try `php://filter` chain generation to make the read evaluate controlled content through a later include/load path.

Pitfall: this is not a generic ysoserial-style chain. Recreate the exact installed WordPress version/classes and trace magic methods with stack traces.

## vite — Vite/SvelteKit SSR prototype pollution through form-data hook

Observed files: `web/vite/dist/app/src/hooks.server.js`, `vite.config.js`, `solution/solve.py`.

Pattern:
- The only server hook is `export const handle = form_data` from `sk-form-data`.
- Sending form fields like `__proto__.source=...` pollutes prototypes used during server-side module rendering/response handling.
- The payload sets `Object.prototype.flag` to base64 of `process.binding('spawn_sync').spawn({ file: '/flag', ... }).output.toString()`.
- The response exposes the polluted property as a header named `flag`; the solver base64-decodes it.
- `vite.config.js` has preview `allowedHosts: ['.chals.sekai.team']`; do not stop at host restrictions if the actual vuln is in SSR request parsing.

Recognition checklist:
- SvelteKit/Vite app with a body/form parser hook and no routes of interest.
- Dependencies parse nested form keys (`a.b`, `__proto__.x`, `constructor.prototype.x`).
- SSR environment still has Node internals (`process`, `process.binding`, `spawn_sync`).
- Output may land in headers or serialized state rather than page body.

Pitfall: prototype pollution payloads often need exact field grammar from the parser library; test `__proto__.x`, `constructor.prototype.x`, nested arrays, and header/body reflection separately.

## Captivating Canvas Contraption — browser exfil via WASM GC/reference-types import abuse under CSP

Observed files: `web/captivating-canvas-contraption/challenge/www/index.html`, `adminbot.js`, `solution/index.ts`.

Pattern:
- Admin bot visits `SITE?wasm=<attacker url>` with `--noexpose_wasm,--jitless`, but the page itself enables `script-src ... 'wasm-unsafe-eval'` and instantiates attacker WASM with only harmless `env` imports.
- AssemblyScript can still declare JS builtins as imports using module/name pairs such as `@external("constructor", "groupBy")`, `Object.*`, and prototype descriptors.
- The exploit abuses `externref`, reference types, `Object.groupBy`, descriptor getters/setters, and `Object.prototype.prepareStackTrace` to recover a `window` reference from V8 callsites when `renderPixel()` throws.
- After getting `window`, it reads `document.cookie`, constructs arbitrary JS strings inside WASM, and invokes `navigator.sendBeacon` with the correct receiver by installing an accessor setter on `Object.prototype["0"]` and triggering it via `Object.assign(navigator, src)`.

Recognition checklist:
1. Admin bot loads attacker-controlled WASM on the protected origin.
2. CSP blocks normal inline/network JS but permits WASM eval/instantiation.
3. Browser supports WASM GC/reference types/externref imports.
4. The challenge exposes repeated JS-to-WASM callbacks (`renderPixel`) where thrown errors can reach `prepareStackTrace`.

Pitfalls:
- `Object.groupBy(["..."], fetch)` fails because the callback receives an integer second argument that `fetch` rejects.
- `navigator.sendBeacon` must be called with `this === navigator`; binding/receiver recovery matters.
- The `prepareStackTrace` window trick did not work from `_start` because `WebAssembly.instantiate` is promise-based; trigger from the later render callback.

## hqli-me — Hibernate query injection to H2 alias RCE, then JShell/JDI localhost pivot

Observed files: `web/hqli-me/dist/*/Main.java`, `UserAuthenticationClient.java`, `solution/e.py`.

Pattern:
- Auth service constructs HQL/JPQL strings with quoted user input: `where u.username = "%s" and u.password = "%s"` and `where s.sessionId = "%s"`.
- Order service has a `fields` selector that is validated but still inserted into HQL: `select %s from Order o ...`.
- The solve uses HQL `function('CSVWRITE', ...)` to reach H2 features and create a Java alias (`CREATE ALIAS SHELLEXEC AS ...`) that runs `ProcessBuilder` and stores output by creating a fake session/user.
- Because outbound network is disabled, the exploit first uses `jdk.jshell.execution.JdiInitiator`/`jlink --save-opts` to execute a local curl/wget against the auth service, then retrieves output through normal app APIs.

Recognition checklist:
- Java/Hibernate challenge where SQLi payloads fail but HQL supports `function(...)` escapes.
- Embedded H2 or similar DB behind Hibernate.
- No outbound network but multiple local services communicate over loopback.
- `jdk.jshell.*`, `jlink`, or JDI classes are present in the runtime; they can be abused as local execution gadgets.

Pitfall: when egress is blocked, design the payload to write results into application state or another local service, not to an external callback.

## rednote — search-result crash oracle for admin-note exfiltration

Observed files: `web/rednote/challenge/app.js`, `views/note.hbs`, `dist/bot.js`, `solution/solve.html`.

Pattern:
- The admin bot creates a private note whose title is `flag` and note body is the flag, then visits an attacker URL in the same browser context. Outbound HTTP requests are restricted, but attacker JavaScript can still open same-site windows and submit forms through a sandboxed helper frame.
- `/search?query=...` returns the first private note where either `title.includes(query)` or `note.includes(query)`. This creates a prefix-membership oracle over the flag if the attacker can distinguish “matched note rendered” from “no note found”.
- The rendered note sanitizes user HTML with DOMPurify but permits `<style>`. A tiny CSS payload using `@starting-style` plus `*::first-letter` triggered a Chrome renderer/crash/navigation state difference in the challenge browser.
- The exploit creates a note whose title is the candidate prefix and whose body is the crash CSS, opens `/search?query=<candidate>`, navigates the popup through `about:blank` and back to the search URL, then treats cross-origin/window-access behavior as the boolean signal. On a match, the matching result page includes the crash CSS; on a miss, it renders the safe error page.
- It brute-forces the flag character-by-character with alphabet reset after each accepted prefix.

Recognition checklist:
1. Admin bot leaves secret content in authenticated app state before visiting attacker content.
2. Search/filter endpoint accepts attacker-controlled probes and returns secret-containing records if a substring/prefix matches.
3. Direct response body is cross-origin/private, but attacker can induce different browser behavior for “result page” vs “error page”.
4. Sanitizer allows CSS or other non-script markup, and browser-version-specific CSS/rendering bugs can become side channels.

Pitfalls:
- This is a browser oracle, not classic XSS. CSP, HttpOnly cookies, and request blocking may all be intact.
- Reproduce the exact bot Chromium version and navigation choreography. Simplified tests can miss crash/window-state oracles.
- Keep injected CSS short; note length was capped at 128 bytes.

## Notebook Viewer — multi-origin iframe heap-size side channel

Observed files: `web/notebook-viewer/challenge/index.html`, `frame.html`, `dist/adminbot.js`, `solution/solver.html`.

Pattern:
- The admin first opens `/?note=<FLAG>`. The page renders one iframe per character, with each frame origin encoded as `https://nbv-<index>-<charCode>.chals.sekai.team/`.
- The bot uses `--host-resolver-rules=MAP nbv-*.chals.sekai.team ...`, so all candidate subdomains resolve to the service, but origins remain separated by hostname.
- `frame.html` writes `note` with `innerHTML`, so an attacker-controlled candidate iframe can execute markup such as an SVG `onload` handler on its candidate origin.
- The exploit opens candidate origins `nbv-<index>-<candidateCode>` and has their frame script post `performance.memory.usedJSHeapSize` back to the attacker page. The true origin already has an existing flag-character frame from the admin’s first page, so its heap profile is measurably higher than non-matching candidate origins.
- The solve batches several candidate frames at a time, picks the candidate with the largest heap usage above a baseline, appends it to the recovered flag, and repeats.

Recognition checklist:
1. Secret characters influence subdomain/origin names, URL paths, cache keys, or frame identities.
2. Admin keeps the secret-rendering page open while visiting attacker content.
3. Wildcard DNS/host-resolver rules make many attacker-chosen origins resolve to the same service.
4. Candidate frames can execute same-origin JS and expose a side-channel such as `performance.memory`, timing, cache warmth, process reuse, or resource count.

Pitfalls:
- This is not a DOM read of the secret page; the leak is from browser resource/process state shared with a matching origin.
- Baseline and threshold are browser-version dependent. Use repeated samples and small candidate batches to reduce noise.
- Look for the secret-to-origin mapping first; without it, `performance.memory` is only noise.
