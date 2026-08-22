# Token-Efficient CLI Workflows

Use compact, filtered output first and expand only when missing detail changes the next decision.

## Decision rule

Use structured agent/file/search tools when they already return targeted output. For terminal-heavy paths, narrow the command or use a compact wrapper such as RTK when it is installed and configured.

Good candidates for compacting:

- `git status`, `diff`, `log`, `show`;
- test/build summaries;
- broad directory/find/grep output;
- Docker/Kubernetes listings;
- first-pass CTF recon.

Keep raw/narrow evidence when exact bytes, offsets, error text, stack traces or exploit responses matter.

Examples:

```bash
# compact first
rg -n "flag|secret|admin" .
git status --short
git diff --stat

# exact evidence when needed
xxd -g1 -l 256 file.bin
python3 exploit.py
```

## RTK / Rust Token Killer

If RTK is already installed for the current agent, it can rewrite supported noisy commands into compact forms. Verify the installed behavior before relying on automatic rewriting.

Typical setup from V1 environments:

```bash
rtk --version
rtk rewrite 'git status'
rtk rewrite 'ls -la'
rtk gain
```

An installation may support agent-specific initialization such as:

```bash
rtk init --agent hermes --auto-patch
```

Treat third-party installer commands as environment-specific; inspect/verify rather than blindly reinstalling during a CTF.

## CTF rule

Compression must not destroy rare evidence.

Prefer:

```text
raw artifact saved to disk -> compact summary in context -> targeted raw slice on demand
```

For `strings`, `binwalk`, network output or exploit logs, save the full artifact/output when it may contain one rare decisive line, then search/filter it.

## Lean instruction design

Always-loaded files should contain:

- routing;
- hard invariants;
- minimal decision rules.

Move into on-demand references:

- long payload catalogs;
- environment-specific setup;
- exhaustive checklists;
- historical challenge examples;
- verbose tutorials.

This is the same progressive-disclosure principle used by V2 category skills.

## When to expand output

Re-run raw or narrower when:

- compact output hides the failing line;
- binary offsets/bytes matter;
- ordering/timing matters;
- an exact server response is the oracle;
- the user explicitly needs complete logs.

Token efficiency is subordinate to correctness.

## Provenance

Consolidated from V1 `token-efficient-cli-workflows` (`SKILL.md` blob `0cf38b701fab3ece4889cc5c231061090d0ca283`). Preserve relevant third-party RTK attribution/config notes if V1 supporting references are migrated later.