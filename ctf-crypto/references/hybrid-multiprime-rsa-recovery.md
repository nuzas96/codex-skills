# Hybrid Multi-Prime RSA Recovery

Use this playbook when an RSA-like CTF construction combines several individually modest weaknesses instead of one textbook attack:

- a modulus with three or more prime factors;
- partial factor residues such as `p mod 2^k` and `q mod 2^k`;
- an auxiliary congruence such as `(p + q) mod M`;
- one factor small enough for ECM or another cheap factoring method;
- a remaining partial-factor problem suitable for Coppersmith;
- a short hash-derived XOR layer around a modular value;
- non-invertible small exponents that require enumerating modular roots per prime and recombining with CRT.

The important lesson is **attack ordering**. Do not treat each clue independently and do not jump directly to a large lattice. Convert every leak into a tighter algebraic description, use cheap factoring to reduce the modulus, then solve only the remaining small-root problem.

This reference was generalized from a Bahtera Siber challenge writeup. Challenge-specific primes, ciphertexts, checksum values, flags and fixed constants are intentionally omitted.

---

## 1. Fingerprint

A common shape is:

```text
N = p * q * r

u = m^e1 mod N
v = (u + p + q) mod N
z = v^e2 mod N
h = Trunc_t(Hash(encode(z)))
c = z XOR int(h)
```

Public data may additionally leak:

```text
p mod 2^k
q mod 2^k
(p + q) mod M
```

The solve direction is the exact reverse of the construction:

```text
recover factors
    ↓
recover hash/XOR candidate z
    ↓
enumerate e2-th roots of z modulo each prime
    ↓
CRT to candidate v
    ↓
remove additive factor-dependent term
    ↓
enumerate e1-th roots modulo each prime
    ↓
CRT to candidate m
    ↓
validate by complete re-encryption
```

Do not attempt plaintext recovery until the factorization and every intermediate layer are algebraically verified.

---

## 2. Inventory the leaks before choosing an attack

Write down:

```text
factor count
approximate factor bit lengths
known low/high bits of each factor
auxiliary congruences involving factors
cipher exponents
hash truncation width
whether modular exponents are invertible modulo phi(N)
```

Useful questions:

1. Can a leaked residue of a missing factor be derived from `N` modulo the same base?
2. Is one factor cheap enough to recover independently with ECM?
3. After removing one factor, can an auxiliary congruence shrink the unknown part of another factor?
4. Does the exponent have a unique inverse, or will modular roots branch?
5. Is the outer hash/XOR map short enough to treat as a separate bounded fixed-point problem?

The right answer is often a **hybrid** attack rather than one named technique.

---

## 3. Derive another factor's low bits from the product

Suppose:

```text
N = p * q * r
p0 = p mod B
q0 = q mod B
B = 2^k
```

Then:

```text
N mod B = p0 * q0 * r0 mod B
```

If `p0*q0` is invertible modulo `B`:

```text
r0 = N * inverse(p0*q0, B) mod B
```

This is especially convenient for `B = 2^k` when the known prime residues are odd.

Always verify:

```python
assert (p0 * q0 * r0 - N) % B == 0
```

### If the product is not invertible

Do not force an inverse. Let:

```text
g = gcd(p0*q0, B)
```

The congruence has solutions only if:

```text
g | N
```

Reduce the congruence by `g` and preserve all residue classes if multiple solutions remain.

General rule:

> A modulus product relation can turn two partial factor leaks into a third partial factor leak for free.

---

## 4. Try cheap factoring before a lattice

If the factors are modest in size, run cheap factor methods first:

```text
trial division / small-prime checks
Pollard rho
Pollard p-1
ECM
```

For a multi-prime modulus, recovering **one** factor can be enough to make the structured remainder much easier.

Example:

```text
N = p*q*r
recover q with ECM
C = N // q = p*r
```

Now the lattice problem is no longer "factor a three-prime modulus with several unknowns." It is a one-variable partial-factor problem against the balanced cofactor `C`.

Validate every recovered factor immediately:

