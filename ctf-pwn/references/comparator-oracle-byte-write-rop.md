# Comparator-Oracle Byte Write -> Budgeted ROP Bootstrap

Use this playbook when a native challenge exposes an indexed byte comparison where the program reveals whether an attacker guess is less than, equal to, or greater than a target byte, and the equality branch permits replacing that byte.

This is stronger than a read oracle and weaker than a direct arbitrary write. Treat it as an **oracle-guided byte installer** whose cost must be budgeted before choosing the final ROP chain.

## Recognition fingerprint

Strong signals:

- attacker controls an array/index that can go out of bounds into stack state;
- the program asks for a byte-sized guess;
- three distinguishable responses encode `guess < target`, `guess == target`, and `guess > target`;
- only the equality path asks for or accepts a replacement byte;
- comparisons are signed-byte or unsigned-byte ordered;
- a loop or session imposes a hard query/turn limit;
- saved return address or other control data is reachable by index;
- the binary is static/non-PIE or otherwise has enough fixed gadgets that a small bootstrap is possible.

Typical primitive:

```text
index i
  -> compare guess g with hidden byte b[i]
       g < b[i]  -> LOW response
       g = b[i]  -> EQUAL response + write replacement w
       g > b[i]  -> HIGH response
```

The equality branch simultaneously identifies the original byte and grants a one-byte write.

---

## 1. Model the comparison semantics exactly

Before automating, determine:

- byte domain: `0..255` or signed `-128..127`;
- comparison instruction: signed (`jl/jg`, `setl/setg`) or unsigned (`jb/ja`, `setb/seta`);
- input parser type (`int`, `long`, character, decimal string, hex string);
- whether the stored byte is sign-extended before compare;
- what happens after equality and replacement;
- whether a failed probe mutates state;
- whether each probe consumes one quota unit.

Do not binary-search `0..255` when the implementation compares `signed char`. Use the exact ordered domain.

Signed-byte helpers:

```python
def s8(x):
    x &= 0xff
    return x if x < 0x80 else x - 0x100


def u8(x):
    return x & 0xff
```

If the service accepts decimal signed values while the payload is assembled as raw bytes, keep the two representations separate.

---

## 2. Convert the tri-state response into a byte-search oracle

A trichotomy oracle gives one bit-plus-direction of ordering information per query, so binary search recovers an 8-bit byte in at most about eight comparisons.

Generic search-and-write routine:

```python
def install_byte(index, desired, probe, finish_equal, hint=None,
                 lo=-128, hi=127):
    """
    probe(index, guess) returns:
      -1 if guess < current byte
       0 if guess == current byte
      +1 if guess > current byte

    On equality the protocol is waiting for the replacement byte.
    """

    if hint is not None:
        h = s8(hint)
        r = probe(index, h)
        if r == 0:
            finish_equal(desired)
            return h
        if r < 0:
            lo = h + 1
        else:
            hi = h - 1

    while lo <= hi:
        mid = (lo + hi) // 2
        r = probe(index, mid)
        if r == 0:
            finish_equal(desired)
            return mid
        if r < 0:
            lo = mid + 1
        else:
            hi = mid - 1

    raise RuntimeError("oracle semantics/index changed")
```

Critical observation:

```text
byte recovery
and
byte replacement
happen in the same equality event
```

Do not waste a second search after recovering the value.

---

## 3. Classify stable and unstable bytes

When local and remote use the same binary but ASLR affects only pointers, many bytes around the target stack frame may remain deterministic:

- fixed return addresses in a non-PIE executable;
- small counters/flags;
- zero padding;
- constant saved values;
- pointer high bytes that follow canonical-address structure may be partially predictable, but do not assume full pointer equality.

Build an invariant map from local runs:

```python
# None = do not assume remotely
KNOWN = [
    0x00,
    0x01,
    None,
    None,
    0x40,
    # ...
]
```

Use a known local byte as the first probe at that position. If it matches remotely, the byte may be installed in one oracle turn rather than a full binary search.

Do not treat a single local observation of an ASLR-derived byte as invariant. Prove stability across multiple fresh local processes first.

---

## 4. Locate the control target by index arithmetic

If the vulnerable array begins at stack offset `base_off` and saved RIP is at `ret_off`, then:

```text
RET_INDEX = ret_off - base_off
```

Derive these values from disassembly/GDB, not from historical constants.

Useful checks:

```bash
objdump -d -M intel ./chall | less
readelf -sW ./chall | less
ROPgadget --binary ./chall | less
```

