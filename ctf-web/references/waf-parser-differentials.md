# WAF and Parser Differential Bypass

Use only after a vulnerability/primitive is confirmed and an intermediary filter blocks the known-good request. In CTFs the useful question is usually not "which obfuscation list bypasses this WAF?" but **which representation does the WAF inspect versus which representation reaches the backend parser?**

## Workflow

```text
confirmed backend primitive
  -> record blocked request and block signature
  -> identify proxy/WAF/backend chain
  -> change ONE representation dimension
  -> compare WAF result and backend semantics
  -> derive parser mismatch
```

Keep a clean baseline and a unique success oracle. A different status code or block page is not proof that the backend received equivalent semantics.

## Representation Dimensions

High-value mismatch classes:

- decoding count: raw vs URL-decoded vs double-decoded;
- parameter duplication/order (HTTP parameter pollution);
- query vs form vs JSON vs multipart vs XML;
- HTTP method or method override;
- header vs body location;
- path normalization and slash handling;
- transfer framing / proxy parsing;
- case/whitespace/comment handling in the backend language;
- Unicode or charset conversion when the backend genuinely decodes it differently.

Test transformations that the **backend parser accepts**, not generic payload decoration.

## Injection-Specific Notes

### SQL

If SQL injection is already confirmed, comments, whitespace alternatives, equivalent operators, JSON/body relocation, or duplicate-parameter semantics may matter. SQLMap tamper scripts are useful after you understand the block and DB syntax; random stacks of tamper scripts create noise and can destroy the oracle.

### XSS

The goal is a browser-equivalent sink, not a different-looking string. Determine HTML context, sanitizer, browser parser, CSP, and event/script constraints before trying alternate tags/encodings. Route browser constraints to `csp-browser.md` and XS-Leak/bot refs.

### Path / SSRF / Other Parsers

Prefer parser-normalization mismatches described by the corresponding focused reference. WAF bypass is a transport/representation layer around the real primitive.

## HTTP-Level Mismatches

If front-end and back-end disagree about request boundaries, transfer encoding, H2 downgrade, or headers, this may become request smuggling rather than ordinary WAF evasion. Route to `request-smuggling.md`.

## Fingerprinting

Headers/block pages can identify Cloudflare/Akamai/ModSecurity/etc., but product identity alone does not tell you the deployed ruleset. Build bypasses from observed behavior.

Useful measurement:

- response status/body hash/length;
- response headers;
- backend side effect;
- timing only when stable;
- server logs/local reproduction when challenge source is available.

## Common Failure Modes

- Starting with huge WAF payload lists before proving a vulnerability.
- Assuming mixed case or double encoding remains meaningful after modern normalization.
- Declaring success because the WAF stopped returning 403 while the backend primitive also stopped working.
- Combining five transformations at once, making the responsible mismatch unknowable.
- Treating a WAF product name as a rule-version fingerprint.

## Provenance

Consolidated from the original `performing-web-application-firewall-bypass` Apache-2.0 skill and existing CTF parser-mismatch notes. Original source is preserved on `archive/pre-restructure-20260823`.
