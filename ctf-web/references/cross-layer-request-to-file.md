# Cross-Layer Request-to-File Chains

Use this focused pass when a request crosses several interpreters and no single isolated test exposes a useful primitive. It complements [WAF/parser differentials](waf-parser-differentials.md), [request smuggling](request-smuggling.md), [path traversal](path-traversal-lfi.md), and the general [multi-stage chain workflow](../../ctf-solve/references/modern-chains.md); it does not replace those references.

## Recognition signals

- A proxy rewrites the request URI into a script path plus `PATH_INFO`.
- A route or signature is built from one path representation while the application parses or decodes another.
- A comma-delimited field selector is escaped as an SQL identifier and then inserted into a query expression.
- A query result is subsequently passed to a filesystem function such as `scandir`, `glob`, `include`, or `readfile`.
- A static-file location or `try_files` rule consumes paths that were transformed or normalized earlier.
- Several components appear individually strict, but attacker-controlled bytes pass through all of them in sequence.

Do not require this exact shape. Work backward from a useful sink (file read, listing, disclosure, authorization decision), then trace its input back to the raw request.

## Build a representation ledger

Record the exact value at each boundary. Keep raw bytes separate from parsed values; mark decode count, normalization, query/fragment splitting, and escaping explicitly.

| Layer | Record | Small discriminating test |
|---|---|---|
| Client / HTTP parser | Exact request-target form (origin-form or absolute-form), bytes, headers, and whether the client normalizes dot segments | Send one raw request with a minimal local socket client and compare with a normal URL client; use a harmless marker path |
| Nginx / reverse proxy | `$request_uri` versus normalized `$uri`, query args, location chosen, rewrite/internal redirect, `try_files`, `$fastcgi_script_name`, and `PATH_INFO` | Inspect the effective config and capture upstream/FastCGI parameters with a local echo fixture; change one request-target feature at a time |
| Application parser | `parse_url` order, percent-decode count, slash/NUL handling, route match, and the exact string used for both authorization and dispatch | Replay the captured path through the actual parser; test encoded delimiters before and after parsing |
| Signature layer | Exact bytes signed by the producer and exact bytes checked by the application | Recompute a synthetic signature from the target-derived canonical value; a signature on a different representation must fail |
| SQL layer | Value vs identifier vs expression context, quote escaping, DB dialect/version, SQL mode, PDO behavior, and query result shape | Use a harmless synthetic schema and compare a known column, a malformed identifier, and a benign scalar expression; observe rows/types, not only error text |
| Filesystem layer | Whether the value is a path, stream-wrapper URI, glob, or ordinary string; which function consumes it; permissions and resulting names/bytes | Use a temporary tree containing synthetic files; first prove listing/read behavior, then test the composed path through the next layer |
| Static-file layer | Location selected, captures, rewritten candidate paths, root/alias, and whether traversal is normalized before lookup | Request a harmless canary in an isolated local tree and verify the exact returned bytes and selected location |

Do not infer what a layer received from the URL shown in a browser or shell command. Preserve a raw request and capture the next layer's input whenever possible.

## Composition workflow

1. Draw the trust path from raw request bytes to the final useful sink. Include rewrites, decoders, authorization checks, query construction, wrappers, and file-serving rules.
2. For each edge, record `input -> transformation -> output` and the source/config line that implements it.
3. Test each transformation with harmless marker values. Confirm the next layer receives the predicted bytes.
4. Test the dangerous composition only after the component transforms are understood. Keep the same synthetic marker through the chain so the source of a change stays identifiable.
5. For signed data, align the signer to the application's actual canonical representation; do not treat a valid signature as proof that the route is safe, or a parser mismatch as a signature forgery.
6. For SQL field selectors, distinguish a quoted identifier from an expression. Escaping one quote character is not a proof across dialects: MySQL backslash behavior and SQL mode can change whether a delimiter remains escaped. Reproduce using the target engine/mode and a non-secret schema.
7. For PHP filesystem functions, test whether the value is interpreted by a registered stream wrapper. A wrapper may list names without reading file contents; prove listing, path disclosure, and content read as separate links.
8. Validate the final file-serving step independently with a synthetic canary. A discovered filename or path is not proof that the content sink is reachable.

