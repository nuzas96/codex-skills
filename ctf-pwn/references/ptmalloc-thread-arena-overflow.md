# Cross-width length bugs and multi-thread ptmalloc arena exploitation

Use this pattern when a network/service parser turns an attacker-controlled signed length into an allocation size and a differently sized copy/read length, especially when the service is threaded and glibc arenas are constrained.

## Recognize

Strong signals:

- A signed parser such as `strtoll()` feeds an unsigned `size_t`.
- Allocation arithmetic modifies that value, e.g. `malloc(len + 1)`.
- A later reader/copy helper accepts a narrower type such as `unsigned int`.
- Negative lengths are not rejected before the cast.
- The service is multi-threaded and performs attacker-shaped `malloc`/`free` operations per request.
- `GLIBC_TUNABLES` disables tcache or caps `arena_max`.
- Persistent/keep-alive connections pin work to long-lived worker threads.

Do the integer-width audit before assuming a conventional heap bug.

## 1. Model every type conversion exactly

For each length, record:

```text
text -> parser return type -> destination type -> arithmetic -> allocator type
                                      -> copy/read helper parameter type
```

A critical pattern is:

```c
size_t n = strtoll(user, NULL, 10);
void *p = malloc(n + 1);
readn(fd, p, n);                 // readn(..., unsigned int len)
```

On a 64-bit target, `user = -1` can produce:

```text
strtoll("-1")         = -1
(size_t)-1            = 2^64 - 1
n + 1                 = 0          (wrap)
malloc(0)             = minimum usable heap chunk
(unsigned int)n       = 2^32 - 1
```

The primitive is therefore not merely an integer bug: it is a tiny allocation paired with a huge attacker-controlled write.

Always verify the exact ABI widths and allocator behavior on the supplied target.

## 2. Keep the vulnerable request blocked

If the copy helper reads until the declared length or EOF, do not immediately finish the request.

Useful choreography:

1. send request headers that trigger the vulnerable tiny allocation;
2. send only enough body bytes to reach the desired heap offset;
3. leave the socket open so the worker stays blocked inside the read;
4. use other connections to allocate/free neighboring chunks;
5. resume the overflow only after the target geometry exists.

A network body read can act like a remotely controlled pause point inside `malloc` lifetime.

## 3. Treat thread arenas as an addressable resource

With ptmalloc, worker threads may use different arenas. If `arena_max` is bounded, additional threads reuse a finite set of arena classes.

For persistent worker services, a stable strategy is:

```text
open many keep-alive connections
 -> let each worker perform one known allocation cycle
 -> keep connections alive
 -> classify slots by deterministic arena assignment order
 -> reuse selected slots for attacker/victim choreography
```

Do not rely on two arbitrary connections sharing an arena by luck when the service lets you pin workers.

Record:

- `arena_max`;
- whether the main thread uses the main arena;
- creation/reuse order of worker arenas;
- which sockets/workers remain pinned;
- whether a selected slot is main-arena or non-main-arena backed.

## 4. Build an unsorted-bin overlap leak

When the overflow starts from a tiny chunk before attacker-shaped live chunks, a useful leak pattern is:

```text
NEG = vulnerable tiny chunk
P   = blocked large allocation
R   = blocked large allocation to be overlapped/echoed
```

Use the overflow from `NEG` to repair any crossed small headers and enlarge `P`'s chunk size so it spans across `R`.

Then:

1. finish `P` so the forged large span is freed;
2. allocate a carefully sized chunk from that free span;
3. leave an unsorted remainder whose user area overlaps live `R`;
4. restore metadata required for `R` to complete safely;
5. finish/echo `R` and read the unsorted `fd`/`bk` pointers now present in its body.

The application echo becomes a heap metadata disclosure primitive.

For the main arena, unsorted pointers can reveal libc (`main_arena` / unsorted-bin head). Depending on geometry, another link may expose a heap pointer.

For a non-main arena, unsorted links can point into the heap-resident `malloc_state`, giving the arena address and a heap-base relation.

Never copy historical offsets. Derive the unsorted-bin head and heap/arena relation from the exact supplied libc/build.

## 5. Why tcache-off changes the plan

When tcache is disabled:

- small frees route directly into fastbins or consolidation paths;
- large chunks reach unsorted/large bins without first being captured by tcache;
- traditional tcache poisoning is unavailable;
- arena metadata and bin unlink side effects become comparatively more valuable.

Do not treat `tcache_count=0` as only a missing technique. It changes heap choreography and often indicates that the intended primitive is in unsorted/large-bin or arena state.

## 6. Pivot a non-main arena through largebin metadata

A powerful advanced pattern is to corrupt a real largebin chunk and the current top chunk so allocator unlink/nextsize maintenance performs a write into `malloc_state`.

Conceptually:

```text
real sorted large chunk
  fd/bk        -> expected largebin links
  fd_nextsize  -> valid relation
  bk_nextsize  -> forged current-top chunk

forged top chunk
  metadata crafted as a valid largebin node
  nextsize links chosen so unlink side effect targets arena->top
```

Trigger an allocation that forces the largebin scan/unlink. If the exact glibc checks are satisfied, the nextsize side effect can replace `arena->top` with a heap address you control.

This is highly version-dependent. Before using it, inspect the supplied libc's `_int_malloc` / `unlink_chunk` largebin checks and derive:

