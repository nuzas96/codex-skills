# Reused Stream Keystream / Two-Time Pad

Use this focused reference when two or more ciphertexts reuse the same stream-cipher keystream. Common causes include AES-CTR nonce reuse under the same key, OTP/key reuse, repeated RC4-style state, or a custom XOR stream that resets.

## Recognize

Strong signals:

- two AES-CTR records share the same nonce/IV under the same key context;
- two XOR/OTP ciphertexts were encrypted with the same pad/key stream;
- the construction implies identical keystream bytes at the same offsets;
- XORing ciphertexts removes encryption structure and yields a plausible plaintext-vs-plaintext relation.

For aligned ciphertexts:

```text
C1 = P1 XOR K
C2 = P2 XOR K

C1 XOR C2 = P1 XOR P2
```

This proves keystream reuse, but it does **not** by itself reveal either plaintext.

## First solve workflow

1. Confirm that the same keystream really applies at the same offsets. For CTR, verify same key context and nonce/counter semantics rather than assuming every repeated-looking field is sufficient.
2. XOR the ciphertexts over their shared length and preserve the result.
3. Search supplied source/artifacts for genuine known plaintext, fixed protocol headers, message templates, filenames, JSON prefixes, timestamps, or other structural anchors.
4. Use a known plaintext segment to recover keystream bytes, then decrypt the paired ciphertext at the same offsets.
5. If no real known plaintext exists, crib-drag short **evidence-backed** words/structures and score the counterpart for structure/language. Prefer protocol/message structure over arbitrary flag-body guesses.
6. Extend only cribs that produce mutually plausible plaintext on both sides. Record rejected cribs so the solve does not loop.
7. Validate recovered plaintext against the original ciphertext relation before treating it as real.

## Flag-format discipline

A known flag format such as `CTF{...}` can be used as a **constraint or scoring signal**, not as replacement plaintext.

Good use:

- test whether a flag prefix at a candidate offset yields a plausible paired protocol/header string;
- use the prefix to recover a few keystream bytes and then demand independent structure to extend them;
- reject a candidate when the paired plaintext becomes impossible/nonprintable or contradicts known structure.

Bad use:

- guessing the flag body from theme words;
- treating printable output alone as confirmation;
- accepting a prefix alignment merely because the other plaintext begins with printable ASCII.

If every position still admits many printable candidates, the crib is underconstrained. Switch to stronger message structure, additional ciphertexts, known plaintext, or a better joint-language model rather than enumerating arbitrary flag suffixes.

## Crib dragging skeleton

```python
def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def crib_drag(c1, c2, crib):
    x = xor_bytes(c1, c2)
    for pos in range(0, len(x) - len(crib) + 1):
        paired = xor_bytes(x[pos:pos + len(crib)], crib)
        yield pos, paired
```

For each candidate, score both sides using actual challenge structure. ASCII printability is only a weak filter.

## Common failure modes

- **Wrong CTR semantics:** same nonce value does not help if the key differs; custom counter construction may shift alignment.
- **One-sided scoring:** a guessed phrase looks good on one plaintext but makes the paired plaintext nonsense.
- **Theme guessing:** trying likely flag suffixes before exhausting structural plaintext evidence.
- **Weak statistical model:** independent byte-frequency scoring often produces printable gibberish because natural language dependencies are ignored.
- **Premature defeat:** if the primitive is confirmed but plaintext recovery is underconstrained, preserve the primitive and continue through `ctf-solve` stuck recovery; do not invalidate the nonce-reuse finding.

## Completion

A successful solve should preserve:

- which ciphertexts reused the keystream;
- exact alignment/shared length;
- the known plaintext or crib that became independently validated;
- recovered keystream/plaintext bytes;
- a local verification that recomputes the XOR relation.

## Provenance

This focused reference consolidates existing V2 knowledge already present in:

- `ctf-crypto/modern-ciphers.md` — CTR/GCM nonce-reuse keystream relation;
- `ctf-crypto/classic-ciphers.md` — OTP/many-time-pad known-plaintext and crib-dragging workflow.

It was promoted into a focused route after CTF Racer benchmark traces showed that the knowledge existed but was not being selected early enough by the V2 routing path.