```python
assert N % q == 0
assert q % B == q0
```

Do not assume a factor is the leaked `p` or `q` until its residue or another public relation identifies it.

---

## 5. Combine a low-bit leak with an auxiliary congruence

Assume:

```text
p = p0 + B*x
p ≡ s (mod M)
```

where `p0 = p mod B` is known and `s` was derived from another leak such as:

```text
(p + q) mod M = S
s = (S - q) mod M
```

Then:

```text
B*x ≡ s - p0 (mod M)
```

This congruence should be solved correctly even when `B` and `M` are **not coprime**.

Let:

```text
g = gcd(B, M)
rhs = s - p0
```

A solution exists only if:

```text
g | rhs
```

Reduce:

```text
B1 = B / g
M1 = M / g
rhs1 = rhs / g
```

Now `gcd(B1, M1) = 1`, so:

```text
x0 = rhs1 * inverse(B1, M1) mod M1
x = x0 + M1*t
```

Therefore:

```text
p = p0 + B*(x0 + M1*t)
```

The unknown is no longer a full `x`; it is the smaller integer `t`.

This is a high-value preprocessing step before Coppersmith.

### Why this matters

A generic partial-factor attack may have an unknown close to the full high half of `p`. The extra congruence converts that unknown into an arithmetic progression with step `M1`, shrinking the root bound by roughly that factor.

Always exploit side congruences **before** building the lattice.

---

## 6. Recover the remaining factor with univariate Coppersmith

After a cheap factor is removed, suppose:

```text
C = p * r
p(t) = p0 + B*(x0 + M1*t)
```

Construct a polynomial over `Zmod(C)`:

```sage
R.<t> = PolynomialRing(Zmod(C))
f = p0 + B*(x0 + M1*t)
```

The desired root `t0` satisfies:

```text
f(t0) = p
p | C
```

This is a factor-root Coppersmith problem.

For balanced `p` and `r`, `p ≈ C^0.5`, so `beta` is typically near `0.5`. Derive the actual bound from the factor sizes and progression step rather than copying a constant.

Sage-style sketch:

```sage
bound = ceil(max_x / M1)
roots = f.monic().small_roots(
    X=bound,
    beta=beta,
    epsilon=epsilon
)

for t0 in roots:
    candidate = ZZ(p0 + B*(x0 + M1*ZZ(t0)))
    if candidate > 1 and C % candidate == 0:
        p = candidate
        r = C // p
        break
```

Validate all original leak relations:

```python
assert p * q * r == N
assert p % B == p0
assert q % B == q0
assert r % B == r0
assert (p + q) % M == S
```

### Do not overfit `beta`

If the recovered factor is not exactly half of `C`, estimate:

```text
beta ≈ log(p) / log(C)
```

and keep the root bound explicit in `PROGRESS.md`.

---

## 7. Separate the hash/XOR fixed-point layer from RSA

A construction may hide `z` as:

```text
h = Trunc_t(Hash(encode(z)))
c = z XOR h
```

Therefore:

```text
z = c XOR h
```

but `h` must satisfy the fixed-point equation:

```text
h = Trunc_t(Hash(encode(c XOR h)))
```

Treat this as a separate bounded search problem over the `t`-bit checksum space.

### Important source limitation

The source writeup that motivated this reference supplied a valid short fixed point but did **not** document the method used to discover it. Do not turn that challenge value into reusable knowledge and do not hardcode it.

Instead, the reusable rule is:

1. define the exact encoding of `z` before hashing;
2. define the exact endianness/integer interpretation of the truncated digest;
3. generate candidate `h` values using a search method appropriate for `t`;
4. accept only candidates satisfying the fixed-point equation exactly;
5. carry **all** valid candidates into the modular-root stage.

For very small `t`, direct enumeration is fine. For widths such as 32 bits, use optimized native/GPU search if necessary, or look for additional challenge structure that reduces the candidate space.

A flag-looking downstream plaintext is not proof that the fixed point is correct; full re-encryption is.

---

