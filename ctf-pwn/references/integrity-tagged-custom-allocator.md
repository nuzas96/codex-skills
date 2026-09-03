# Integrity-Tagged Custom Allocator Metadata Forgery

Use this reference when a native CTF target uses a **custom allocator or object header** whose metadata includes a size/length field plus an integrity value, and an adjacent read/write bug lets you leak and then rewrite that metadata.

The reusable primitive is not merely "heap overflow". It is:

```text
leak adjacent allocator header
  -> understand integrity relation
  -> forge a larger valid size
  -> application trusts the forged size
  -> later legitimate edit becomes an overflow into the next live object
  -> overwrite callback / vtable / function pointer
  -> trigger controlled call
```

This is different from ordinary ptmalloc chunk corruption because the application may enforce its **own** header magic, flags and checksum before every operation.

## Recognition signals

Strong signals include:

- application-managed objects are preceded or followed by fixed-size metadata;
- a show/read operation returns more bytes than the nominal object length;
- the leaked adjacent bytes decode into stable fields such as `magic`, `size`, `flags`, `checksum`;
- edits are bounded by a size read from allocator metadata rather than the original requested length;
- corrupting size alone causes an integrity/checksum failure;
- two or three controlled allocations can be made adjacent in a predictable order;
- a later object contains a callback, destructor, validator, vtable, function pointer or indirect-call target;
- seccomp or NX means the final control-flow primitive must pivot into ROP rather than execute injected code directly.

## 1. Map the custom header before corrupting it

Reverse the exact header layout and validation path first.

Conceptually:

```c
struct hdr {
    uint32_t magic;
    uint32_t size;
    uint32_t flags;
    uint32_t checksum;
};
```

Do not assume these field widths or order. Derive them from the supplied binary/source and confirm with multiple allocations of different requested sizes.

Record:

- header size and alignment;
- which field controls usable payload length;
- whether `size` includes header bytes or only user bytes;
- which operations validate metadata;
- exact integrity/checksum formula;
- whether any secret cookie, heap address, generation counter or per-process randomness participates.

## 2. Use adjacency deliberately

A useful layout is:

```text
A user data | B header | B user data | C header | C user data / callback
```

Choose A so its buggy read or write reaches B's header. Choose B so a forged size can later span far enough to reach the control-sensitive fields in C.

Do not rely on allocator folklore alone. Verify adjacency from an actual leak, debugger, or deterministic allocation behavior.

## 3. Turn an overread into a metadata oracle

If the program displays more bytes than A owns, preserve the raw leak and parse the trailing bytes as B's header.

Example parser shape:

```python
import struct

magic, old_size, flags, checksum = struct.unpack('<IIII', leak[-16:])
```

Validate the parse before using it:

- `magic` should stay stable across equivalent objects;
- `size` should correlate with requested allocation size/alignment;
- flags should match object state/class;
- checksum should change predictably when another validated field changes.

A plausible-looking tuple from one run is not enough.

## 4. Repair simple integrity tags instead of deleting them

When reversing shows a checksum that is a plain XOR of header fields, changing one field can be repaired algebraically.

If:

```text
checksum = K ^ magic ^ size ^ flags
```

and only `size` changes, then:

```python
new_checksum = old_checksum ^ old_size ^ new_size
```

This works because all unchanged terms cancel.

General rule:

```text
old_tag XOR old_changed_terms XOR new_changed_terms = new_tag
```

**Only use this delta trick after proving the tag is XOR-linear.** It does not apply to CRCs with hidden state, keyed MACs, nonlinear hashes, address-dependent cookies, or checksums that include payload bytes unless those contributions are also understood.

## 5. Size inflation creates a trusted overflow

The important state transition is often:

```text
physical allocation is still small
metadata now claims it is large
application later trusts metadata.size
```

That converts a normal edit path into a powerful primitive:

```c
edit(obj_B, input, validated_size_from_forged_header);
```

The allocator has not actually enlarged B. Only the program's **belief** about B changed.

Think of this as **trusted-length laundering**: a one-time adjacent metadata corruption upgrades later legitimate writes into a much longer overwrite.

After forging the header, verify the new effective capacity with the smallest non-destructive test before sending the final payload.

## 6. Preserve intervening metadata while reaching the next object

A size-inflated B may cross C's allocator header before reaching C's callback or object fields.

Model the exact layout:

```text
B payload
  + offset_to_C_header
  + C header bytes that must remain valid
  + offset_to_C_callback
  + replacement callback
  + controlled callback context
```

If C's metadata is validated before the callback fires, preserve or correctly reconstruct every required field. Blind padding can destroy the trigger before control flow is reached.

## 7. Prefer an existing callback over manufacturing an arbitrary write

