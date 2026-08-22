# how2heap — Per-glibc-version heap exploitation reference

Source: https://github.com/shellphish/how2heap (cloned to `/tmp/upgrade-2026-06-22b/how2heap`)

This repo tracks how each heap technique works (or breaks) across glibc versions 2.23 → 2.43. **Critical because heap exploitation is glibc-version-specific**: a technique that works on 2.35 silently fails on 2.39, with no compiler warning. Always check `glibc_X.YY/<technique>.c` for your challenge's glibc before committing to a primitive.

Repo structure: each `glibc_X.YY/` directory has working `.c` files. Each `.c` file is a self-contained demo (compile with `gcc -o demo <file>.c` then run; many have a `:arrow_forward:` link to debug in-browser via wargames.ret2.systems).

---

## 1. The patch-tracking system (USE THIS FIRST)

Every technique `.c` file links to the glibc patch that introduced (or broke) the technique. Example: `tcache_poisoning.c` cites the patch that added tcache padding requirement AND the patch that added safe-linking.

**Workflow when starting a heap challenge:**
1. Identify the remote glibc version (`strings ./libc.so.6 | grep 'GNU C Library'` or `libc-database` lookup).
2. Open the relevant `glibc_X.YY/*.c` file in how2heap.
3. Read the comments at top — they say which patches affect this technique.
4. Adjust your exploit accordingly (often: add padding allocation, add XOR obfuscation, add alignment check).

**Why this matters more than writeups:** writeups are typically glibc-specific. How2heap abstracts across versions.

---

## 2. tcache_poisoning (modern — requires heap leak + safe-linking bypass)

**Pattern:** same as classic tcache poisoning (corrupt `chunk->fd` to point at target), but on glibc ≥ 2.32 you need:
1. **Heap address leak** (to defeat safe-linking — see below).
2. **One extra malloc before the corrupted chunk returns** (post-2.32 patch added a "padding" requirement — see comments).
3. **Alignment check** — target address must be 16-byte aligned (post-2.32 patch).

**Safe-linking XOR (glibc ≥ 2.32):**
```c
#define PROTECT_PTR(pos, ptr) \
  ((__typeof (ptr)) ((((size_t) pos) >> 12) ^ ((size_t) ptr)))
#define REVEAL_PTR(pos, ptr)  PROTECT_PTR (pos, ptr)
```

Freelist `fd` is stored as `chunk_addr >> 12 ^ target_addr`. So you need chunk_addr (heap leak) to compute the right XOR for target_addr.

**Demo code (from how2heap glibc_2.35/tcache_poisoning.c):**
```c
size_t stack_var[0x10];
size_t *target = NULL;
for(int i=0; i<0x10; i++) {
    if(((long)&stack_var[i] & 0xf) == 0) { target = &stack_var[i]; break; }
}

intptr_t *a = malloc(128);
intptr_t *b = malloc(128);
free(a);
free(b);

// VULN: assume we have a write primitive here
b[0] = (intptr_t)((long)target ^ (long)b >> 12);

intptr_t *c = malloc(128);  // gets `b`'s old chunk back
c = malloc(128);            // gets `target` (stack!)
```

**Tell:**
- glibc ≥ 2.32.
- Have a write-after-free or heap overflow.
- Need to write to arbitrary address (e.g., stack, GOT, hook).

---

## 3. decrypt_safe_linking — recover tcache key from leaked ptr

**Pattern:** if you leak a tcache freelist pointer (e.g., via UAF read or uninitialized memory), XOR it with `chunk_addr >> 12` to recover the next pointer in the chain. Useful when you need to know the next chunk's address without a separate leak.

**Demo (glibc_2.35/decrypt_safe_linking.c, 2156 bytes):**
- Prints heap pointer, XORs with adjacent pointer shifted, recovers next pointer.

**When to use:** during exploitation, when you have one heap leak and need to compute pointer relationships (e.g., "is the next chunk still allocated? where does it go?").

---

## 4. house_of_botcake (glibc 2.26-2.33 — tcache + fastbin overlap)

**Pattern:** free two adjacent chunks into tcache. Free one again into fastbin (by filling tcache first or using `malloc_consolidate`). The fastbin chunk overlaps with the still-tcache-resident chunk. Allocate from fastbin → mutate the overlapping tcache-resident chunk's `fd` → arbitrary write via tcache.

**Why it's elegant:** works even with safe-linking if you can read the original pointer back.

**Tell:**
- glibc 2.26-2.33.
- Adjacent allocations in fastbin size class.
- Want to bypass tcache protections by going through fastbin.

---

## 5. house_of_einherjar (single-byte null off-by-one → overlapping chunks)