## Service-state-and-constructor edges

For connected Web vulnerabilities, use the [compact exploit dependency graph](../../ctf-solve/references/modern-chains.md#compact-exploit-dependency-graph); retain the representation ledger above for each parser edge.

- **Authentication fall-through:** trace what happens after writing an error, including outbound requests. Test a harmless downstream state change despite a denied response. A second auth check may still block the action, but a separate service may let an earlier primitive create credentials or alter the shared auth store. Prove that mutation and subsequent authentication separately.
- **URL reconstruction:** include credentials/userinfo, authority, path, query and fragment as separate attacker-controlled inputs. Check both regex match and no-match behavior: a failed replacement may leave the original destination intact. Validate the parsed destination and actual serialized request, including method/body; do not assume an HTTP client can affect only HTTP services. Protocol compatibility and service defenses are explicit prerequisites.
- **Input delivery:** when a sink requires a local file, inventory who can create or supply it: uploads, temporary request spools, open descriptors, logs and caches. Test ownership, descriptor lifetime, parser validity and repeatability with synthetic data. A filename parameter alone proves neither arbitrary content nor arbitrary reading.
- **Constructor/dependency gadgets:** enumerate the installed classes reachable through reflection, then inspect initialization and delegated calls. Look for connection options, initialization queries, callbacks, local-file transfers and implicit reads/writes. Check argument conversion and exact dependency version. Prove one harmless constructor side effect before extending the chain; object creation or an exception alone is not code execution.
- **Target location and observation:** map the target to its service and required privileges. A file leak may supply database credentials without supplying database rows. Treat credential recovery, database connection/query execution and result observation as separate edges. If output is suppressed, test an authorized synthetic callback or a calibrated boolean/error/timing oracle with positive and negative controls; network policy, timeout behavior and state lifetime can invalidate it.

These are alternative edge families, not a required exploit sequence. Review the first missing prerequisite before collecting payloads or assuming a constructor is exploitable.

## Negative controls and stop conditions

- A normal request and one minimally mutated request should select the expected locations and route before exploring encodings.
- A wrong decode count, altered signed path, non-matching SQL identifier, empty wrapper match, and out-of-root canary should each fail for an observed reason.
- If a local CLI test disagrees with an FPM/proxy deployment, capture the boundary values and mark runtime parity as unknown; do not generalize the CLI result to the deployment.
- If the primitives fail individually, do not automatically discard the chain. If the composition also fails at a captured boundary, reject that specific chain and pivot.
- Do not brute-force signature keys or use a private verifier as an oracle when a configuration disclosure or representation mismatch is testable from source.

## Environment requirements

Nginx location order, absolute-form request handling, URI normalization, `rewrite ... last`, and FastCGI variables are version/configuration dependent. PHP-FPM can differ from CLI in SAPI configuration and path-info handling. SQL escaping depends on engine and mode. PHP wrappers depend on registration, function support, and filesystem permissions. Record actual versions and effective config; label untested behavior as unknown.

For a safe local reproduction, bind services to loopback, use synthetic keys/files/rows, keep private answers out of the app tree, and capture raw requests plus upstream parameters. Do not download images or install packages just to remove an explicitly documented runtime limitation.

## Provenance

Generalized after studying the official public DUCTF 2025 Legendary materials at pinned source revision `f423ae945ddb8370bbb4ca86c425dd8b9ed6a33b` (2026-11-12). The multi-layer recognition and validation workflow is generalized; no challenge payload or answer is reproduced here.

The service/state/constructor planning additions were generalized from the [official Off Dah Rails M8 writeup](https://github.com/DownUnderCTF/Challenges_2025_Public/blob/f423ae945ddb8370bbb4ca86c425dd8b9ed6a33b/web/off_dah_rails_m8/solve/WRITEUP.md), reviewed after the independent attempt (2026-11-12). No payloads, credentials or answers are retained.
