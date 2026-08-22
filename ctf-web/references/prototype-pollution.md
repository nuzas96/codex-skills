# JavaScript Prototype Pollution

Canonical V2 reference for client- and server-side JavaScript prototype pollution. The reusable exploit model is **source -> polluted prototype property -> gadget/sink**, not merely finding that `({}).polluted` can be set.

## Recognition

Strong source patterns:

- recursive merge/clone/default functions over attacker-controlled objects;
- parsing nested keys such as `__proto__[x]`, `constructor[prototype][x]`;
- unsafe property assignment by path;
- URL/query/hash parsers that materialize nested objects;
- JSON merge/update APIs in Node.js.

Potential paths:

```text
__proto__.x
__proto__[x]
constructor.prototype.x
constructor[prototype][x]
```

Exact behavior depends on parser/library/version and whether dangerous keys are filtered.

## Confirm the source cleanly

Client-side example concept:

```javascript
({}).ctfProbe
```

Set a benign unique property through the suspected source, then check whether a fresh ordinary object inherits it.

Server-side pollution often needs a response/state oracle because the prototype is not directly visible. Prefer a harmless property that affects a predictable code path over destructive global properties.

Distinguish:

- own property on one object;
- pollution of a custom prototype;
- global `Object.prototype` pollution.

They have different gadget reach.

## Find gadgets instead of guessing payloads

After confirming a source, search code/dependencies for property reads where no own-property check/default initialization occurs:

```javascript
if (options.isAdmin) ...
render(data, options)
child_process.spawn(cmd, args, options)
config.url
config.escapeFunction
```

For each candidate:

1. is the object inheriting from the polluted prototype?
2. is the property absent as an own property?
3. can attacker control its type/value?
4. does it reach a meaningful sink?
5. what action triggers that sink?

This is more reliable than trying generic `isAdmin`, `shell`, `NODE_OPTIONS`, template or DOM property lists blindly.

## Client-side chain

```text
URL/hash/postMessage/object source
 -> prototype property
 -> library/application property read
 -> DOM/URL/code sink
 -> XSS/flag action
```

Use DOM Invader or source tracing to accelerate gadget discovery. Reproduce the actual source and sink in the target browser/version.

Potential gadget classes include:

- HTML/string passed into `innerHTML`/HTML parser;
- script/URL/transport configuration;
- sanitizer configuration objects;
- DOM attribute/property defaults.

Pollution alone is not XSS.

## Server-side chain

```text
JSON/query merge source
 -> server process prototype
 -> later request/job/render/spawn reads polluted property
 -> auth/state/RCE effect
```

Important questions:

- Does pollution persist across requests in the same Node process?
- Is the object cloned/frozen/recreated?
- Does the trigger happen in the same request or a later endpoint?
- Are workers/processes recycled?
- Is the polluted property overwritten by an own property?

A multi-request trigger can be the intended CTF chain.

## Authentication / logic gadgets

Properties such as `isAdmin`, `role`, `verified`, feature flags or validation options can matter **only if source shows an inherited read**.

Do not report privilege escalation based solely on inserting these names into `__proto__`. Verify the downstream authorization/state change.

## Node execution gadgets

RCE gadgets around template engines, child processes or Node options are highly version/library-specific. Before using a historical gadget, verify:

- exact Node version;
- library/template-engine version;
- target API invocation;
- whether the relevant options object inherits from polluted prototype;
- any post-pollution sanitization/copying.

Use target source first; pattern catalogs are hypotheses.

## Detection pitfalls

- JSON parsing of `{"__proto__":...}` may produce an own property without immediately changing the parsed object's prototype; the vulnerable **merge step** is often what pollutes.
- modern libraries may explicitly drop `__proto__`, `prototype`, or `constructor` keys;
- `Object.create(null)` objects do not inherit from `Object.prototype`;
- setting `toString` to a non-function may cause noisy DoS but teaches little about a flag path;
- pollution can affect your test harness itself; use a fresh page/process between experiments when needed.

## Cross-reference

Existing V1 `ctf-web/node-and-prototype.md` contains broader Node/sandbox chains. Use this focused reference for the pollution source/gadget methodology and link into that file only for a matching Node-specific hard chain.

## Provenance

Consolidates V1 `exploiting-prototype-pollution-in-javascript/SKILL.md` (Apache-2.0, author `mahipal`, blob `02b462bcc25f6e172bb9eee3ad243c049d596541`) with existing `ctf-web/node-and-prototype.md`. Generic pentest report text and unverified gadget payload catalogs are intentionally not placed in the active router context.