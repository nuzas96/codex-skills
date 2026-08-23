# Empirical Web CTF Field Workflow

This reference preserves high-value session-derived web-solving heuristics that do not belong in individual vulnerability references. Load it when the challenge surface is ambiguous, responses are subtle, or a blind/async path makes ordinary payload testing unreliable.

## Measure the Backend, Not the HTML

Client-side `maxlength`, input type, JS validation, and form restrictions are hints only. Establish the real server limit with controlled requests. If a field cap matters, binary-search the length and determine whether the backend counts bytes, Unicode code points, decoded characters, or serialized length.

Check whether validation applies to only one representation (`request.form`, JSON body, query string, multipart part, etc.). Do not assume the UI's representation is the only accepted one.

## Response-Size Deltas Need a Double Baseline

Never treat a small response-length difference as a leak until it reproduces across the **same request shape**.

Procedure:

1. Send baseline A and baseline B back-to-back with identical method/headers/content type/field set.
2. Confirm their lengths/hashes are stable.
3. Change one input only.
4. Repeat the exact pair.
5. Attribute a delta only if it follows the changed field consistently.

Differences caused by multipart boundaries, extra headers, compression, rotating tokens, timestamps, or different request shapes are noise.

## Routing-Layer Fingerprinting

A reverse-proxy default site can reveal that the public vhost is only a routing layer. For Nginx Proxy Manager-like deployments, unknown `Host` values may all fall through to the same default page. Once that behavior is stable, stop brute-forcing vhost names without new evidence.

But **default proxy page != no application**. Probe a small evidence-driven set of alternate ports on the same host (commonly 8080/8443/3000/5000/8000) and compare status/body/header fingerprints. The real app may be directly exposed outside the front proxy.

## PHP LFI / Source-Disclosure Session Lessons

When a PHP app constructs a content path from `page`/`file`/`include`, distinguish the normal content branch from a fallback raw-file branch.

High-value workflow:

1. Prove LFI with a small known file.
2. Use `php://filter/convert.base64-encode/resource=<relative-file>` to disclose PHP source when the runtime/config supports it.
3. Prefer paths relative to the PHP working directory/docroot when absolute guesses fail.
4. Read Apache/PHP config or `/proc/self/*` only as needed to map layout.
5. Inspect author comments/hints, but treat conspicuously planted flag paths as possible decoys.
6. If a named path fails, test a **small semantic sibling set** (`admin/`, `private/`, `internal/`, `secret/`) before broad fuzzing when challenge wording strongly suggests a deliberate misdirection.

When extracting base64 from HTML, identify the actual DOM container used by the response branch and choose the longest credible base64 blob. A parser that extracts the first base64-looking token can silently decode page noise instead of the file.

## Blind Challenge: Input Renderer vs Output-Side Processor

A public form with no reflection can feed very different sinks.

### Input-rendering sink

An admin/reviewer/browser later renders the submitted fields. Test harmless HTML/network canaries and route to browser/admin-bot references.

### Output-side processor

A program consumes what the application **produces**: email body, log line, webhook message, Slack/Discord unfurler, SIEM URL extractor, mail DNS/MX lookup, etc. In this case script tags are the wrong payload class. Use URL/domain markers in the output-relevant fields/headers instead.

Author hints like "reviewer/admin sees it" favor renderer; explicit denial of XSS/browser rendering should prune that branch immediately.

If a hint ambiguously endorses one of two interpretations, keep both branches alive until evidence distinguishes them. Do not lock in based on intuition alone.

Useful output-side probes include:

- unique subdomain in an email-domain field to observe DNS/MX behavior;
- full `https://<marker>.<owned-domain>/` URL in text fields;
- URL markers in `Referer`, `User-Agent`, query/path or other fields likely to enter logs;
- one unique marker per field/endpoint so callbacks are attributable.

## Async / Load-Shedded Blind SSTI

Some challenge workers render templates asynchronously, so public response time is normally flat while only a subset of jobs are processed. One failed timing probe does not rule out SSTI.

Recognition:

- most identical requests return fast;
- occasional identical requests are significantly slower;
- challenge hint indicates blind/timing/template behavior;
- worker may impose a fixed execution cap.

Testing rule:

1. replay the **same** delay payload multiple times;
2. examine maximum/outlier latency as well as median;
3. use a delay longer than a plausible worker cap to reveal capped executions;
4. compare against repeated control requests under the same load;
5. only infer SSTI when slow events correlate with the payload across enough trials.

Do not immediately convert this into large blind extraction; first prove the worker model and success predicate.

## Blind Callback Discipline

Before submitting to the target, self-test the owned callback endpoint and ensure it records complete path/query plus timestamps. Use compact, unique markers. Record the exact submitted payload in `PROGRESS.md` so a delayed callback can be mapped back to its source.

If no callback arrives, distinguish:

- wrong primitive;
- processing delay/batch schedule;
- worker sampling/load shedding;
- outbound DNS-only vs HTTP behavior;
- action/approval step not yet triggered;
- callback infrastructure failure.

## General Rule

A five-second empirical test is often more valuable than many turns of speculation once a hypothesis is concrete. After 2-3 rounds of reasoning about the same browser/parser/worker behavior, build the smallest safe harness and test it.

## Provenance

Consolidated from the original user-specific `web-ctf` workflow and session-derived CTF field notes. The complete original remains on `archive/pre-restructure-20260823`.
