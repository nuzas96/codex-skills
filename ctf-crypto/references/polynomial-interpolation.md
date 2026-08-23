# Fast Polynomial Interpolation and Vandermonde Recovery

Use this reference when a challenge gives many pairs `(x_i, y_i)` over a finite field/ring and the target is the coefficients of the unique polynomial

```text
f(x) = a_0 + a_1 x + ... + a_{n-1} x^(n-1)
```

such that `f(x_i) = y_i`.

## Recognize

Strong signals:

- source constructs rows `[1, x, x^2, ..., x^(n-1)]`;
- a Vandermonde matrix is passed to a generic linear solver;
- coefficients are later serialized as bytes, pixels, key material, or another artifact;
- all `x_i` are distinct modulo the field modulus;
- the number of points is large enough that explicitly building an `n x n` matrix is impossible;
- evaluation points are consecutive or otherwise structured, for example `0, 1, 2, ...`.

The mathematical primitive is **polynomial interpolation**, not generic linear algebra.

## Primitive

Given distinct points `(x_i, y_i)` modulo `p`, recover the unique degree `< n` polynomial `f` satisfying

```text
f(x_i) = y_i  (mod p)
```

The Vandermonde system and the interpolation problem are equivalent, but the interpolation structure admits much faster algorithms.

## Complexity triage

Avoid choosing an algorithm before estimating `n`.

| Method | Typical cost | Use when |
|---|---:|---|
| Explicit Vandermonde + generic solve | `O(n^2)` memory, about `O(n^3)` work | almost never beyond tiny `n` |
| Naive coefficient-form Lagrange/Newton | about `O(n^2)` | small inputs only |
| Product/subproduct-tree interpolation | about `O(M(n) log n)` to `O(n log^2 n)` depending on multiplication backend | large inputs |
| Optimized native library such as FLINT | implementation-dependent, usually the best first choice for huge machine-word-modulus inputs | hundreds of thousands to millions of points |

`M(n)` is the complexity of multiplying degree-`n` polynomials.

## Solve workflow

1. **Write the exact ring/field.** Record modulus, point count, coefficient order, and target serialization.
2. **Verify uniqueness assumptions.** Ensure all `x_i` are distinct modulo the modulus and required denominator differences are invertible.
3. **Determine what is actually needed.** If the challenge only needs `f(z)` at one point, do not recover every coefficient. If it serializes the coefficients, full interpolation is required.
4. **Reject the matrix formulation for large `n`.** Do not materialize the Vandermonde matrix.
5. **Choose by scale.** Use ordinary interpolation for small cases; switch to product-tree / fast multipoint algorithms or an optimized library for very large cases.
6. **Recover coefficients in the expected order.** Most polynomial libraries expose coefficients low degree first, but verify this before serializing.
7. **Validate locally.** Re-evaluate the recovered polynomial at several supplied points before trusting the output artifact.
8. **Validate representation separately.** Confirm byte range, endianness, dropped padding coefficients, file magic, or any other target-specific encoding.

## FLINT fast path

For a modulus that fits FLINT's `nmod` representation, check the native interpolation routine:

```text
nmod_poly_interpolate_nmod_vec_fast
```

This is preferable to translating a million-point problem into Python/Sage-level loops when the target fits the API.

Before using it, confirm:

- the modulus semantics match the challenge;
- all evaluation points are valid and distinct modulo the modulus;
- the routine returns the full coefficient polynomial in the expected coefficient order;
- enough memory is available for the input/output vectors and product-tree workspace.

For challenge-sized datasets, library overhead is usually far smaller than the cost of a generic matrix solve.

## Divide-and-conquer model

A useful mental model is to split the points into two halves and build zero polynomials

```text
Z_1(x) = product(x - x_i) over the first half
Z_2(x) = product(x - x_i) over the second half
```

Then represent

```text
f = f_1 Z_2 + f_2 Z_1
```

so each half-size interpolation can be solved recursively after dividing the target values by the opposite zero polynomial evaluated at the corresponding nodes.

Fast implementations use product trees, remainder trees, and fast polynomial multiplication to avoid quadratic work.

## Consecutive-node caution

Consecutive points such as `x_i = i` are useful structure, but they do **not** automatically make naive coefficient recovery cheap. A direct Lagrange/Newton implementation that repeatedly manipulates full coefficient arrays can still be quadratic.

Use the structure only when the chosen algorithm/library exploits it efficiently.

## Pitfalls

- **Do not build the Vandermonde matrix** just because the supplied source does.
- **Do not call a generic linear solver** on a structured interpolation problem at large scale.
- **Do not assume Lagrange means fast.** The textbook formula can still become `O(n^2)` when recovering all coefficients.
- **Do not confuse evaluation with coefficient recovery.** Barycentric interpolation can evaluate efficiently without necessarily giving every coefficient cheaply.
- **Check modulus/inverses.** Duplicate nodes modulo the modulus or non-invertible differences can invalidate ordinary field interpolation assumptions.
- **Check coefficient serialization.** A challenge may intentionally drop a trailing coefficient or encode only a prefix.
- **Verify the artifact.** File magic or a known format is a stronger final check than visually plausible bytes.

## Source / provenance

Reusable pattern harvested from **picoCTF 2024 — `flag_printer`** after observing a supplied program that built a Vandermonde system over a finite field and attempted a generic solve on about 1.77 million points.

A public solution by PetePriority documents the same reduction from Vandermonde solving to polynomial interpolation, a divide-and-conquer `O(n log^2 n)`-style approach, and the much faster FLINT `nmod_poly_interpolate_nmod_vec_fast` implementation:

- https://github.com/PetePriority/picoctf-2024/tree/main/cryptography/flag_printer
- https://github.com/PetePriority/picoctf-2024/blob/main/cryptography/flag_printer/README.md

Harvested: 2026-08-23.

The permanent lesson is the **recognition and scale-aware algorithm choice**, not the challenge flag or dataset-specific constants.
