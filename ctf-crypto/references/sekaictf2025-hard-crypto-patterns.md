# SekaiCTF 2025 zero/near-zero crypto patterns

Source: `project-sekai-ctf/sekaictf-2025` second pass, focused on 0-3 solve challenges.

## Law and Order — malicious FROST participant via invalid curve/singular point semantics

Observed files: `crypto/law-and-order/dist/chall.py`, `crypto/law-and-order/solution/solve.py`.

Pattern:
- Threshold ECDSA/FROST-style protocols that accept user-supplied EC points must validate that every point is on the intended curve and in the intended subgroup.
- Here `input_point()` only rejects `(0,0)` and bounds coordinates; `Point.__eq__` treats equality as `(P + -Q).x == 0` through `py_ecc`, not as strict tuple equality.
- The solver constructs commitments/nonces on degenerate/singular-looking points (`x=0`, chosen `y`) and uses polynomial equations over `GF(p)` to force accepted proof/share equations while making the aggregate public key and challenge collapse modulo a small factor.
- The final signature-share check is bypassed by choosing nonce points so that the group challenge has the required residue and sending `z_i = 0`.

Recognition checklist:
1. User controls EC commitments, public keys, nonce points, or verification shares.
2. Code lacks explicit curve-membership validation and subgroup/order checks.
3. Equality is implemented indirectly via addition/infinity checks.
4. Verification formulas use Jacobian/projective formulas that assume non-degenerate inputs.

Exploit sketch:
- Model the verifier's exact point formulas symbolically over `GF(p)` rather than over the abstract EC group.
- Search for low-order/degenerate points accepted by the library/formula boundary.
- Force aggregate commitment/public share relationships first, then pick signing nonces that make challenge residues compatible with a zero or known signature share.

Pitfall: do not reason only from the cryptographic paper. Reproduce the implementation's exceptional cases (`add`, `multiply`, equality, point-at-infinity encoding) exactly.

## unfairy-ring / unfairy-ring++ — UOV ring XOR target without a signer secret

Observed files: `crypto/unfairy-ring/dist/chall.py`, `crypto/unfairy-ring-plusplus/dist/chall.py`, `dist/uov.py`.

Pattern:
- Ring verification accepts concatenated UOV signature blocks and XORs the public-map outputs: `xor(pubmap(sig_i, pk_i)) == shake256(msg, 44)`.
- Public keys are deterministic from anime-name seeds (`shake256(name, 43576)`), and there is no per-member secret in the verifier.
- Each block has 112 GF(256) variables and only 44 output bytes/equations. Treat the whole ring as one underdetermined multivariate quadratic system, not as independent signature verification.

Triage route:
1. Parse `uov.pubmap`: variables split into vinegar `v=68` and oil `m=44`; output includes P1(v,v), P2(v,o), P3(o,o).
2. Because XOR in GF(256) is addition, combine all member pubmaps into one target system.
3. Try fixing many variables randomly and solving the remaining linearized/quadratic system; for UOV-shaped maps, choose variables so one block becomes linear in oils after vinegar assignment.
4. If direct solve is too large, use the original UOV signing method as a guide: random vinegar assignment reduces one public map to linear equations in oils. The ring XOR lets you absorb residual target with the last block.

Why valuable: even without a full solve script in the repo, this is a strong recognition pattern for post-quantum/MQ CTF challenges: a signature-looking verifier may actually expose a many-variable public map where ring aggregation turns forgery into underdetermined equation solving.

## APES — chosen permutation encryption as projective-line recovery

Observed files: `crypto/apes/dist/chall.py`, `crypto/apes/solution/solve.sage`.

Pattern:
- The oracle encrypts a chosen permutation by iterating `i = plainperm[i ^ k]` for 64 key bytes, then xors the final key byte.
- The solve chooses `plainperm[i] = i^-1` over `GF(256)`, lifting the transform into a projective/Mobius action on `P^1(F_256)`.
- From one lucky ciphertext permutation, build a linear system over pairs `(a,b)` and recover a 2x2 projective matrix from a high-zero kernel vector.
- Use the resulting projective permutation cycle containing infinity to reconstruct enough key bytes.

Recognition checklist:
- Challenge permits chosen permutation/S-box input.
- Repeated key mixing alternates XOR/addition-like operations with attacker-selected nonlinear permutation.
- A field inverse permutation often linearizes the system into PGL/Mobius transformations.

Pitfall: the provided solve uses a probabilistic favorable-cycle condition (~1/5549 attempts). If adapting to remote, keep the retry loop and rate limits in mind; there may be better success-rate variants, but the core trick is the projective lift.
