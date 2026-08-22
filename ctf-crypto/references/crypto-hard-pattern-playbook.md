# Crypto hard-pattern playbook

Reusable decision trees from SekaiCTF 2025 zero/near-zero crypto patterns. Use when normal RSA/AES/ECC checklists do not fit and the challenge has implementation-defined crypto, post-quantum/MQ signatures, or chosen permutations.

## 1. Invalid EC point / exceptional-formula checklist

Use for threshold ECDSA, FROST, Schnorr multi-signatures, custom EC libraries, and any protocol accepting user-supplied points.

Red flags:
- User supplies public keys, commitments, nonce points, shares, or proof points.
- Parser only bounds `x,y` or rejects `(0,0)`; no curve equation check.
- No subgroup/order check or cofactor clearing.
- Equality is implemented indirectly, e.g. `P == Q` as `(P + -Q).x == 0`.
- Library uses optimized Jacobian/projective formulas with exceptional cases.

Workflow:
1. Reproduce the implementation's exact point operations, not the abstract group.
2. Search for accepted points that are:
   - not on the curve,
   - singular/degenerate,
   - low order/small subgroup,
   - exceptional for addition/doubling formulas,
   - alternative encodings of infinity.
3. Build symbolic equations over the implementation field `GF(p)` for the verifier's checks.
4. Force aggregate public key/commitment equations first; then target the challenge/hash equation.
5. Try zero/known signature shares after collapsing equations with degenerate points.

Quick probes:
```python
# For short Weierstrass y^2 = x^3 + ax + b over p
for x in [0,1,p-1,2,p//2]:
    rhs = (x*x*x + a*x + b) % p
    # test y values even if not sqrt(rhs) if parser accepts raw coords
```

Validation tests to add locally:
- Does parser reject non-curve points?
- Does `P + (-P)` produce a canonical infinity?
- Does `P == Q` behave correctly for invalid points?
- Does multiplying invalid `P` by group order return infinity or weird coordinates?

Pitfall: do not stop at “cryptographically impossible.” Many CTF EC bugs live exactly at the mismatch between paper group law and implementation formulas.

## 2. UOV/MQ signature forgery triage

Use for UOV/Rainbow/MQ signature challenges, especially ring or aggregate verification.

Recognition:
- Public map outputs `m` bytes/elements from many variables.
- Verification checks `pubmap(sig, pk) == H(msg)` or XOR/sum of multiple pubmaps equals target.
- There are far more variables than equations.
- Seeds deterministically expand public keys, so verifier exposes enough structure.

Attack decision tree:
1. Count variables vs equations.
   - If variables >> equations, model as underdetermined MQ system.
2. Look for UOV shape: vinegar variables make equations linear in oil variables after assignment.
3. For ring/aggregate verification, combine all public maps before solving; XOR over GF(2^8) is addition.
4. Choose all but one block/participant randomly, compute residual target, then solve last block if possible.
5. If direct last-block solve fails, distribute residual over multiple blocks and linearize oils in each block.
6. Use the implementation's GF packing/unpacking exactly; endian/field representation mistakes dominate failures.

Minimal solver skeleton:
```python
# Pseudocode
for attempt in range(N):
    sigs = [random_block() for _ in range(ring_n)]
    residual = target
    for i in range(ring_n-1):
        residual ^= pubmap(sigs[i], pk[i])
    # assign vinegar for last block, derive linear system in oils
    oils = solve_linearized_uov(pk[-1], vinegar, residual)
    if oils:
        sigs[-1] = pack(vinegar, oils)
        assert xor(pubmap(s,p) for s,p in zip(sigs,pks)) == target
        break
```

Pitfalls:
- `pickle`/Python integer packing may hide GF element order; inspect `gf_unpack`/`gf_pack`.
- UOV implementations often pack triangular matrices; reconstruct correctly before equation building.
- Full Groebner on all variables is usually worse than exploiting UOV linearization.

## 3. Chosen permutation -> projective/Mobius recovery

Use when oracle lets you choose a permutation/S-box and the secret key repeatedly indexes through it.

Recognition:
- You control a permutation `P` over 2^n elements.
- Encryption does repeated `state = P[state xor/add key_i]` or similar.
- Output is a permutation or many encrypted indices.
- Domain can be interpreted as `GF(2^n)`.

Core trick:
- Choose `P(x) = x^-1` over `GF(2^n)` with a special value for zero/infinity.
- The sequence `x -> 1/(x+k)` is a Mobius/projective transformation on `P^1(F)`.
- A repeated keyed walk becomes a 2x2 projective matrix.
- Recover that matrix from observed input/output pairs, then reconstruct key bytes from the induced cycle/action.

Workflow:
1. Implement GF arithmetic matching the challenge's byte representation.
2. Submit inverse permutation as chosen plaintext/permutation.
3. Lift observed permutation to projective points `(x:1)` plus infinity.
4. Solve for a 2x2 matrix up to scalar using linear equations from input/output pairs.
5. Use cycles/orbits containing infinity to recover key components.
6. Repeat if the attack has a favorable-cycle probability.

Pitfalls:
- GF polynomial/representation mismatch ruins everything; verify inverse table with known test pairs.
- Projective matrices are up to scalar; normalize before comparing.
- Some solves are probabilistic. Keep retry loops and estimate success probability before hitting remote.

## 4. Hard crypto note template

For future rare crypto finds, record:
- Exact primitive family and why standard assumptions failed.
- Input controlled by attacker.
- Verification equation in implementation terms.
- Variable/equation count or group/order facts.
- Minimal reproducible solver idea, not just final script.
- Representation pitfalls: endian, field polynomial, point encoding, exceptional cases.