- chunk sizes and bin index;
- `fd`, `bk`, `fd_nextsize`, `bk_nextsize` validation;
- `malloc_state.top` offset;
- `NON_MAIN_ARENA` requirements;
- the exact heap address that should become the new top.

## 7. Rewrite the non-main `malloc_state` only after the pivot

If a blocked request body can be allocated from the pivoted top, it may overwrite heap-resident arena state.

Useful fields can include:

```text
mutex / flags
top
last_remainder
bin heads
binmap
next / next_free
attached_threads
system_mem / max_system_mem
```

A common safe reconstruction strategy is:

- zero transient state;
- mark the arena non-contiguous when needed;
- make empty bin heads self-reference their correct headers;
- set `top` to the chosen forged top;
- set `system_mem`/`max_system_mem` consistently with the forged region;
- keep arena-list/thread fields coherent enough for the next allocation.

Do not blindly clone an old `malloc_state` layout; derive every offset from the exact libc.

## 8. Turn top splitting into a constrained write

After controlling `arena->top`, allocator bookkeeping itself can write a remainder header at a chosen address.

For target address `W`, choose the new remainder header so its `size` field lands at `W`:

```text
remainder = W - SIZE_SZ
victim    = chosen forged-top address
nb        = remainder - victim
```

Make `nb` a valid aligned malloc chunk size and forge:

```text
top_size = nb + desired_remainder_size
```

Request `nb`. Splitting the forged top writes the remainder header, including its size field, at the target.

This is not a fully arbitrary qword write. The value normally must be **size-shaped**, e.g.:

```text
(value & alignment_mask) == PREV_INUSE
(value & ~alignment_mask) >= MINSIZE
```

Name this primitive precisely: **chosen-address allocator size-field write**.

## 9. Shape protected pointers to fit a constrained write

A constrained allocator write becomes much stronger when the target program/libc stores pointers through a reversible encoding.

For glibc-style pointer mangling of the form:

```text
stored = ROL64(pointer ^ guard, rotation)
```

and a primitive that can only write size-shaped values, solve the problem backwards:

1. choose a size-shaped `stored` value;
2. for desired function pointer `target`, derive

```text
guard = target ^ ROR64(stored, rotation)
```

3. write the crafted guard first;
4. then write the size-shaped encoded function pointer.

Alternatively, if the guard is already controlled, compute the encoded target and test whether it satisfies the write-shape constraint.

This converts "I cannot write an arbitrary pointer" into "I can choose the encoding key so the required representation fits my allocator primitive."

Always derive the mangling formula/rotation from the supplied libc.

## 10. Modern RCE endpoints when hooks/GOT are unattractive

On full-RELRO modern glibc, traditional hooks may be gone. With several constrained writes, viable control data may exist in:

- thread-local pointer guards;
- cancellation state;
- forced-unwind function pointers/state;
- registered exit handlers and their arguments;
- other pointer-mangled libc control structures.

One advanced chain is:

```text
leak libc
 -> gain repeated size-shaped writes from fresh non-main arenas
 -> set pointer guard to make desired encoded targets writable
 -> replace an existing pointer-mangled exit callback with a command function
 -> replace its argument with controlled heap data
 -> prepare cancellation/unwind state
 -> trigger a main-thread cancellation point
 -> unwind reaches the prepared exit path
```

Treat this as a version-specific endpoint, not a universal recipe. Derive TLS offsets, cancellation semantics, unwind globals, exit-list layout and pointer mangling from the supplied libc/debug/source.

## 11. Reliability lessons

For remote multi-thread allocator exploitation:

- create a clean process state when practical;
- pace worker creation if scheduler timing affects arena assignment;
- pin sockets instead of reconnecting randomly;
- label arena slots and track busy/free state explicitly;
- keep every blocked request's allocation phase in a state machine;
- restore heap headers crossed by a long overflow before triggering their frees;
- validate each leak/write stage independently;
- use fresh non-main arenas for destructive writes when one arena cannot safely survive repeated metadata corruption;
- keep retries bounded and fail on geometry divergence rather than spraying blindly.

## Common dead ends

- Searching only for a conventional stack/heap overflow and missing cross-width length conversions.
- Seeing `malloc(0)` and assuming no useful allocation is returned.
- Assuming the full 64-bit parsed length reaches a helper whose formal parameter is 32-bit.
- Racing random worker threads instead of exploiting stable arena assignment.
- Trying tcache poisoning when tcache is explicitly disabled.
- Forcing a raw arbitrary-write technique when allocator bookkeeping already supplies a useful constrained write.
- Rejecting a constrained write because a target pointer is not size-shaped without considering attacker-controlled pointer encoding/guard state.
- Reusing glibc offsets or largebin checks from a different version.

## Source / provenance

Technique harvested after a blind V2 evaluation of SekaiCTF 2026 `echo-chamber` exposed missing cross-width length and multi-thread ptmalloc-arena methodology.

- Source repository: `nuzas96/sekaictf-2026-cuba`
- Challenge source: `pwn/echo-chamber/challenge/chal.c`
- Runtime configuration: `pwn/echo-chamber/challenge/run.sh`
- Official solver studied: `pwn/echo-chamber/solution/solve.py`
- Harvest date: 2026-08-29

The reference intentionally omits challenge flag material, fixed exploit offsets, concrete heap/libc addresses and challenge-specific command strings.