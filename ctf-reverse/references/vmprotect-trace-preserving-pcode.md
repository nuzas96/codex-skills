# Trace-preserving VM p-code operand patching

Use this pattern when a virtualized/protected binary must be patched **inside the VM bytecode/tape** while the VM handlers, executed native trace, tape-read lane, output-call sites, or control flow must remain unchanged.

The key idea is to treat the protected program as two layers:

```text
native VM handlers / decoder state
        +
encrypted or encoded p-code/tape operands
```

Do not immediately try to devirtualize the whole VM. If the goal is to change a small constant or emitted value while preserving the exact execution path, recover only the p-code operand(s) that feed the target semantic store and re-encode downstream operands so the decoder stays synchronized.

## Recognize

Strong signals:

- VMProtect/custom VM/virtualized function.
- Challenge explicitly allows patching only VM p-code/tape bytes.
- Validator rejects changes to executed handler bytes.
- Tape read addresses/widths or handler instruction trace must remain identical.
- Desired behavior differs only in a few constants or data values, not branches/opcodes.
- Protected samples may be randomized between rounds, so fixed offsets are unreliable.
- VM operands are decoded using rolling register/flag state; changing one operand can corrupt later decoding even if control-flow opcodes were untouched.

This is a **dataflow and re-encoding** problem, not primarily an unpacking problem.

## Primitive

Given a baseline execution trace, identify a p-code read whose decoded value eventually reaches a target store/use. Then solve for replacement encoded bytes that make the same decode slice produce a new semantic value.

If modifying that operand changes the runtime decoder state, re-encode later tape operands so their **decoded semantics remain equal to baseline**. This preserves the same tape-read lane and native handler trace.

## Recovery workflow

### 1. Emulate one baseline execution

Use Unicorn/Qiling or equivalent and collect at minimum:

```text
instruction events: (RVA, size, native bytes)
tape reads:        (sequence, reader RIP, tape RVA, width, raw encoded bytes)
register snapshot at each tape read
relevant flags, especially carry
output/call sites
target stores/uses
```

Stub imports or runtime boundaries instead of emulating the full OS. For PE binaries, map the image at its preferred base, create a synthetic stack, replace the output/import target with a fake stub, and stop at the protected-function return boundary.

### 2. Separate handler bytes from tape bytes

Build two sets from the baseline trace:

```python
executed = {
    rva
    for event in events
    for rva in range(event.rva, event.rva + event.size)
}

tape = {
    rva
    for read in reads
    for rva in range(read.ea, read.ea + read.width)
}
```

Every proposed patch byte should satisfy:

```text
patch ⊆ tape
patch ∩ executed = ∅
```

This is a useful invariant even when the challenge validator does not enforce it explicitly.

### 3. Locate the semantic target dynamically

Do not search protected bytes for the plaintext constant and assume it is an operand. Watch runtime stores/uses instead.

Example target signal:

```text
VM decodes a 32-bit operand
→ native handler transforms it
→ value is stored to VM stack/context/native stack
→ later output depends on it
```

When the baseline value is known, hook writes and record stores matching that semantic value. Save:

- store RIP/event index;
- destination address;
- source register when identifiable;
- number of tape reads consumed before the store.

### 4. Backslice from the store to candidate tape reads

For each target store, search recent tape reads that:

- occur before the store;
- have a compatible width;
- feed the same source register or a register in the short decode chain;
- are close in the native event trace.

Use a bounded slice rather than symbolically executing the whole VM.

A good candidate is not accepted merely because it is nearby. Prove it by solving the slice for the **original baseline value** and checking that the solved encoded bytes equal the bytes actually read from the tape.

```text
candidate tape read
→ symbolic replay
→ constrain target store = old semantic value
→ solved encoded operand == original tape bytes ?
```

If not, reject the candidate.

## 5. Symbolically replay only the decode slice

Make only the candidate tape operand symbolic. Seed registers, flags, and relevant stack bytes from the snapshot taken at the tape read. Replay native instructions from that read until the target store.

For x86 VMProtect-style handlers, the useful instruction subset often includes:

```text
mov/movzx/movsx/lea
xor/or/and
add/adc/sub/sbb
inc/dec/neg/not
rol/ror/shl/shr/sar
bswap/xchg/xadd
bt/btc/bts
clc/stc/cmc
```

Capstone can decode the concrete instruction trace while Z3 models the operand-dependent dataflow.

Minimal shape:

```python
enc = BitVec("enc", width * 8)
state = symbolic_state(reg_snapshot, flag_snapshot, stack_snapshot)
seed_tape_read(state, read_insn, enc)

for event in events[read_event + 1 : store_event]:
    state.execute(disasm(event.rva))

final = value_used_by_store(state, store_insn)
solver.add(final == desired_semantic_value)
```

