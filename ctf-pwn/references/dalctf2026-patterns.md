# DalCTF2026 — Pwn Patterns

Source: https://github.com/DalCTF/DalCTF2026

---

## 1. Flush+Reload cache side-channel (pwn/toilet-simulator)

**Pattern:** victim process owns a secret (e.g. flag file you can't read directly). It accesses one of two shared memory pages depending on the value of each secret *bit*. Attacker shares the same physical page and times its own `clflush` + reload to determine which page the victim touched.

**Per bit:**
1. `clflush` both probe pages out of cache.
2. Let the victim run.
3. Read each probe page → measure load latency with `rdtsc`/`rdtscp`.
4. Cache-hit page = the bit's value.

**Sample multiple times per bit, majority-vote** to denoise.

**Challenge signature:** ssh to a container, root-only file, victim process running as a different user, hint about "shared memory" / "two pages" / "semaphores".

**Caveat:** needs same physical page (shared mmap). Modern CPU mitigations may interfere — CTF setups are usually intentionally vulnerable.

---

## 2. MP4 uuid box buffer overflow → shellcode in video (pwn/video-killed-the-pwn-star)

**Pattern:** video-processing C binary parses MP4 atoms. `parse_uuid_raw()` trusts the `size` field of the `uuid` box without checking → buffer overflow.

**Conditions:**
- NX disabled → can execute shellcode from the buffer itself.
- PIE enabled → full addresses randomised, but **partial overwrite** on the return address (low 1-2 bytes) only has ~1/16 to ~1/4096 entropy. Submit the same video repeatedly until it works.

**Exploit:**
1. Craft an MP4 where the `uuid` box's *data* IS your shellcode.
2. Submit → parser overflows, ret address lands in your buffer.
3. PIE partial overwrite → ~1/16 success rate; retry until it hits.

**Recognise:** video/audio/image parser exposed via HTTP in C/C++. Check `uuid`, `free`, `skip`, `mdat` atom handlers.
