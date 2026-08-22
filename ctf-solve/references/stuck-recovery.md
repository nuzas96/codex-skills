# Stuck-Recovery Gate

Use this reference **before** declaring a CTF challenge blocked, unsolvable, exhausted or impossible.

The purpose is not blind persistence. It is to distinguish:

- wrong payload variation;
- exhausted primitive class;
- wrong attack class;
- missed source/endpoint/path;
- stale version assumptions;
- challenge-infrastructure behavior;
- a genuinely exhausted solve.

## Seven-point enumeration

Walk all seven points and record each result in `PROGRESS.md`.

### 1. Source audit completeness

Verify that all supplied source/artifacts relevant to execution were actually inspected, not only the obvious files.

Check:

- route/controller/handler registration;
- middleware/decorators/auth wrappers;
- templates and error pages;
- static JS/CSS/SVG/HTML;
- config, Dockerfile/compose, dependency manifests;
- bot/browser runner;
- backups/test fixtures/debug files;
- client code that transforms inputs before requests.

A missed secondary parser or error renderer can be the intended path.

### 2. Endpoint / protocol surface completeness

Enumerate the actual surface, including behaviors that may differ from the happy path:

- undocumented routes;
- trailing slash/case/path normalization differences;
- alternate HTTP methods where relevant;
- HEAD/OPTIONS semantics;
- nested GraphQL/API resolvers;
- secondary ports/services;
- redirects/proxy paths;
- parser differences between front and back ends.

Do not fuzz blindly; enumerate based on the framework/source/protocol.

### 3. Library/CVE/advisory freshness

For version-dependent primitives, verify current information for the **exact relevant version range**.

Check official advisories, changelogs, security issues and CVE/GHSA data for libraries/browser/runtime involved. Old writeups establish patterns, not current exploitability.

Re-check freshness when the CTF or deployed image is newer than the notes you are relying on.

### 4. Exact target-version verification

A primitive tested on another browser/libc/kernel/library version is not conclusively dead on the target.

Capture exact target facts when possible:

- browser/user agent and build;
- package lock / requirements versions;
- libc/loader;
- kernel;
- language/runtime;
- container image/toolchain.

Then run the smallest exact-version reproduction possible.

### 5. Hint / challenge-design interpretation

Interpret hints at multiple layers:

- literal wording;
- implied primitive;
- implied architecture/trust boundary;
- what hypothesis the hint makes less likely;
- what step the challenge author expects a solver to notice.

A hint about reaching a renderer, resolver or parser may be telling you **which boundary** matters rather than naming the exploit directly.

### 6. CTF infrastructure paths

Check whether deployment introduces behavior absent from standalone source:

- reverse proxy / forwarded headers;
- same-host proxy and loopback checks;
- container/service topology;
- internal bot/devtools/debug service;
- per-team instance differences;
- platform-generated routes/secrets;
- alternate ports/hosts;
- load balancing/cache normalization.

Never assume `source says X` means `deployed topology behaves exactly like X`.

### 7. Communication / final assessment

After points 1–6, classify the state precisely:

- `new path found` -> test it;
- `primitive class exhausted` -> switch class;
- `needs missing artifact/version/credential supplied by challenge` -> state exactly what is missing;
- `deployment appears inconsistent/broken` -> show evidence;
- `reasonable paths genuinely exhausted` -> provide a concise handoff with the exact blocker and strongest remaining hypothesis.

Do not ask the user vague questions that could have been answered through available evidence. Ask only a specific missing piece if necessary.

## Anti-patterns

### Payload-variant loop

Trying ten syntactic variants of the same blocked primitive is not ten paths. After a few controlled variants prove the class is blocked, switch primitive class.

### Tiny-tweak optimism

A different XSS tag, encoding spelling or heap size is not a new strategy unless it changes the parser/state boundary responsible for the failure.

### Stale empirical ceiling

`Failed three weeks ago` is not a target-version result. Revalidate if target software changed or the previous result came from a different build.

### Premature broken-challenge claim

Other solves, intended hints or a known working deployment are evidence that a missing path may exist. Do not call the challenge broken without deployment-specific evidence.

## Compact report format

Record this in progress when the gate is exhausted:

```text
1. Source audit: ...
2. Endpoint/protocol enumeration: ...
3. CVE/advisory freshness: ...
4. Exact-version verification: ...
5. Hint/design interpretation: ...
6. CTF infrastructure paths: ...
7. Assessment: ...

Specific blocker: ...
Strongest next path / missing evidence: ...
```

## Historical source

This preserves the V1 `ctf-stuck-recovery` mechanism in a focused reference. The original full skill remains frozen at `archive/pre-restructure-20260823`.