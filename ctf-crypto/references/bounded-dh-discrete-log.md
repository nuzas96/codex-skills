# Bounded Diffie-Hellman Discrete Logs

Use this reference when a Diffie-Hellman-like challenge exposes public values such as

```text
A = g^a mod n
B = g^b mod n
```

and one private exponent is known or strongly hinted to lie in a comparatively small interval.

The decisive weakness is usually **the exponent bound**, not the apparent bit length of the modulus. A 150-, 256-, or 2048-bit modulus does not protect a private exponent chosen from only a few million possibilities.

This reference also covers the common CTF complication where the modulus is composite or `gcd(g,n) != 1`, so ordinary baby-step giant-step fails because it tries to invert a non-unit.

---

## Recognition signals

Strong signals include:

- Diffie-Hellman public values `A`, `B`, generator/base `g`, modulus `p`/`n`;
- narrative or source gives a maximum private exponent, small RNG range, timestamp-derived exponent, PIN-sized secret, or bounded counter;
- full discrete log looks impossible from modulus size, but the exponent interval is small;
- a normal BSGS implementation raises an inverse error;
- `gcd(g,n) > 1` or the supposed DH modulus is composite;
- recovering either private exponent immediately yields a shared secret used in a KDF/AES layer;
- the service binds the intercept and verification to one cookie/session and a short deadline.

Fast mental model:

```text
large modulus
+ small exponent interval
= interval discrete log, not full-group discrete log
```

---

## First discriminating tests

Write down the exact equations and inspect the parameters before choosing a solver:

```python
from math import gcd

print('n bits =', n.bit_length())
print('gcd(g,n) =', gcd(g, n))
```

Also determine:

```text
0 <= x <= B ?
g^x = A mod n ?
g^x = B mod n ?
is n actually prime?
```

If source is available, identify exactly how the private exponent is sampled. Do not infer a bound only from one observed value.

If the bound is `B`, ordinary bounded BSGS costs roughly:

```text
O(sqrt(B)) time
O(sqrt(B)) memory
```

For example, a range of millions reduces to only a few thousand baby steps and giant steps.

---

## Standard bounded baby-step giant-step

For a unit base (`gcd(g,n)=1`), solve

```text
g^x = h mod n
0 <= x <= B
```

by writing

```text
x = i*m + j
m = ceil(sqrt(B+1))
```

Then

```text
g^(i*m+j) = h
h * (g^(-m))^i = g^j mod n
```

Store the baby steps `g^j`, then walk giant steps until a table match appears.

```python
import math


def bsgs_bounded(g: int, h: int, n: int, bound: int):
    g %= n
    h %= n
    m = math.isqrt(bound) + 1

    table = {}
    value = 1
    for j in range(m):
        table.setdefault(value, j)
        value = value * g % n

    gm = pow(g, m, n)
    factor = pow(gm, -1, n)

    gamma = h
    for i in range(m + 1):
        j = table.get(gamma)
        if j is not None:
            x = i * m + j
            if x <= bound and pow(g, x, n) == h:
                return x
        gamma = gamma * factor % n

    return None
```

The final `pow(g,x,n) == h` check is mandatory. Hash-table collisions, reduced equations, order wraparound, or an implementation mistake must not become an accepted secret.

---

## Why ordinary BSGS can fail

The giant-step multiplier requires

```text
(g^m)^(-1) mod n
```

which exists only when

```text
gcd(g,n) = 1
```

If Python reports something like:

```text
ValueError: base is not invertible for the given modulus
```

that is not evidence that the bounded-DLP idea is wrong. It means the algebra used by ordinary BSGS assumes a multiplicative group, while the challenge gave a non-unit base or composite modulus.

Before changing attacks, inspect:

```python
import math
print(math.gcd(g, n))
```

This error is a **parameter-structure signal**.

---

## Safe handling of non-coprime bases

There are two useful strategies.

### Strategy A: reduce to a coprime divisor as a projection

If `d = gcd(g,n) > 1` and a divisor `q | n` can be chosen such that

```text
gcd(g,q) = 1
```

then the original equation

```text
g^x = h mod n
```

implies

```text
g^x = h mod q
```

So a bounded DLP modulo `q` can produce candidate exponents.

This is useful in CTFs where one shared factor is obvious and removing it leaves a convenient coprime modulus.

But this is only a **projection** of the original equation. It can lose information or produce an exponent equivalent only modulo the order of `g` in the reduced group.

Therefore:

```text
recover candidate modulo q
→ verify pow(g, candidate, n) == h on ORIGINAL n
```

If the reduced candidate does not verify, do not conclude the bounded attack is dead. Use extended BSGS or enumerate other candidates consistent with the reduced relation.

### Strategy B: extended BSGS / gcd stripping