In GDB, correlate the indexed address expression with the live stack frame:

```text
indexed byte address = frame_base + array_offset + attacker_index
```

Then verify that writing `RET_INDEX` changes the first byte of saved RIP in a local controlled run.

Do not begin remote byte installation until the index-to-address mapping is proven.

---

## 5. Treat the query limit as an exploit resource

For an ordered domain of 256 values, naive worst-case cost is roughly:

```text
8 comparison queries per unknown byte
```

For `n` payload bytes:

```text
worst_case_queries ~= 8 * n
```

plus protocol overhead if equality/replacement consumes an additional turn.

Before selecting a payload, calculate:

```python
budget = TOTAL_TURNS
bootstrap_len = len(stage1)
worst = bootstrap_len * 8
print(worst, budget)
```

This immediately answers whether installing a full ORW/ret2libc chain byte-by-byte is realistic.

### Better cost model

Let:

- `U` = number of bytes whose original value is unknown;
- `H` = number of bytes with a good first-probe hint;
- `S` = bytes already equal to the desired payload and therefore skipped;
- `q_bin` = average binary-search cost for unknown bytes;
- `q_hint` = average cost when a hint is tried first.

Then estimate:

```text
Q ~= U*q_bin + H*q_hint - S*saved_cost
```

Measure this locally and keep a safety margin for remote protocol desynchronization/retries.

The correct exploit may be the chain with the **fewest oracle-installed bytes**, not the chain with the fewest gadgets overall.

---

## 6. Prefer a minimal bootstrap over installing the final chain

If the oracle can overwrite saved RIP but every byte is expensive, install only enough ROP to obtain an unrestricted input primitive.

Canonical bootstrap:

```text
read(0, writable_area, large_size)
        |
        v
pivot RSP to writable_area
```

Then send the full second-stage chain directly through stdin.

Why this is powerful:

```text
expensive primitive = oracle-guided byte writes
cheap primitive     = normal read() after control-flow hijack
```

Use the expensive primitive only to reach the cheap primitive.

### Typical stage 1

For a static/non-PIE x86-64 binary with syscall gadgets:

```text
pop rax ; ret       -> SYS_read
pop rdi ; ret       -> 0
pop rsi ; ...       -> BSS
pop rdx ; ...       -> size
syscall ; ret
pop rsp ; ret       -> BSS
```

Exact gadgets and side-effect pops must be derived from the supplied binary.

A libc-call bootstrap such as `read@plt` is equally valid when dynamic symbols are available.

---

## 7. Build stage 2 for direct flag access

After the pivot, stage 2 no longer needs to be installed byte-by-byte.

Prefer a deterministic ORW chain when the flag path is known:

```text
open(path, O_RDONLY)
read(fd, buf, count)
write(1, buf, count)
```

This is often more reliable than an interactive shell, especially in a constrained service.

If the file descriptor from `open()` is not statically known, account for it explicitly:

- reason from which descriptors are already open;
- use a gadget/sequence that moves `rax` into `rdi` if available;
- use `openat`/`sendfile` variants where appropriate;
- or pivot to a libc call sequence with easier register transfer.

Do not hardcode an FD unless the process model supports it.

---

## 8. Loop exhaustion may be the control-flow trigger

A common trap is successfully overwriting saved RIP but never returning from the vulnerable function because the program remains inside a fixed-turn loop.

Model the trigger separately:

```text
install stage 1
  -> consume/exit remaining loop iterations
  -> vulnerable function returns
  -> overwritten RIP fires
  -> stage 1 read()
  -> send stage 2
```

If the protocol has a harmless input that consumes a turn without mutating the target, use it to exhaust the remaining quota deterministically.

Do not confuse:

```text
write primitive completed
```

with:

```text
control flow triggered
```

They may be separated by hundreds or thousands of loop iterations.

---

## 9. Protocol synchronization is part of the exploit

A byte oracle often has multiple response endings. Parse semantic markers, not arbitrary sleeps.

Example:

```python
def probe(idx, guess):
    io.send(f"{idx}\n{guess}\n".encode())
    data = io.recvuntil((LOW_MARK, EQUAL_MARK, HIGH_MARK))

    if EQUAL_MARK in data:
        return 0
    if LOW_MARK in data:
        io.recvuntil(NEXT_PROMPT)
        return -1

    io.recvuntil(NEXT_PROMPT)
    return +1
```

