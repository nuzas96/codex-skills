# NoSQL Injection

Canonical V2 reference for CTF NoSQL query injection, especially JSON/MongoDB-style operator injection. Use when user-controlled scalar fields can become query objects/operators or when server-side query expressions are constructed unsafely.

## Recognition

Strong signals:

- JSON API backed by MongoDB/Mongoose or another document database;
- source passes request objects directly into query filters;
- application expects a string but accepts an object/array;
- query parameters such as `field[$ne]`, `field[$regex]` survive framework parsing;
- Mongo-style error messages/operators;
- boolean behavior changes when a value is replaced with `{ "$ne": ... }` or `{ "$regex": ... }`.

Do not assume every NoSQL database supports Mongo operators. Identify the driver/query language first.

## Core primitive: type/operator confusion

A vulnerable pattern often looks conceptually like:

```javascript
collection.findOne({ username: req.body.username, password: req.body.password })
```

If the application validates only field presence, JSON can change a scalar into a query object:

```json
{
  "username": {"$ne": "impossible"},
  "password": {"$ne": "impossible"}
}
```

The key issue is **query structure controlled by input type**, not the literal `$ne` payload.

## Minimal testing sequence

1. Capture a valid baseline with scalar values.
2. Replace **one field** with an operator object while keeping everything else identical.
3. Compare status, redirect, body shape/length, auth cookie and application state.
4. If object input is rejected, test whether URL/form parsers can build nested objects (`field[$ne]`, arrays, bracket notation).
5. Once one operator is accepted, map the exact operator set/driver behavior rather than spraying payload lists.

## Authentication bypass

High-value operators in Mongo-like query languages:

```text
$ne      not equal
$gt/$gte ordering
$regex   pattern match / blind prefix oracle
$exists  field existence
$in      membership
```

For login, first target one known user while relaxing only the password condition. Matching arbitrary users with both fields widened can produce unstable/incorrect account selection.

Example conceptual probe:

```json
{"username":"admin","password":{"$regex":".*"}}
```

If successful, verify the actual authenticated identity/role rather than treating any 200 response as bypass.

## Blind extraction with regex

When response behavior tells whether a query matched, prefix regex can become a character oracle:

```json
{"username":"admin","password":{"$regex":"^a"}}
{"username":"admin","password":{"$regex":"^ab"}}
```

Before automating:

- prove one true and one false prefix;
- escape regex metacharacters correctly;
- determine character alphabet from context/source;
- distinguish case sensitivity/collation;
- identify account lockout/rate limits if any.

Then automate prefix growth and cache results.

## `$where` / server-side expression injection

Some MongoDB configurations historically allow JavaScript predicates via `$where`. This is a different primitive from ordinary operator injection.

Check source/driver/database version to confirm the operator is accepted. If exposed, use a simple boolean or timing proof before attempting data extraction. Modern deployments may disable/deprecate server-side JavaScript or sanitize `$` operators.

## URL/form parser differences

Framework parsing can change:

```text
username[$ne]=x
```

into a nested object, but not all frameworks/configurations do. Inspect the server-side parsed type if source/debug behavior is available.

Test JSON and form/query inputs separately; a safe JSON schema does not imply safe URL parser behavior and vice versa.

## Other NoSQL families

For CouchDB/Couchbase/ArangoDB/Elasticsearch or custom query DSLs, identify their native expression/query syntax first. The reusable question remains:

> Can attacker input alter query **structure/operator semantics** rather than remain a data value?

Do not transplant Mongo payloads blindly.

## Automation discipline

Generic NoSQL scanners can help discover leads but often produce false positives around authentication/status pages. For CTFs, a short target-specific script with a proven boolean oracle is usually more reliable.

Useful automation inputs:

```text
endpoint
field/path
operator
known account/document selector
true-response classifier
alphabet
rate limit
```

## Common failure modes

- server validates scalar types before query construction;
- Mongoose/schema casting rejects objects/operators;
- `$`/dot-key sanitization is enabled;
- query matches a document but auth code separately verifies password;
- regex anchors/case/escaping are wrong;
- response classifier confuses generic 200/error pages with a true match.

## Cross-category pivots

If injection reaches application/admin functionality, remain `ctf-web`. If a recovered encrypted field needs real cryptanalysis, add `ctf-crypto`. If the backend exposes a custom binary protocol whose logic must be reversed, add `ctf-reverse`.

## Provenance

Consolidates V1 `exploiting-nosql-injection-vulnerabilities/SKILL.md` (Apache-2.0, author `mahipal`, blob `05d31b4e2ce35440b9fb80da13f51677c98f071e`) and existing MongoDB/$where patterns in `ctf-web/server-side-advanced-4.md`. Generic assessment-report/remediation boilerplate is intentionally omitted.