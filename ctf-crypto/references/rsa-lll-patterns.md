# RSA-LLL — Lattice-based RSA attacks (Coppersmith + Boneh-Durfee)

Source: https://github.com/mimoo/RSA-and-LLL-attacks (cloned to `/tmp/upgrade-2026-06-22b/rsa-lll`)

This repo contains **production-quality SageMath code** for two lattice-based RSA attacks, plus a survey paper. The `boneh_durfee.sage` (341 lines) and `coppersmith.sage` (227 lines) files are ready to use — just provide your `N`, `e`, `c` (and partial info).

Pre-req: `sage -python script.sage` (SageMath with fpylll). If you don't have Sage, install via `conda install -c conda-forge sage` or use sagemath/sage docker image.

---

## 1. Coppersmith stereotyped messages (partial known plaintext)

**Pattern:** if you know part of the plaintext message (e.g., you know the message starts with `"the password is: "`), recover the rest using Coppersmith's small-root attack on the relaxed RSA problem.

**Relaxed model:**
```
Standard:  c = m^e mod N, find m.
Relaxed:   c = (m + x)^e mod N, you know `m`, find small `x`.
```

**When it works:** Coppersmith says if the unknown `x` is < N^(1/e), you can recover it efficiently via LLL lattice reduction.

**Implementation (from coppersmith.sage, the `coppersmith_howgrave_univariate` function):**

```python
# Suppose message is m = "the password today is: " + unknown_short_password
# And you know m[:-len(unknown)] and have c, e, N.
from coppersmith import coppersmith_howgrave_univariate

known_prefix = int.from_bytes(b"the password today is: ", "big") << (len(unknown)*8)
f = ((m_known + x)^e) - c  # polynomial in x with small root mod N
dd = f.degree()              # = e
beta = 1                     # modulus is N itself (not a factor)
epsilon = beta / 7
mm = ceil(beta^2 / (dd * epsilon))
tt = floor(dd * mm * ((1/beta) - 1))
XX = ceil(N^((beta^2/dd) - epsilon))  # upper bound on root
roots = coppersmith_howgrave_univariate(f, N, beta, mm, tt, XX)
```

**Tuning `XX`:** the bigger the unknown, the bigger XX must be — but LLL time grows fast. Default values work for ~16-byte unknowns with e=65537.