## 8. Do not assume a modular exponent has a unique inverse

After factorization, suppose:

```text
z = v^e2 mod N
N = p*q*r
```

It is tempting to compute:

```text
d2 = inverse(e2, phi(N))
v = z^d2 mod N
```

That only works when the exponent is invertible over the relevant group.

If:

```text
gcd(e2, p_i - 1) != 1
```

for one or more prime factors, multiple `e2`-th roots may exist.

Correct strategy:

```text
roots modulo p
roots modulo q
roots modulo r
       ↓
Cartesian product
       ↓
CRT each combination
       ↓
candidate v values
```

Sage sketch:

```sage
primes = [p, q, r]
root_sets = [
    Zmod(prime)(z).nth_root(e2, all=True)
    for prime in primes
]

for roots in itertools.product(*root_sets):
    v = ZZ(CRT(list(map(ZZ, roots)), primes))
    assert power_mod(v, e2, N) == z
```

This turns the inversion into a finite **root tree**.

Record the root count per prime. It explains the candidate explosion and prevents accidentally discarding valid branches.

---

## 9. Reverse additive layers before the next root tree

If the construction used:

```text
v = (u + p + q) mod N
```

then for every candidate `v`:

```text
u = (v - p - q) mod N
```

Only then undo the previous exponent:

```text
u = m^e1 mod N
```

Again enumerate roots independently modulo each prime:

```sage
root_sets = [
    Zmod(prime)(u).nth_root(e1, all=True)
    for prime in primes
]

for roots in itertools.product(*root_sets):
    m = ZZ(CRT(list(map(ZZ, roots)), primes))
```

Do not collapse the two exponent layers into one unless the intervening addition is absent.

---

## 10. Candidate control

A multi-layer root tree can create several candidates. Keep it disciplined:

```text
hash/XOR candidates
    × e2-root combinations
    × e1-root combinations
```

At each stage apply only algebraically valid filters:

- exact fixed-point equality;
- exact modular-power equality;
- expected message-size bound if known from source;
- exact parser/encoding constraints;
- flag format as a final scoring filter.

Then run the full forward construction on any surviving plaintext.

Example verifier shape:

```python
def verify(m):
    u = pow(m, e1, N)
    v = (u + p + q) % N
    z = pow(v, e2, N)
    raw = encode(z)
    h = int.from_bytes(hashlib.sha256(raw).digest()[:t_bytes], "big")
    return (z ^ h) == ciphertext
```

The original ciphertext equation is the final authority.

---

## 11. Attack-order decision tree

```text
multi-prime modulus + partial factor leaks
        ↓
reduce N modulo leaked base
        ↓
derive any missing factor residue
        ↓
try cheap factor methods
        ↓
recover one full factor if feasible
        ↓
apply auxiliary congruences to remaining factor
        ↓
turn high unknown into arithmetic progression
        ↓
univariate Coppersmith on the reduced cofactor
        ↓
verify full factorization + every leak
        ↓
solve short hash/XOR fixed-point layer
        ↓
enumerate modular roots per prime
        ↓
CRT root tree
        ↓
reverse additive layer
        ↓
enumerate next modular-root tree
        ↓
full forward verification
```

The order matters. Every early step should reduce the dimension or candidate count of the next one.

---

## 12. Common dead ends

### Dead end: Coppersmith immediately on the original multi-prime modulus

If ECM can cheaply peel off one factor, do that first. A reduced two-factor cofactor is usually a much cleaner small-root target.

### Dead end: ignore the auxiliary modulus leak

A relation such as `(p+q) mod M` may look tiny, but combined with `p mod 2^k` it constrains the high-half variable to an arithmetic progression and can materially shrink the Coppersmith bound.

### Dead end: use CRT as if all moduli were coprime

When combining a `2^k` leak with a decimal modulus such as `10^d`, the moduli often share powers of two. Solve the linear congruence with `gcd` reduction instead of calling a coprime-only CRT blindly.

### Dead end: invert the exponent globally

