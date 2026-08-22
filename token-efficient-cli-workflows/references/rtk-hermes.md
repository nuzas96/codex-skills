# RTK for Hermes Reference

RTK (Rust Token Killer) is a Rust CLI/proxy that reduces token consumption by filtering and summarizing command output before it reaches the model context. It is most valuable for terminal-heavy agent work: git, test runners, build logs, directory listings, grep/search output, Docker/Kubernetes, and similar noisy commands.

## Install

Recommended Linux/macOS install:

```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
```

The installer detects OS/arch, downloads a release tarball, verifies SHA-256 checksums, checks archive paths for traversal, and installs to `~/.local/bin/rtk` by default.

Verify:

```bash
rtk --version
rtk --help | head -80
```

## Hermes Initialization

Initialize Hermes integration:

```bash
rtk init --agent hermes --auto-patch
```

This creates a Hermes plugin and enables it in `~/.hermes/config.yaml`.

Typical files:

```text
~/.hermes/plugins/rtk-rewrite/__init__.py
~/.hermes/plugins/rtk-rewrite/plugin.yaml
```

The plugin registers a `pre_tool_call` hook. For Hermes `terminal` tool calls, it runs:

```bash
rtk rewrite '<original command>'
```

If RTK returns a rewritten command, the plugin mutates the terminal command before execution. It fails open on timeout/error so normal terminal usage still works.

Hermes must be restarted after initialization for automatic rewriting to apply in a running session.

## Verification

Smoke tests:

```bash
rtk rewrite 'git status'
rtk rewrite 'ls -la'
rtk gain
```

Expected examples:

```text
git status -> rtk git status
ls -la     -> rtk ls -la
```

`rtk gain` may report `No tracking data yet` immediately after install; that is normal until RTK-wrapped commands run.

## Caveats

- RTK primarily affects shell/terminal commands. Native Hermes file tools such as `read_file`, `search_files`, and `patch` do not necessarily pass through RTK.
- Compact output is not always appropriate. For byte-level CTF work, exploit debugging, exact stack traces, or subtle parser bugs, use raw output or a narrow command that preserves the relevant detail.
- If GitHub API is rate-limited while inspecting the repo, raw README URLs may still work, e.g. `https://raw.githubusercontent.com/rtk-ai/rtk/master/README.md`.
