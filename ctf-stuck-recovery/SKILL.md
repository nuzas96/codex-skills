---
name: ctf-stuck-recovery
description: Use when you've hit a wall on a CTF challenge and are tempted to declare "blocked" or "can't solve this". The user has repeatedly pushed back on premature defeat. This skill installs a structured pre-defeat checklist that forces enumeration of all remaining paths BEFORE reporting blocked. Load it the moment you find yourself writing "I'm stuck" / "this is unsolvable" / "I can't solve this" / "empirical ceiling has been hit" — apply the 7-point enumeration checklist before deciding to give up.
---

# CTF Stuck-Recovery Protocol

The user has corrected the agent multiple times for declaring a challenge "blocked" too early. Their feedback pattern:

- "kalau org lain bleh kenape kau takleh" — others can solve it, so the technique exists
- "try harrder all path" — exhaust all paths, not just the obvious ones
- "if stuck mybe kau salah path ataupun tetinggal something" — wrong path OR missing something specific

The failure mode: agent does source analysis, finds 2-3 candidate exploits, tests them, gets blocked by Chrome version / library patch / CSP / auth gate, and writes a defeat summary. The user knows the challenge has solves (it's a public CTF, often with public writeups) and pushes back.

The fix is NOT "try harder" as a vague feeling. It's a structured enumeration that catches the paths the agent didn't think to try. Apply this BEFORE writing any defeat summary.

## When to apply this skill

The moment you catch yourself writing any of:
- "I'm stuck"
- "this is unsolvable"
- "I can't solve this"
- "the intended XSS chain is blocked"
- "the empirical ceiling has been hit"
- "all known techniques are exhausted"
- "no documented mXSS / bypass / primitive works"

If the user is asking for a fresh attempt on a challenge the agent previously failed: load this skill FIRST, before any code or attack chain planning.

## The 7-point enumeration checklist

Before declaring blocked, walk through ALL 7 points. Don't skip any. Document each as either "verified dead" or "untried, here's what would happen".

### 1. Source-code audit completeness

Have you actually read EVERY file in the source archive, or just the "key" endpoints?

**Check:**
- All route handlers (not just `/api/tickets/<id>` and `/status`)
- All template files (look for HTML injection in error pages, 404s, static files)
- All static assets (`.js`, `.css`, `.svg`, `.html`) — sometimes the static folder contains a misconfigured admin page or test fixture
- All `__init__.py` / `app.py` / factory files — check the CSP middleware, the auth decorators, the route registration order
- The bot runner — look at HOW the bot launches, not just what URL it visits

**Common misses:**
- The `/login` GET form contains a CSRF token or hidden field you didn't notice
- The error template (404, 500, abort 400) reflects user input you didn't see
- The CSP middleware has a path-based exception (e.g., `/api/*` skips the strict CSP)
- The static folder has a `.bak` or `.swp` file with extra endpoints

### 2. Endpoint enumeration completeness

Did you enumerate EVERY route, including HEAD/OPTIONS/PATCH/DELETE behaviors?

**Check:**
- Run `flask routes` or equivalent — does the app have undocumented endpoints?
- For each endpoint, what does HEAD do? OPTIONS?
- What happens with weird HTTP methods (`PROPFIND`, `REPORT`)?
- What about trailing slashes (`/api/tickets/<id>/` vs `/api/tickets/<id>`)?
- What about case-sensitivity (`/API/tickets` vs `/api/tickets`)?
- What about path-prefix matching (`/api/tickets` matches `/api/tickets-extra`)?

### 3. CVE / advisory freshness for the libraries involved

Have you checked for advisories published in the LAST 6 MONTHS for every library in the stack?

**Check:**
- DOMPurify: search `cure53/DOMPurify` issues sorted by recent
- Flask / Werkzeug: CVE feeds, especially for the Werkzeug version in `requirements.txt`
- PyJWT: signing algorithm confusion, kid injection
- SQLite: any known parser CVEs
- Browser engines: `crbug.com` for the EXACT bot version (e.g., "HeadlessChrome 149.0.0.0")

**Where to look:**
- GitHub Security Advisories (`https://github.com/advisories?query=...`)
- The library's GitHub issues filtered by `is:issue is:closed label:security`
- The library's CHANGELOG for the exact version range
- nvd.nist.gov for CVEs in the version range

**Pattern:** DOMPurify 3.3.1 was released early 2025. If the challenge is mid-2026, there's potentially 12+ months of CVEs between the bundle and the solve date. The prior session's findings may be stale.

### 4. Primitive verification on the EXACT bot/browser version

If the technique was "tested and failed" on a different Chrome version, that's not the same as tested on the bot's Chrome.

**Always check:**
- `chromium --version` inside the bot container (if accessible)
- Bot UA from prior probe (e.g., `HeadlessChrome/149.0.0.0`)
- The `Dockerfile` from the challenge source — pinned chromium version

**Why this matters:** a primitive that works on Chrome 142 (your local dev box) may fail on Chrome 149 (the deployed bot). And vice versa. The empirical ceiling moves between versions.

**Re-verify:** if your "this doesn't work" evidence is from a different version, that's NOT a confirmed blocker for the bot. Treat it as "untested on target version".

### 5. Author hint interpretation depth

When the author gives a hint ("the missing piece is X"), interpret it at multiple levels of depth.

**For each hint, ask:**
- What are the LITERAL interpretations? (the words as written)
- What are the IMPLICIT interpretations? (what the author might mean by this phrasing)
- What does it IMPLY about the challenge design? (what would the author need to have done for this hint to be correct?)
- Does the hint eliminate any of your current hypotheses?

**Pattern for "(b) reach the API as rendered HTML":**
- Literal: make the browser navigate to /api/tickets/<id> and render the response
- Implicit: maybe via a path the browser ALREADY uses for that endpoint
- Design implication: the author expected a specific way to make this happen that the solver would discover
- Hypothesis elimination: the author wouldn't hint at DOMPurify (a) if the answer required DOMPurify bypass; they'd hint at the rendered HTML path specifically because that's the chain primitive

### 6. CTF-infrastructure-specific paths

Public CTF challenges often run on infra (CTFd, dynamic flag containers, NGINX reverse proxies, containerized bots) that introduces vectors the standalone code doesn't show.

**Check:**
- Is there a reverse proxy in front of the Flask app? (`X-Forwarded-For` header, `Forwarded` header)
- Does the proxy expose other internal services?
- Does the challenge's bot container have other processes (chromedriver, devtools) that might be reachable?
- Is there a per-team instance separation that means "admin" in the codebase might map to "any logged-in user" in practice?
- Are there challenge-specific debug endpoints (`/debug`, `/_debug`, `/admin`)?

**Specifically for the Deskmesh challenge**, the prior session identified: "Local host-network plus TCP-proxy testing confirmed the actual exploitable bug: when Deskmesh is exposed through a same-host proxy, `/escalate` becomes reachable to any logged-in user because Flask sees the proxy hop as loopback." If the live instance uses a proxy, this applies even if direct loopback doesn't.

### 7. Communication paths with the user

If after points 1-6 you've genuinely exhausted all reasonable paths, the correct action is to ASK THE USER, not to declare defeat.

**Phrasing for asking:**
- "I've checked X, Y, Z — what about W?"
- "The author hinted at (b). I tried A, B, C within that hint. Have I missed a sub-path?"
- "My empirical ceiling is at [specific primitive]. Is there a more recent technique you know about?"
- "Other solvers used [technique] — is that within my skill set or do I need new tools?"

**Don't:**
- Declare defeat without enumerating first
- Ask open-ended "what should I do" questions — give the user specific options
- Imply the challenge is broken — imply you haven't found the right path yet

## What this skill is NOT

- It's NOT "always keep trying" — there ARE challenges that are unsolvable on the deployed infra, and recognizing that is also a skill.
- It's NOT "never give up" — some hours of work are better spent on a different challenge.
- It's NOT a substitute for actual skill — knowing the techniques matters; this just makes sure you don't SKIP techniques you don't know about.

## How to use it

When you find yourself typing any of the "I'm stuck" phrases:
1. STOP. Do not write the defeat summary.
2. Open the 7-point checklist above.
3. For each point, write a 1-2 sentence finding ("Checked: X. Result: Y").
4. After completing all 7 points, make an honest assessment.
5. Update PROGRESS.md with the checklist results AND the assessment.
6. THEN write the text reply — either asking the user a specific question or reporting the actual final state.

## Anti-patterns to avoid

- **"I'll just try one more thing" loops** — if you've tried the same primitive 3+ times with variations, that's the wrong primitive. Switch CLASS of primitive.
- **"Maybe if I tweak the payload a tiny bit"** — payload variations within the same primitive class are not the same as trying different primitives. If `<svg/onload=X>` doesn't work, `<svg><animate onbegin=X>` is still the SAME CLASS.
- **"The empirical ceiling has been hit" without re-verifying the bot version** — the ceiling is version-specific. Chrome 150 may have introduced new behavior.
- **"I tested this 3 weeks ago, it still doesn't work"** — without re-testing on the live bot right now, you don't know. The library may have been updated, the bot config may have changed.

## Output format for "exhausted the checklist" report

When you've genuinely exhausted all 7 points and want to ask the user, format the report as:

```
1. Source code audit: [verified: read all X files; checked: Y, Z]
2. Endpoint enumeration: [verified: ran flask routes; checked: HEAD, OPTIONS, weird methods]
3. CVE / advisory freshness: [checked: lib X issues, Y releases; finding: Z]
4. Primitive verification: [tested: A, B, C; on version: D; result: E]
5. Author hint interpretation: [hint: (b); interpreted as: ...; tried: ...]
6. CTF infra paths: [checked: X-Forwarded-For, proxy, debug endpoints]
7. Communication: ask user specific question X

Specific blocker: [the exact primitive that's failing]
Question: [what to ask user]
```

This format helps the user give you a USEFUL answer instead of a vague "try harder".

## Related skills

- `progress-discipline` — handles continuous PROGRESS.md updates
- `ctf-desktop-workspace` — handles workspace setup
- `solve-challenge` — handles individual challenge solving methodology
- `ctf-{web,pwn,crypto,...}` — domain-specific techniques