For equality, the service may be waiting at a different prompt. Handle that state explicitly before sending the replacement.

Keep a `turns` counter in the exploit and assert it never exceeds the server limit.

---

## 10. Payload-byte optimization

Before probing a byte, skip writes that are already known to equal the desired payload:

```python
for off, desired in enumerate(stage1):
    original = KNOWN[off]

    if original is not None and original == desired:
        continue

    install_byte(RET_INDEX + off, desired, hint=original, ...)
```

Other useful reductions:

- choose gadgets whose little-endian encodings share bytes with the existing stack content;
- prefer shorter bootstrap chains even if stage 2 becomes larger;
- exploit fixed zero/high address bytes in non-PIE addresses;
- place data such as the filename in an already-existing binary string when safe;
- use BSS/other writable static memory rather than constructing large stack frames through the oracle.

Do not overfit gadget choice to one accidental local stack snapshot. Only count bytes as free when their remote stability is justified.

---

## 11. Common dead ends

### Dead end: install the entire final ROP chain byte-by-byte

Why it fails:

- query budget scales with payload length;
- network latency multiplies every binary-search probe;
- one desync late in the chain wastes the full session.

Better:

```text
minimal read+pivot bootstrap -> direct stage-2 input
```

### Dead end: linear scan each byte

A 256-value linear scan can cost roughly 128 queries on average per byte.

Use ordering information. The point of `<` and `>` responses is binary search.

### Dead end: treat the primitive as a blind write

If writing is permitted only when the guess equals the old value, you must first solve the old byte. A desired replacement value is not itself a valid guess unless it happens to equal the current byte.

### Dead end: ignore signedness

Searching `0..255` against a signed comparison produces contradictory-looking branches around `0x80`.

### Dead end: overwrite RIP and immediately send stage 2

If the function has not returned, stage-2 bytes may be consumed by the original loop/parser instead of `read()`.

### Dead end: assume every local stack byte is remote-stable

ASLR-derived pointers and environment-dependent frame values may differ. Mark them unknown and pay the binary-search cost.

---

## 12. Verification checklist

Before remote execution, prove locally:

- [ ] exact signed/unsigned comparison semantics;
- [ ] tri-state response mapping;
- [ ] equality branch writes the requested replacement;
- [ ] index-to-stack-address formula;
- [ ] saved RIP/control target index;
- [ ] stage-1 gadget addresses from the exact binary;
- [ ] writable staging address;
- [ ] stage-1 `read()` size and pivot behavior;
- [ ] stage-2 ORW/ret2libc chain independently works from the pivot area;
- [ ] query budget with safety margin;
- [ ] loop-exit/control-flow trigger;
- [ ] protocol state after equality vs inequality responses.

During remote exploitation record:

```text
installed bytes / total
oracle turns used / total budget
last successful index
stage-1 trigger reached?
stage-2 read reached?
final file output observed?
```

---

## 13. General exploit pattern

```text
OOB indexed byte access
        |
        v
ordered comparator oracle
(< / == / >)
        |
        v
binary-search current byte
        |
        v
== branch grants replacement byte
        |
        v
oracle-guided byte installer
        |
        +--> compute quota economics
        |
        v
install only minimal saved-RIP bootstrap
        |
        v
exit/exhaust original loop
        |
        v
read attacker-controlled stage 2 into BSS
        |
        v
stack pivot
        |
        v
full ORW / ret2libc chain
        |
        v
flag
```

The central lesson is not merely “use ROP.” It is:

> When memory can be modified only after correctly guessing its old byte, convert the comparison into an ordered oracle, budget the expensive writes, and spend them only on a bootstrap that unlocks a cheaper input channel.

---

## 14. Routing signals

Route here when challenge/source/output contains combinations such as:

```text
OOB signed-byte comparison
binary-search stack byte
comparison oracle byte write
equality-gated byte write
guess lower / equal / higher target byte
oracle-guided ROP bootstrap
turn-limited byte overwrite
query-budgeted ROP
conditional byte replacement after correct guess
stack byte oracle then BSS pivot
```

Generic stack overflow without the comparison/equality-gated write primitive should stay in `overflow-basics.md` / `rop-and-shellcode.md`.

---

## Provenance

Generalized from the Bahtera Siber `Majlis Raja Raja` writeup. Challenge-specific addresses, stack index, turn count, file path, invariant bytes, and flag are intentionally omitted. Preserve only the reusable primitive, budget model, staged-control-flow strategy, and reliability lessons.
