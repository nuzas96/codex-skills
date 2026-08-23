# CSP, Browser Constraints, and Scriptless Exfiltration

Use after you have a browser-controlled primitive (XSS, HTML injection, DOM clobbering, admin bot visit, or scriptless injection) and Content Security Policy or browser behavior limits the next step.

## Start by Parsing the Real Policy

Record every enforced header and meta policy. Distinguish `Content-Security-Policy` from report-only policy. Map at least:

- `default-src`
- `script-src` / `script-src-elem`
- `style-src`
- `img-src`
- `connect-src`
- `frame-src` / `child-src`
- `object-src`
- `base-uri`
- `form-action`
- nonce/hash/`strict-dynamic` usage

Do not say "CSP blocks XSS" generically. State exactly which directive blocks which action.

## Decision Tree

```text
HTML/script primitive exists
  -> is CSP enforced?
  -> direct inline/external execution allowed?
  -> nonce/hash reusable or attacker-influenced?
  -> whitelisted origin contains executable gadget/JSONP?
  -> base/form/object/frame/connect/img/style path usable?
  -> if script impossible, is scriptless exfil enough?
```

## Unsafe Directives

`'unsafe-inline'` or broad script origins may immediately widen execution, but CSP3 nonce/hash behavior can change how `'unsafe-inline'` is interpreted. Test in the exact browser/version instead of relying on old CSP folklore.

`'unsafe-eval'` matters only if you already have a reachable gadget that calls eval-like functionality.

## Nonces / Hashes

Check whether nonces:

- repeat across responses;
- are reflected into attacker-readable markup;
- can be copied into an injected element;
- are used with `strict-dynamic`;
- are assigned by script gadgets you can influence.

Do not assume CSS can read a nonce: browsers may hide nonce content from selectors/DOM in ways that changed over time. Verify empirically.

## Whitelisted Origins / Gadgets

A trusted CDN/domain is useful only if it exposes an actual execution gadget compatible with the policy and current browser. JSONP, old AngularJS gadgets, libraries with script-creating APIs, and attacker-controlled paths on trusted origins are possible classes, not guaranteed bypasses.

Verify the exact response content type, callback behavior, redirects, SRI, and browser execution.

## `base-uri`, `form-action`, and Non-Script Paths

If markup injection is available:

- missing `base-uri` may affect relative URLs;
- missing `form-action` may permit form exfiltration;
- permissive `img-src`, `style-src`, `connect-src`, or `frame-src` may provide side channels;
- CSS selectors can sometimes leak attacker-observable state without JS.

The flag path may require data exfiltration, not arbitrary script execution.

## Admin Bot Reality Check

For bot challenges, use the repository's empirical references:

- `modern-xs-leaks-patterns.md`
- `dompurify-3.3.1-mxss-verification.md`
- relevant `bot-*.md` notes

Re-test old primitives on the bot's **exact Chrome/browser version**. Browser security behavior, parser quirks, SameSite, PNA, COOP/CORP, cache partitioning, and sanitizer interactions become stale quickly.

## Scriptless / XS-Leak Escalation

If CSP prevents script but allows navigation, resources, CSS, forms, frames, or timing oracles, pivot from "get XSS" to "extract one bit / trigger one authenticated action". Build a deterministic oracle first, then automate extraction.

## Common Failure Modes

- Reading only `script-src` and ignoring fallback directives.
- Treating report-only CSP as enforced.
- Copying a JSONP/Angular bypass from an old writeup without testing the current endpoint/browser.
- Assuming a nonce leak technique still works in current Chrome.
- Ignoring scriptless exfil when the challenge only needs a secret, not code execution.

## Provenance

Consolidated from the original `performing-content-security-policy-bypass` Apache-2.0 skill plus `ctf-web/client-side-advanced.md` and current empirical bot/XS-Leak references. Original source is preserved on `archive/pre-restructure-20260823`.
