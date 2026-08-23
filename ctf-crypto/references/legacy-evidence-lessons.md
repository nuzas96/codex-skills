# Legacy Evidence Lessons

Load when a mathematically plausible attack still needs exact proof or robust oracle transport.

- For low-exponent RSA, require an exact integer root and verify `m^e == c` before decoding.
- Test close primes with Fermat and partial-prime leakage with the appropriate small-root method; always confirm `p*q == n`.
- For PRNG-to-RSA chains, verify predicted generator outputs before collecting CRT samples and require an exact final root.
- For smooth-order ECC, solve subgroup logs, combine with CRT, and verify the recovered scalar by multiplying the generator.
- Classify padding-oracle responses explicitly, including disconnect/EOF, normal responses, false positives, and final-byte ambiguity.
- Derive XOR/known-plaintext keys only from explicit artifacts and validate decrypted structure before flag scanning.
- Preserve raw binary plaintext when it is not readable; do not force text or infer a flag.