Solve for `enc`, convert it back to little-endian tape bytes, and patch only that tape location.

## 6. Treat carry/flags as decoder state

Encrypted p-code decoders may use `adc`, `sbb`, rotations, bit tests, or other flag-sensitive operations. A symbolic slice that ignores carry can produce a locally plausible but wrong encoding.

Record at least the carry flag at tape-read boundaries when the handler sequence uses it. More flags may be necessary for another VM.

## 7. Re-encode downstream operands after a state-changing patch

This is the most important non-obvious step.

Suppose a baseline operand is decoded as:

```text
tmp      = load_op(register_before, encoded_operand, carry)
material = key_op(tmp, decoder_key_register, carry)
```

Changing one target operand may alter registers or carry used as the decoder key for later reads. If later encoded bytes are left unchanged, the VM can decode different opcodes/operands and diverge even though only data was intended to change.

For each later tape read, preserve the **baseline decoded material** while solving a new encoded operand under the current runtime decoder state.

Conceptually:

```text
baseline encoded
 + baseline register/key/flags
 → baseline decoded material

new current register/key/flags
 + NEW encoded
 → same baseline decoded material
```

When operations are invertible, solve directly:

```python
def invert_right(op, result, left, carry, mask):
    if op == "xor": return result ^ left
    if op == "add": return (result - left) & mask
    if op == "adc": return (result - left - carry) & mask
    if op == "sub": return (left - result - carry) & mask
    # handle other target-specific operations carefully
```

If the transform is awkward or non-bijective, use a small Z3 equation instead.

Start downstream re-encoding from the earliest semantic patch and continue for subsequent tape reads until execution completes or decoder state reconverges.

## 8. Re-run with strict trace equivalence

After generating the patch, emulate again and compare against the baseline:

```text
same tape read count
same tape read RVA and width at each sequence index
same native handler event count
same handler RVA/size/native bytes
same output-call count and call sites
same protected-function stop/return site
```

Only the intended semantic output/data should differ.

This catches accidental opcode changes, lane changes, incorrect decoder resynchronization, and handler corruption.

## Randomized protected samples

If each protection build randomizes handlers, section layout, or p-code placement, never carry raw offsets from one sample to another.

Repeat per sample:

```text
load PE
→ discover VM/tape section structurally
→ emulate baseline
→ discover target stores dynamically
→ backslice to tape reads
→ prove candidate against original bytes
→ solve replacement encoding
→ re-encode downstream tape
→ strict trace validation
```

Structural and runtime invariants survive randomization better than signatures.

## Fast decision tree

```text
Need to change protected output/value?
│
├─ native handler patch allowed
│    → ordinary dynamic patching may be enough
│
└─ only VM tape/p-code may change
     │
     ├─ operand is plaintext/static
     │    → patch operand + trace-validate
     │
     └─ operand is runtime encoded/encrypted
          → baseline tape-read trace
          → identify semantic store
          → bounded symbolic backslice
          → solve target operand encoding
          → re-encode downstream operands
          → strict trace equivalence
```

## Pitfalls

- Trying to fully devirtualize VMProtect when only four data values matter.
- Searching for plaintext immediates in the protected file and missing runtime-decoded operands.
- Patching native handler instructions when the validator allows only tape bytes.
- Choosing the nearest tape read without proving it reproduces the original encoding.
- Symbolically executing millions of VM instructions instead of a bounded read-to-store slice.
- Ignoring carry/flags in the decode chain.
- Changing one encrypted operand and assuming later operands will still decode identically.
- Reusing fixed tape RVAs across randomized protection builds.
- Validating only final output; always validate tape lane and handler trace too when available.

## Tooling pattern

A practical implementation combines:

```text
PE parser     → section/import/RVA mapping
Unicorn       → deterministic baseline + patched execution
Capstone      → decode native handler instructions in the observed slice
Z3            → solve one encoded operand through a bounded dataflow slice
```

Prefer this hybrid over global symbolic execution.

## Source / provenance

Technique harvested from the official SekaiCTF 2026 `mikuprotect` challenge after a blind V2 evaluation showed that generic custom-VM guidance did not cover trace-preserving p-code mutation.

- Source repository: `nuzas96/sekaictf-2026-cuba`
- Challenge source: `reverse/mikuprotect/challenge/server.py`
- Official solver studied: `reverse/mikuprotect/solution/solve.py`
- Harvest date: 2026-08-29

The original solver is challenge-specific and large. This reference keeps only the reusable trace, backslice, symbolic-operand, decoder-resynchronization, and validation methodology; challenge constants, target strings, fixed offsets, and flag material are intentionally omitted.
