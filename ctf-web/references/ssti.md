# SSTI / Template Injection

Use this reference when user-controlled data is rendered by a server-side template engine or when a reflected expression is evaluated rather than printed literally.

## Recognition

Start with harmless arithmetic probes and compare literal vs evaluated output:

- `{{7*7}}` — Jinja2/Twig-family signal
- `${7*7}` — Freemarker/Velocity/Spring-style signal
- `#{7*7}` — Thymeleaf/EL-family signal
- `<%= 7*7 %>` — ERB/EJS-family signal

Do not jump straight to RCE. First prove **evaluation**, then identify the engine from target behavior, dependency files, error messages, and syntax differences.

Useful discriminator: `{{7*'7'}}` commonly produces string repetition in Jinja2 but numeric behavior in Twig-like contexts. Treat this only as a hint; engine/version/custom filters can change behavior.

## CTF Decision Tree

```text
input reflected
  -> literal or evaluated?
  -> identify engine/framework/version
  -> enumerate available objects/filters/globals
  -> smallest useful primitive
       config leak / file read / object traversal / command execution
  -> derive final chain from target-specific objects
```

## Jinja2 / Flask

High-value objects include Flask config and template globals. Prefer stable globals such as `cycler`, `joiner`, namespace helpers, or application-provided objects over hard-coded `__subclasses__()` indexes.

Why: subclass indexes are process/version dependent and copied offsets often fail remotely.

Typical progression:

1. `{{config}}` or another harmless object disclosure.
2. Confirm Python object traversal is allowed.
3. Locate a stable path to useful globals/modules.
4. Read the target file or execute the minimum command needed for the flag.

If attributes such as `__class__`, `__mro__`, `__globals__`, brackets, dots, or underscores are filtered, derive equivalent access through target-supported filters/functions rather than blindly mutating payloads.

## Twig / PHP

Identify the exact Twig version and exposed filters/functions. Old payload catalogs become stale quickly. Check whether application-added callbacks, filters, filesystem helpers, or PHP functions are reachable. A successful expression oracle does not imply direct command execution.

## Java Template Engines

Freemarker, Velocity, Thymeleaf, Pebble, and expression-language stacks differ substantially by version and sandbox policy. Determine:

- exact engine;
- whether object/class access is exposed;
- whether utility classes are disabled;
- whether Spring/Java reflection or static methods are reachable.

Prefer dependency/version evidence over generic payload lists.

## Other Engines

For ERB/EJS/Smarty/Mako/Pongo2/Vue server rendering, use the same sequence: harmless evaluation -> fingerprint -> reachable objects -> smallest primitive. Check existing `ctf-web/server-side*.md` references for engine-specific historical patterns only after the engine is known.

## Client-Side Template Injection

If expressions execute only in the browser, this is CSTI rather than SSTI. Route to browser/client-side analysis and verify framework/version in the real browser. Do not interpret client-side `49` as server-side code execution.

## Automation

`tplmap`/`SSTImap` can help after a manual oracle exists. Automated fingerprinting should not replace source/dependency inspection and may generate false engine matches.

## Common Failure Modes

- Copying a Jinja2 subclass index from a writeup.
- Assuming `{{7*7}} -> 49` uniquely identifies one engine.
- Treating sanitization output in a test harness as proof of browser/server behavior.
- Brute-forcing payload syntax before reading `requirements.txt`, `package.json`, `composer.lock`, Java dependencies, or templates.
- Escalating to RCE when a direct config/file read already reaches the flag.

## Provenance

Consolidated from the repository's original `exploiting-template-injection-vulnerabilities` Apache-2.0 skill plus the existing `ctf-web/server-side*.md` CTF notes. The original pre-restructure source remains frozen on `archive/pre-restructure-20260823`.