For the general congruence

```text
a^x = b mod m
```

with `gcd(a,m) != 1`, repeatedly strip common gcd factors before entering the ordinary BSGS phase.

Conceptually:

```text
while d = gcd(a,m) > 1:
    check whether the target is compatible with d
    divide target/modulus by d
    accumulate the forced prefix factor
    increment the exponent offset

then solve the remaining coprime DLP with BSGS
```

A compact implementation pattern is:

```python
import math


def exbsgs_bounded(a: int, b: int, m: int, bound: int):
    """Solve a^x == b (mod m), 0 <= x <= bound, including gcd(a,m)>1."""
    if bound < 0:
        return None

    a %= m
    b %= m

    if m == 1:
        return 0
    if b == 1:
        return 0

    offset = 0
    k = 1

    while True:
        d = math.gcd(a, m)
        if d == 1:
            break

        if b == k:
            return offset if offset <= bound else None

        if b % d != 0:
            return None

        b //= d
        m //= d
        k = (k * (a // d)) % m
        offset += 1

        if offset > bound:
            return None

    # Now k * a^y == b (mod m), with gcd(a,m)=1.
    try:
        target = b * pow(k, -1, m) % m
    except ValueError:
        return None

    y = bsgs_bounded(a, target, m, bound - offset)
    if y is None:
        return None

    return offset + y
```

Treat this as a reusable pattern, not a substitute for verification. Always check the recovered `x` against the **original** `(a,b,m)` values.

---

## Bound-first attack selection

Before using a generic DLP tool, compare the interval size against the group size/order.

```text
known small interval B
    → bounded BSGS or Pollard kangaroo
known smooth group order
    → Pohlig-Hellman may be cheaper
unknown/no useful bound
    → normal DLP analysis
non-coprime base/modulus
    → exBSGS / gcd stripping / factor structure first
```

A full-group discrete log package can be unnecessary overkill when the private exponent is intentionally tiny.

### BSGS vs Pollard kangaroo

Both can exploit a known interval.

- BSGS: deterministic, simple, `O(sqrt(B))` memory.
- Pollard kangaroo/lambda: similar expected time but far lower memory, useful when `B` is larger.

For normal CTF bounds in the millions or low billions, BSGS is often easiest to implement and debug.

---

## Recover only one exponent unless redundancy helps

If

```text
A = g^a mod n
B = g^b mod n
```

then recovering either `a` or `b` is enough:

```text
s = B^a mod n
```

or

```text
s = A^b mod n
```

Recovering both can be useful as a consistency check:

```python
assert pow(g, a, n) == A
assert pow(g, b, n) == B
assert pow(B, a, n) == pow(A, b, n)
```

But under a strict time window, do not spend half the deadline recovering a second exponent that is not required.

Rule:

```text
one verified exponent → derive shared secret immediately
```

---

## Always compute the real shared secret in the original construction

If a reduced modulus was used only to solve the discrete log, do **not** derive the final DH secret modulo that reduced value unless the target actually does so.

Correct pattern:

```text
reduced modulus / exBSGS
→ recover x
→ verify x against original public equation
→ shared = pow(other_public, x, ORIGINAL_MODULUS)
```

This distinction is critical.

---

## KDF and representation discipline

After recovering the shared integer, inspect exactly how it becomes key material.

Common possibilities:

```text
SHA256(long_to_bytes(shared))
SHA1(str(shared).encode())
SHA256(hex(shared).encode())
HKDF(shared_bytes, ...)
shared.to_bytes(fixed_width, 'big')
```

These are not interchangeable.

If the target hashes the **decimal ASCII representation** of the integer, then:

```python
material = str(shared).encode()
```

is different from:

```python
material = shared.to_bytes((shared.bit_length()+7)//8, 'big')
```

When source is available, mirror it exactly. Otherwise use strong downstream validation such as authenticated tags, valid padding plus structured plaintext, or a target-side verifier.

Do not "fix" a strange KDF representation to what a real protocol would normally use.

---

## AES follow-on layer

A typical challenge chain is:

```text
small DH exponent
→ bounded DLP
→ shared secret
→ hash/KDF
→ AES-CBC/GCM/etc.
→ secret phrase/token
```

For CBC, validate PKCS#7 strictly instead of blindly removing the last byte count:

```python
def unpad_pkcs7(data: bytes, block_size=16):
    if not data:
        raise ValueError('empty plaintext')
    n = data[-1]
    if not 1 <= n <= block_size:
        raise ValueError('bad padding length')
    if data[-n:] != bytes([n]) * n:
        raise ValueError('bad padding bytes')
    return data[:-n]
```

A plausible-looking plaintext is weaker evidence than a full forward relation plus valid cipher semantics.

---