If `gcd(e, phi(N)) != 1`, a single RSA private exponent does not represent all plaintext roots. Enumerate roots modulo prime factors.

### Dead end: keep only the first modular root

The valid plaintext may live on a different CRT branch. Preserve all roots until an algebraic or format constraint eliminates them.

### Dead end: accept a hash/XOR candidate because downstream bytes look plausible

Verify the exact fixed-point relation and then the complete encryption pipeline.

### Dead end: use floating-point approximations for factor bounds

Keep integer bounds explicit. Coppersmith success depends on the real root size, not a rough narrative estimate.

---

## 13. Reusable Sage/Python skeleton

```sage
import itertools
from math import gcd

# Inputs:
# N, B=2^k, p0, q0, auxiliary modulus M and relation S,
# one recovered factor q, ciphertext, exponents e1/e2.

# Derive r mod B when invertible.
r0 = (N * inverse_mod((p0*q0) % B, B)) % B

# Remove cheap factor.
C = N // q

# Derive p mod M from auxiliary relation.
s = (S - q) % M
rhs = (s - p0) % M
g = gcd(B, M)
assert rhs % g == 0

B1 = B // g
M1 = M // g
rhs1 = rhs // g
x0 = (rhs1 * inverse_mod(B1, M1)) % M1

# p(t) = p0 + B*(x0 + M1*t)
R.<t> = PolynomialRing(Zmod(C))
f = p0 + B*(x0 + M1*t)

# Derive X/beta from actual sizes; placeholders only.
roots = f.monic().small_roots(X=X_bound, beta=beta, epsilon=epsilon)

for t0 in roots:
    candidate = ZZ(p0 + B*(x0 + M1*ZZ(t0)))
    if candidate > 1 and C % candidate == 0:
        p = candidate
        r = C // p
        break
else:
    raise RuntimeError("partial factor not recovered")

assert p*q*r == N
assert p % B == p0
assert q % B == q0
assert r % B == r0
assert (p+q) % M == S

# After independently recovering each valid z from the hash/XOR layer:
primes = [p, q, r]
for z in z_candidates:
    roots2 = [Zmod(pr)(z).nth_root(e2, all=True) for pr in primes]
    for rr2 in itertools.product(*roots2):
        v = ZZ(CRT(list(map(ZZ, rr2)), primes))
        if power_mod(v, e2, N) != z:
            continue

        u = (v - p - q) % N
        roots1 = [Zmod(pr)(u).nth_root(e1, all=True) for pr in primes]
        for rr1 in itertools.product(*roots1):
            m = ZZ(CRT(list(map(ZZ, rr1)), primes))
            if power_mod(m, e1, N) != u:
                continue
            if verify_full_construction(m):
                print(m)
```

The skeleton intentionally leaves `X_bound`, `beta`, `epsilon`, `z_candidates`, encoding and the full verifier challenge-specific.

---

## 14. What to record in PROGRESS.md

Record:

```text
exact construction equations
factor count and bit lengths
all leaked residues/congruences
how each new residue was derived
cheap-factor method and factor identity proof
arithmetic progression for the partial factor
Coppersmith polynomial + X/beta/epsilon
hash/XOR fixed-point equation and candidate count
root count per prime for each exponent layer
CRT candidate count
full forward-verification result
```

This makes the solve reproducible and exposes where a wrong branch entered.

---

## 15. Routing signals

Route here when several of these occur together:

```text
N = p*q*r or multi-prime RSA-like modulus
low bits of multiple factors leaked
factor residues modulo 2^k
(p+q) mod M or another auxiliary factor congruence
ECM recovers one factor but not the whole construction
partial factor becomes an arithmetic progression
Coppersmith against a remaining cofactor
truncated hash XOR fixed point around modular value
multiple modular e-th roots per prime
CRT root enumeration after factorization
```

If the challenge is merely standard partial-prime Coppersmith, use `references/rsa-lll-patterns.md` instead. Use this focused reference when the **composition of leaks, factor peeling, fixed-point layer and modular-root tree** is the decisive difficulty.