If C already contains a function pointer/callback that the application later invokes, targeting it is often simpler than turning the corrupted allocator into a generic arbitrary-write primitive.

Determine:

- callback offset;
- callback calling convention / arguments;
- what pointer is passed as `rdi`, `rsi`, `rdx`, etc.;
- whether the containing object itself is attacker-controlled;
- which menu/action/destructor validates and then invokes the callback.

The trigger is part of the exploit primitive. A corrupted callback that is never reached is not code execution.

## 8. `setcontext` can bridge a callback into staged ROP

When the callback receives a pointer to attacker-controlled object memory, a suitable `setcontext` entry point can turn that structured object into register state and a stack pivot.

Do not copy historical offsets such as `setcontext+61` or fixed ucontext field positions blindly. Derive the exact implementation from the supplied libc/static binary.

The reusable composition is:

```text
overwrite callback -> setcontext-compatible entry
controlled object  -> fake context
fake context       -> registers for read(0, STAGE, N)
                     + RSP/RIP into writable staging memory
trigger callback
send stage-2 ROP directly over stdin/socket
```

The first stage should be minimal. Its job is only to escape the cramped corrupted object and gain a large, clean ROP workspace.

For generic pivot/gadget details, use `ctf-pwn/rop-advanced.md` rather than duplicating them here.

## 9. Respect seccomp instead of forcing `execve`

After control flow is obtained, inspect the actual syscall policy.

Useful checks:

```bash
seccomp-tools dump ./chall
strace -f ./chall 2>&1 | head
```

If `execve` is blocked but file I/O syscalls are allowed, use an allowed file-read chain such as:

```text
open/openat -> read/pread -> write/sendfile
```

Select syscalls from the observed filter, not from a memorized ORW template. Existing generic seccomp/ROP techniques live in `ctf-pwn/sandbox-escape.md`, `rop-advanced.md`, and the selected advanced reference.

## 10. Unknown flag path: use the read primitive for reconnaissance

Once arbitrary file read works, do not brute-force paths blindly.

Useful first reads can include:

```text
/proc/self/environ
/proc/self/cmdline
```

Environment variables may reveal `HOME`, service directories, container paths or deployment hints. Process command line can reveal the executed binary path or wrapper.

Treat those reads as **path discovery**, then use challenge-specific strings/configuration to select the final target file.

## 11. Reliability discipline

- Preserve exact binary input lengths; menu helpers that append newlines can shift corruption boundaries.
- Parse and log the leaked header before forging it.
- Change the minimum metadata fields necessary.
- Recompute integrity from target-derived logic, never hardcode one run's checksum.
- Verify the inflated size before overwriting the final object.
- Calculate the offset from B's real payload start to C's callback exactly.
- Preserve C metadata if the trigger validates it.
- Stage large ROP through a fresh `read()` instead of embedding everything in the corrupted heap object.
- Derive callback, gadget, wrapper and writable-memory addresses from the supplied binary/libc.
- If remote and local layouts differ, separate stable binary offsets from runtime heap addresses.

## Common failure modes

- Treating a custom allocator as glibc ptmalloc and applying tcache recipes immediately.
- Seeing a checksum and assuming it can be zeroed or ignored.
- Applying the XOR-delta checksum repair without first proving XOR-linearity.
- Inflating a size beyond the next object but forgetting that an intervening header must stay valid.
- Overwriting a callback without checking its invocation ABI or trigger path.
- Assuming a file transfer/read primitive means the flag path is already known.
- Forcing `system("/bin/sh")` even though seccomp or privilege rules make direct shell execution unreliable.
- Copying `setcontext` offsets from another libc/static build.
- Building the complete ORW chain inside the small corrupted object when a short staged `read()` is available.

## Completion checklist

- [ ] custom header layout derived from the target;
- [ ] adjacent leak proves A/B layout;
- [ ] integrity formula understood;
- [ ] forged header passes validation;
- [ ] B's effective editable length increases as predicted;
- [ ] distance to C callback/control field is measured;
- [ ] required C metadata remains valid;
- [ ] callback trigger and calling convention are understood;
- [ ] pivot/context offsets are target-derived;
- [ ] seccomp policy is accounted for;
- [ ] final file path is evidence-backed;
- [ ] exploit succeeds reproducibly without challenge-specific leaked constants in the reusable logic.

## Provenance

Generalized from the user-supplied P4KT4M Bahtera Siber writeup for **Cap Mohor** (binary exploitation), studied 2026-09-04. The source demonstrated an adjacent allocator-header leak, XOR-repaired size inflation, overwrite of a neighboring callback, a `setcontext`-based staged ROP pivot, and seccomp-compatible file reading. Challenge-specific addresses, credentials, remote ports and flag values are intentionally excluded.