**Pattern:** classic off-by-null (e.g., `scanf("%s")` into a 0x100 buffer, missing NUL byte terminator off-by-one clears the LSB of next chunk's prev_size). Set prev_size to span back over your chunk → free triggers backward consolidation → overlapping chunks.

**Pre-req:** glibc < 2.29 doesn't check `prev_size` validity (post-2.29 added `chunksize(p) != prev_size(next_chunk(p))` check, which BREAKS this in standard form).

**Modern variant (post-2.29):** tcache poisoning + house of einherjar combo. Read how2heap `house_of_einherjar.c` comments for the tcache stashing workaround.

**Tell:**
- Off-by-null bug (e.g., `strcpy`, `scanf %s`, missing NUL on custom string format).
- glibc 2.26-2.33 (for the basic technique).

---

## 6. large_bin_attack (write a heap address to an arbitrary location)

**Pattern:** sort a chunk into largebin (size ≥ 0x400). Trigger another insertion into the same largebin. During insertion, `bin->bk` gets overwritten with `unsorted_bin_head + offset` — i.e., a heap pointer leaks to an arbitrary location you choose.

**Use case:** overwrite `_IO_list_all` or `mp_.tcache_bins` with a heap address to enable further exploitation.

**Pre-req:** glibc 2.26-2.29 (patched in 2.30 to check the insertion target).

**Tell:**
- Can allocate large chunks (≥ 0x400).
- Want to write a heap pointer somewhere controllable.

---

## 7. tcache_stashing_unlink_attack (smallbin + unsorted bin → arbitrary allocation)

**Pattern:** fill tcache for a size, free a chunk into unsorted bin (not fastbin, not tcache). Trigger `malloc_consolidate` or wait for the next malloc that pulls from smallbin. The chunk's `bk` is dereferenced to populate the tcache freelist — control `bk` to make tcache return an arbitrary address.

**Tell:**
- glibc 2.26-2.31.
- Have unsorted bin chunks that could be moved to smallbin.
- Need arbitrary allocation (e.g., into `_IO_list_all`, into stack via stack address leak).

---

## 8. house_of_water / house_of_tangerine (heap address leak without free)

**Pattern:** force `sysmalloc` (out-of-memory path) which leaves heap metadata in tcache pointers without requiring a free. Read the tcache pointer to get heap base leak.

**When to use:** when the program never frees but you still need a heap leak.

**Tell:**
- Tight memory budget (close to `RLIMIT_AS`).
- Can trigger OOM conditions.

---

## 9. mmap_overlapping_chunks (chunk shrink via mmap)

**Pattern:** force an mmap allocation, then have it overlap with existing heap chunks via careful size manipulation. The mmap chunk's pages become part of the heap address space.

**Use case:** cross-cache contamination — read/write between mmap and heap regions.

**Tell:**
- Can trigger mmap allocations (e.g., large `malloc`).
- Memory layout is sparse.

---

## 10. tcache_relative_write (write-relative, glibc ≥ 2.34)

**Pattern:** post-glibc-2.34, the safe-linking protection makes tcache poisoning more complex. `tcache_relative_write.c` (11694 bytes — largest in the repo) demonstrates the modern bypass: abuse the fact that `fd` XOR doesn't protect against writes to chunks whose address is *known-relative* to the chunk you're corrupting.

**Demo mechanism:** control a chunk's contents, then use a UAF on a chunk at `chunk + delta` to write `delta` away via tcache fd manipulation.

**Tell:**
- glibc ≥ 2.34.
- Have UAF + adjacent chunk control.

---

## Glibc version compatibility quick map

| Technique | First works | Breaks at | Modern variant |
|-----------|-------------|-----------|----------------|
| `fastbin_dup` | always | 2.43 (still works <2.43) | use tcache_dup instead |
| `tcache_dup` | 2.26 | 2.29 (key check) | bypass via padding |
| `tcache_poisoning` | 2.26 | 2.32 (safe-linking) | needs heap leak + XOR |
| `house_of_botcake` | 2.26 | 2.34 (tcache per-thread) | tcache + fastbin hybrid |
| `house_of_einherjar` | 2.26 | 2.29 (prev_size check) | tcache stashing variant |
| `unsafe_unlink` | always | 2.26 (fd/bk checks) | rarely useful now |
| `large_bin_attack` | always | 2.30 (insertion check) | limited to 2.26-2.29 |
| `tcache_stashing_unlink_attack` | 2.29 | 2.32 (safe-linking) | still partially works |

**Always check the patch link in the .c file comment for your specific glibc.**

---

## How to use this repo in a CTF

```bash
# 1. Identify glibc version
$ strings ./libc.so.6 | grep -oE 'GLIBC [0-9]+\.[0-9]+' | head -1
GLIBC 2.35

# 2. List available techniques
$ ls how2heap/glibc_2.35/*.c

# 3. Read the technique you want — comments at top tell you about patches
$ head -30 how2heap/glibc_2.35/tcache_poisoning.c

# 4. Compile and run locally
$ gcc -g -o /tmp/demo how2heap/glibc_2.35/tcache_poisoning.c
$ /tmp/demo

# 5. Adapt for your challenge's heap layout / glibc mitigations
```

**Debugging tool:** wargames.ret2.systems (linked from each `.c` file as `:arrow_forward:`) — runs the technique in a browser with gdb attached. Useful when local glibc doesn't match.