**Tell:**
- Challenge hints about partial plaintext recovery.
- You have e, N, c, and know *most* of the message.
- RSA uses standard padding (Coppersmith breaks many textbook + weak-PKCS#1 schemes).

---

## 2. Coppersmith factoring with high bits known (partial prime leak)

**Pattern:** if you know high bits of one prime (e.g., from a side channel, partial key generation bug, or memory disclosure), recover the full prime via Coppersmith. Then `p = recovered`, `q = N // p`.

**Relaxed model:**
```
Standard:  N = p*q, find p (or q).
Relaxed:   N = (p_approx + x)*q, you know p_approx, find small x.
```

**Implementation:**
```python
# Suppose you know high 50% of p via some leak
beta = 0.5  # we know upper half of bits of q
dd = 1       # f(x) = x - q_approx
epsilon = beta / 7
mm = ceil(beta^2 / (dd * epsilon))
tt = floor(dd * mm * ((1/beta) - 1))
XX = ceil(N^((beta^2/dd) - epsilon)) + 1000000000000000000000000000000000
roots = coppersmith_howgrave_univariate(f, N, beta, mm, tt, XX)
# q_approx + roots[0] = q
q = q_approx + roots[0]
p = N // q
```

**When it works:** Coppersmith requires the unknown portion to be < N^(beta^2/dd). For partial prime (beta=0.5), you need to know >50% of the bits.

**Tell:**
- Key generation has a bug that leaks high bits (e.g., reusing same prime with small entropy, fault attack, hardware bug).
- Side channel exposes partial factor.

---

## 3. Boneh-Durfee small private key (d < N^0.292)

**Pattern:** if the RSA private exponent `d` is small (< N^0.292, much smaller than the standard `d ≈ N^0.5` from Wiener), recover it via Boneh-Durfee's lattice attack (a Coppersmith-like attack for small inverse problems).

**Bounds comparison:**
- Wiener: works for `d < N^0.25` (continued fractions).
- Boneh-Durfee: works for `d < N^0.292` (lattice, ~17% improvement).
- Herrman-May (simplified BD): similar bound, faster.

**Implementation (from boneh_durfee.sage):**
```python
from boneh_durfee import small_roots

# Given e, N (where e*d = 1 mod phi(N), d < N^0.292)
# The polynomial f(x, y) = 1 + x * (A + y) mod e, with:
#   x = -pivot  (a small integer related to k = (ed-1)/(p+q))
#   y = -(p+q)   (another small integer)
# has small roots that recover the private key.

delta = 0.292  # bound on d
m = 4          # lattice dimension (tune for speed/accuracy)
t = int((1-2*delta) * m)
X = 2*floor(N^delta)
Y = floor(N^(1/2))
# Bounds + polynomial definition...
# Run small_roots() — returns x, y → recovers d.
```

**Default vs improved:**
- Set `helpful_only = True` (default) for the author's optimizations (faster convergence on typical inputs).
- Set `helpful_only = False` to use the textbook algorithm.
- `dimension_min = 7` (default) — increase to speed up at cost of success rate.

**Tell:**
- CTF challenge says "small d" or hints at weak private exponent generation.
- `d` looks suspiciously small (e.g., 256-bit when N is 4096-bit).
- `e` is unusually large (Boneh-Durfee works best with large `e`).

---

## 4. Quick-reference decision tree

```
Challenge gives you:    | Try first
------------------------+------------------------
e, N, c + partial m     | Coppersmith #1 (stereotyped)
N + ~half of q          | Coppersmith #2 (factor with high bits)
e + N (no c, no d)      | Boneh-Durfee if e is large
                        | Wiener if e is huge (d < N^0.25)
d leaks but too small   | Already broken by definition
multiple of (p-1) leaks | Pollard p-1 (not lattice)
p,q share many bits     | Fermat factoring (not lattice)
```

---

## 5. Tools you'll need

**SageMath:**
```bash
# Install (Ubuntu/Debian)
sudo apt install sagemath

# Or via conda
conda install -c conda-forge sage

# Run a .sage file
sage boneh_durfee.sage
```

**Sage in Docker (cleanest):**
```bash
docker run -it --rm -v $(pwd):/work sagemath/sagemath sage /work/boneh_durfee.sage
```

**Tunables to experiment with:**
- `m` (lattice dimension) — bigger = slower but more accurate. Try 4-7.
- `t` — depends on `m` and `delta`. Author's calculation in code.
- `X`, `Y` — root bounds. Conservative overestimate usually OK.

---

## 6. Common pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| XX too small | LLL returns wrong vector (no root found) | Increase XX, accept slower run |
| XX too big | LLL hangs / OOM | Reduce XX; ensure you're on the tight bound |
| m too small | Misses small roots | Increase m (try 4, 5, 6) |
| m too big | Slow + numerical instability | Reduce m |
| `helpful_only` interaction | Some roots missed | Toggle `helpful_only` and retry |
| Sage version mismatch | fpylll API change | Use the docker image |
| Time budget | LLL takes hours on big N | Reduce `m`, reduce `XX`, try simpler attack first |

---

## 7. Why this repo is THE go-to

- The author (David Wong) maintains updated versions as new improvements are published.
- `boneh_durfee.sage` includes the latest Herrman-May simplification + personal improvements.
- The survey PDF (`survey_final.pdf`) explains the math background if you want to understand WHY it works.
- Slides (`slides.pdf`, `slides.pptx`) are CTF-friendly — focus on the practical attack flow.

**Alternative repos if you need something different:**
- `defund/coppersmith` — standalone Python impl (no Sage required) for simpler cases.
- `saelo/copperquill` — variant for multi-prime RSA.
- `jhswartz/eccpy` — ECC Coppersmith if your challenge is ECC not RSA.
