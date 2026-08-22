# Modern Web Chains

## Contents

- URL representation mismatch
- FTP bounce and protocol smuggling
- Blind SQL injection through sort order
- Upload polyglots that survive image processing
- GraphQL alternate resolver paths
- Length-confusion memory disclosure

## URL Representation Mismatch

When an SSRF filter checks a raw hostname string but the client later resolves it, try equivalent loopback representations and verify what the downstream resolver accepts:

- unsigned 32-bit decimal IPv4, such as converting `127.0.0.1` with `int(ipaddress.ip_address(...))`;
- shortened or mixed-base IPv4 forms where supported;
- IPv6-mapped IPv4;
- redirects, DNS rebinding, and userinfo/parser discrepancies.

Do not stop at reaching localhost. Enumerate internal routes and look for a second primitive such as SSTI, admin-only behavior, or an internal API. Encode the complete chain in one request only after each stage works separately.

## FTP Bounce and Protocol Smuggling

An FTP server that permits the client to choose the data destination can become an internal TCP proxy. Investigate `PORT` or `EPRT` handling and whether hostnames, arbitrary ports, or internal addresses are accepted.

Chain model:

1. Set the FTP data connection target to an internal plaintext service.
2. Select an FTP command whose argument is forwarded to that connection.
3. Encode the destination protocol exactly, including length fields and CRLF boundaries.
4. Account for URL decoding or other transformations applied by the FTP implementation.
5. Capture the data-channel response as the protocol oracle.

For Redis RESP, derive frames rather than memorizing them: an array starts with `*N`, each bulk string with `$LEN`, and every component ends in CRLF. Test a harmless command before reading a key.

## Blind SQL Injection Through Sort Order

If input reaches `ORDER BY` but output rows are visible, turn row order into a boolean channel:

```sql
ORDER BY CASE WHEN (<condition>) THEN numeric_column ELSE text_column END
```

Prepare two rows whose numeric ordering and lexical ordering disagree. Determine truth by which marker appears first. Then extract length or bytes with binary search over `ASCII(SUBSTRING(...))`; avoid a printable-character linear scan unless request limits are irrelevant.

Useful properties:

- It survives filters focused only on `UNION`, `SLEEP`, or `BENCHMARK`.
- The oracle can live in either the column expression or direction expression.
- Stable tie-breaking matters; add a secondary sort key when needed.
- Use response positions, structured IDs, or JSON order as the success predicate.

## Upload Polyglots That Survive Image Processing

When extension controls server execution but a decoder validates content, distinguish three questions:

1. Does the upload pass image parsing?
2. Does server-side re-encoding preserve the payload?
3. Does the web server execute the stored extension?

Place code in a format-valid region rather than blindly appending it. Download the stored result and byte-compare it after every attempt. For PHP-bearing images, a parser-stopping construct such as `__halt_compiler()` can prevent arbitrary trailing image bytes from being interpreted as PHP syntax. Confirm the active handler and storage path before building command execution.

## GraphQL Alternate Resolver Paths

Authorization may exist on a top-level resolver but not on nested relations returning the same object. Use introspection or error-guided field discovery to build an object graph, then enumerate every path to the protected field.

Checklist:

- Compare direct lookup, list, search, parent-child, and reverse-relation resolvers.
- Test field-level authorization independently from object-level authorization.
- Treat a forged or weakly signed JWT as only one chain link; authorization logic may still require a resolver bypass.
- Request the minimum sensitive field first to separate auth failure from query-shape errors.

## Length-Confusion Memory Disclosure

For custom services receiving both `data` and `size`, test whether the claimed length is trusted beyond the actual buffer. Increase gradually and inspect binary output, repeated heap fragments, environment strings, keys, or structured markers.

Workflow:

1. Establish normal echo or health-check behavior.
2. Send a claimed size just above the real data length.
3. Increase in bounded steps and retain raw bytes rather than decoded text only.
4. Identify stable secret prefixes and exact key length.
5. Reconstruct any downstream crypto parameters from the application response instead of assuming mode, IV, or padding.

Source basis: reusable abstractions from the DalCTF 2026 organizer writeups, <https://github.com/DalCTF/DalCTF2026>.