## Do not solve disclosed randomness that is unnecessary

Challenges sometimes hint at multiple weak random values: private exponent, IV seed, timestamp seed, nonce counter, etc.

Ask first:

```text
Is this value already transmitted?
Is recovering it necessary for the final decryption?
Does it provide independent verification only?
```

If the IV is already returned in full, brute-forcing the IV seed is usually optional. It may be a useful consistency check, but it should not delay the decisive exponent recovery under a deadline.

Priority:

```text
necessary secret first
optional provenance later
```

---

## Stateful and time-limited crypto services

In interactive CTF crypto, correct mathematics can still fail if the protocol state is mishandled.

If `/intercept` creates a challenge instance and `/verify` consumes it:

1. create one persistent HTTP session;
2. fetch one fresh instance;
3. save all parameters locally;
4. perform the expensive math locally without extra network requests;
5. submit using the same cookies/session before the deadline;
6. do not refresh the intercept unless you intentionally abandon the current instance.

Python pattern:

```python
import requests

s = requests.Session()
challenge = s.get(BASE + '/intercept').json()
# solve locally
result = s.post(BASE + '/verify', json={'answer': recovered})
```

### Backend-worker inconsistency

If the same session occasionally receives contradictory state errors from a load-balanced service, distinguish **solver error** from **backend-state routing noise**.

A safe CTF retry policy is:

```text
same recovered candidate
+ same session
+ same challenge instance
→ bounded retry of verification only
```

Do not automatically call `/intercept` again, because that may rotate the secret and invalidate the value you just recovered.

Record response classes and stop retrying when the deadline or target semantics say the instance has expired.

---

## End-to-end solver architecture

Prefer one deterministic script:

```text
GET challenge instance using persistent session
→ parse n,g,A,B,ciphertext,IV
→ read/derive exponent bound
→ inspect gcd(g,n)
→ bounded BSGS if unit
   or exBSGS/gcd-reduced candidate search if non-unit
→ verify private exponent on original equation
→ compute shared secret on original modulus
→ reproduce exact KDF representation
→ decrypt and validate plaintext
→ submit immediately with same session
→ bounded same-instance retries only if evidence shows backend inconsistency
→ decode/extract any returned final artifact
```

This minimizes manual delay and stale-session mistakes.

---

## High-value checks when stuck

### BSGS inverse throws `ValueError`

Check:

```python
math.gcd(g, n)
```

If non-one, switch to exBSGS/gcd stripping or a justified coprime projection.

### Candidate works modulo reduced modulus but not original

The projection lost information or returned an equivalent exponent class. Use the original equation as truth and recover/enumerate a candidate that satisfies it.

### Shared secret looks right but AES is garbage

Check representation before blaming the DLP:

- decimal ASCII vs raw bytes;
- hex text vs integer bytes;
- fixed-width leading zeroes;
- hash family/truncation;
- IV encoding;
- CBC padding.

### Verification says no active session

Confirm:

- same cookie jar/session object;
- no accidental second `/intercept`;
- deadline not expired;
- backend inconsistency is reproducible before adding retries.

### Bound seems too large for memory

Use a memory-reduced interval-DLP technique such as Pollard kangaroo, or split/parallelize the interval if target constraints justify it.

---

## What not to do

Do not:

- judge DLP hardness only from modulus bit length;
- linearly brute-force millions of exponents when BSGS reduces the work to square root;
- assume `p` is prime because the variable is named `p`;
- assume `g` is invertible;
- treat an inverse error as proof BSGS is conceptually wrong;
- derive the final shared secret using a helper/reduced modulus when the target uses the original modulus;
- accept a candidate without `pow(g,x,n)==public` verification;
- guess key serialization;
- recover an IV seed when the IV itself is already supplied and the seed is irrelevant;
- start a new session between intercept and verification;
- refresh a timed challenge while still solving the old parameters.

---

## Routing and ownership

This remains `ctf-crypto` when the primary blocker is recovering the bounded discrete logarithm and reproducing the cryptographic construction.

Add `ctf-web` only when HTTP authentication/session exploitation itself becomes the hard primitive rather than simple state preservation.

Related references:

- `modern-ciphers.md` for AES/mode-specific issues;
- `advanced-math.md` for broader DLP/finite-field math;
- `ecc-attacks.md` when the discrete log is on an elliptic curve rather than an integer multiplicative structure.

---

## Provenance

Generalized from the Bahtera Siber `Surat Pahlawan` workflow. The reusable lessons are the small private-exponent interval, square-root bounded-DLP search, non-unit/composite-modulus handling, original-equation verification, exact shared-secret serialization, and same-session deadline discipline. Challenge-specific parameters, recovered exponents, phrases, credentials, endpoints, and flag values are intentionally omitted.
