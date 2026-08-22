# Path Traversal, LFI, and File-Path Confusion

Use when user input influences a filesystem path, filename, template include, download/view route, archive extraction path, or framework file helper.

## Recognition

Look for parameters such as `file`, `path`, `page`, `template`, `include`, `module`, `src`, `document`, `folder`, `dir`, or filename-like JSON fields. Source code is stronger evidence than parameter names.

Establish a normal file-read baseline before traversal attempts. Record status, body length, content type, and any canonicalized path/error.

## Decision Tree

```text
user controls path
  -> read or write?
  -> relative, absolute, URL, archive member, template name?
  -> what normalization happens and in which layer?
  -> smallest sensitive-file proof
  -> if include/execute semantics exist, evaluate escalation
```

## Traversal Families

Test only variants suggested by the target's normalization stack:

- `../` and `..\`;
- URL-encoded separators/dots;
- double decoding when multiple layers decode;
- mixed slash/backslash on Windows-aware stacks;
- repeated-dot or repeated-separator normalization quirks;
- absolute paths when only relative traversal is filtered;
- prefix/path-join confusion;
- alternate filesystem namespaces on Windows.

Old payloads such as overlong UTF-8 or PHP null-byte truncation are version-specific historical techniques. Do not spend time on them unless the runtime/version supports them.

## High-Signal Proof Files

Pick files that prove the primitive without unnecessary broad reads:

Linux examples:
- `/etc/hostname`
- `/etc/passwd`
- `/proc/self/cmdline`
- `/proc/self/environ`
- application `.env`/config/source files

Windows examples:
- `C:\Windows\win.ini`
- web/app configuration files

In source-available CTFs, prioritize the application's source/config and the expected flag location over generic `/etc/passwd` demonstrations.

## LFI vs Raw File Read

Determine whether the application:

- returns raw bytes;
- interprets the file as a template/script;
- routes through a language wrapper;
- reads through another parser.

This distinction controls escalation.

For PHP, wrappers such as `php://filter` can convert source into a readable representation when direct include executes it. `php://input`, `data://`, log/session inclusion, and similar paths are configuration/version dependent; confirm wrapper settings and inclusion semantics first.

## Path Parser Mismatch

CTF-relevant bugs often arise because adjacent layers disagree:

- proxy vs application path normalization;
- URL decoder vs router;
- `startswith()` authorization vs normalized path;
- extension check vs final stored filename;
- archive member name vs extraction destination;
- Windows vs POSIX separator handling;
- basename/canonicalization performed before vs after decoding.

Map the transformation order instead of generating hundreds of random encodings.

## Automation

Use `ffuf`, focused wordlists, or a small Python matrix only after you know the success predicate. Baseline filtering is mandatory; a `200` alone is not proof because many apps return custom error pages with `200`.

## Escalation

Once a file primitive is confirmed, ask whether the flag is already readable. Escalate to code execution only when needed and supported by the target's include/parser behavior.

Potential CTF chains include:

- source/config read -> secret/key -> token/session forgery;
- LFI -> application source -> hidden endpoint;
- include semantics -> controlled log/session/file -> execution;
- traversal write -> configuration/template overwrite;
- archive traversal -> place controlled file outside extraction root.

## Common Failure Modes

- Brute-forcing traversal depth without learning the base path.
- Treating every file-read endpoint as PHP LFI.
- Using stale null-byte/overlong-UTF8 payloads against modern runtimes.
- Looking only for `/etc/passwd` and missing app source/config/flag files.
- Ignoring decode/canonicalization order across proxy/framework layers.

## Provenance

Consolidated from the original `performing-directory-traversal-testing` Apache-2.0 skill and existing `ctf-web/server-side-advanced*.md` path/parser notes. Original source is preserved on `archive/pre-restructure-20260823`.
