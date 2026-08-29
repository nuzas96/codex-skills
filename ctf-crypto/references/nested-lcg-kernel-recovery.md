# Nested LCG recovery with short kernels and resultants

Use this pattern when observed values come from one linear congruential generator whose additive term is itself the state/output of another LCG, especially when both moduli and multipliers are secret.

## Recognize

Strong signals:

- Source contains two chained recurrences such as
  `u[n+1] = a*u[n] + b (mod p)` and
  `y[n+1] = A*y[n] + u[n+1] (mod P)`.
- Only the outer sequence `y[n]` is printed.
- Both `p` and `P` are unknown primes/moduli.
- There are roughly 10-20 consecutive outer observations: too few for blind high-dimensional symbolic solving, but enough to expose short linear recurrences.
- Ordinary single-LCG modulus recovery on `y` or its first differences fails because the increment is not constant.
- The inner state may be wider than the outer modulus, so reduction through `P` hides an extra small quotient rather than destroying all structure.

Do not flatten this immediately into a standard LCG. The varying inner increment is the primitive.

## Construction

Write the exact recurrence first. A common form is

```text
u[i+1] = a*u[i] + b        (mod p)
y[i+1] = A*y[i] + u[i+1]   (mod P)
```

Define first differences

```text
dy[i] = y[i+1] - y[i]
```

The hidden inner LCG implies that suitable short integer linear combinations of consecutive `dy` values are unusually small / structured. A lattice basis for the right kernel of an overlapping-window matrix can expose these relations.

## Recovery workflow

### 1. Difference the observed outer sequence

```sage
from sage.all import *

dy = vector(ZZ, obs[1:]) - vector(ZZ, obs[:-1])
```

Using differences removes the outer seed offset and makes the hidden recurrence easier to isolate.

### 2. Build overlapping windows and find short right-kernel vectors

For `m` consecutive differences, form several shifted rows of the same window length. Example shape:

```sage
w = 11
rows = 3
Y = matrix(ZZ, rows, w)
for i in range(rows):
    Y[i] = vector(dy[i:i+w])

short_kernel = Y.right_kernel_matrix().LLL()
```

The exact window size is target-derived. Keep enough columns that the right kernel has dimension, then LLL-reduce it. Do not assume every reduced row is useful: very short trivial relations may need to be discarded.

### 3. Interpret short kernel rows as polynomials

For a short kernel vector `r = (r0,...,r{k})`, build

```text
R_r(x) = r0 + r1*x + ... + rk*x^k
```

The hidden inner multiplier `a` is a common root modulo the inner modulus `p`. Therefore resultants of independent relation polynomials share `p` as a factor.

```sage
R.<x> = PolynomialRing(ZZ)
polys = [sum(row[i] * x^i for i in range(len(row))) for row in useful_rows]

candidate = gcd(polys[0].resultant(polys[1]),
                polys[1].resultant(polys[2]))
```

Factor the GCD and select factors consistent with the source-derived modulus bit length. Never choose a factor only because it decrypts to printable text.

### 4. Recover the inner multiplier

Move two independent relation polynomials to `GF(p)`. Their polynomial GCD contains the common root `a`.

```sage
f0 = polys[0].change_ring(GF(p))
f1 = polys[1].change_ring(GF(p))
roots = gcd(f0, f1).roots(multiplicities=False)
```

Validate candidate roots by reconstructing later relations; do not stop at the first algebraic root if multiple candidates exist.

### 5. Lift the kernel to isolate hidden inner-difference terms

The first kernel recovers recurrence relations, not yet the hidden `u[i]` values. Build a shifted stacked matrix from the short-kernel rows: prepend and append zeros to express the same relation at adjacent offsets.

```sage
M = matrix(ZZ, 0, len(dy)-1)
for row in useful_rows:
    M = M.stack(matrix(ZZ, [[0] + list(row)]))
    M = M.stack(matrix(ZZ, [list(row) + [0]]))

K2 = M.right_kernel_matrix().LLL()
```

Scale / orient the second kernel using the observed differences, then combine it with the geometric vector

```text
1, a, a^2, ...
```

to recover a centered representative of the hidden inner-difference sequence. This is the subtle stage: kernel vectors are only defined up to scale and lattice basis choice, so verify the resulting sequence against all observations.

### 6. Recover the outer modulus from corrected differences

Once hidden inner-difference corrections `dx[i]` are available, relations of the form

```text
dy[i+1] - dx[i] = A * dy[i]    (mod P)
```

hold. Eliminate `A` between adjacent equations:

```text
g_i = dy[i]   * (dy[i+2] - dx[i+1])
    - dy[i+1] * (dy[i+1] - dx[i])
```

Then

```text
P | gcd(g_0, g_1, ...)
```

Factor the GCD and select the factor matching the expected outer-modulus size.

### 7. Recover the outer multiplier and initial state

With `P` known,

```text
A = (dy[i+1] - dx[i]) / dy[i]  (mod P)
```

Then use the first outer recurrence to recover the original seed/key. Be careful when an inner value was reduced through both `p` and `P`: two centered/lifted representatives can differ by `p`. Test algebraically valid lift candidates and validate the recovered key against the original encryption relation.

## Why standard LCG recovery fails

For a normal LCG,

```text
x[n+1] = A*x[n] + C (mod M)
```

second-order determinant-style expressions are multiples of one fixed modulus because `C` is constant. Here the increment is itself evolving modulo another secret modulus, so those invariants are contaminated.

The fix is not “more brute force.” Recover the hidden recurrence first using short integer relations.

## Practical heuristics

- Start with first differences before invoking symbolic solvers.
- With about a dozen observations, try overlapping-window right kernels before large generic lattices.
- LLL is being used to find **short recurrence relations**, not as a black-box secret finder.
- Resultants convert “same unknown modular root” into an integer divisible by the hidden modulus.
- Use source-known bit lengths to rank resultant/GCD factors.
- If the inner modulus is wider than the outer modulus, explicitly track the possible quotient/lift ambiguity.
- Validate every recovered modulus, multiplier and state against all printed observations before decrypting.

## Pitfalls

- Treating the printed sequence as a single LCG and repeating standard modulus-recovery formulas.
- Running generic LLL without first identifying what a short vector represents.
- Using too few independent kernel polynomials: a single resultant often carries many irrelevant factors.
- Assuming the first right-kernel basis row is meaningful before LLL reduction.
- Ignoring scale/sign ambiguity in the second kernel.
- Losing the distinction between equality over `ZZ`, congruence modulo `p`, and congruence modulo `P`.
- Accepting ASCII plaintext as the only verification; reconstruct the PRNG sequence too.

## Source / provenance

Technique harvested from the official SekaiCTF 2026 `orbital-strike` challenge and solver after a blind V2 evaluation exposed the missing nested-LCG pattern.

- Source repository: `nuzas96/sekaictf-2026-cuba`
- Challenge source: `crypto/orbital-strike/challenge/chall.py`
- Official solver studied: `crypto/orbital-strike/solution/solve.sage`
- Harvest date: 2026-08-29

This reference generalizes the recurrence/kernel/resultant method and intentionally omits challenge-specific constants and flag material.
