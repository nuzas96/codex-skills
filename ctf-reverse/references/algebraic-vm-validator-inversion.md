# Algebraic inversion of custom-VM validators

Use this reference when a custom VM or bytecode interpreter validates attacker input with a mostly straight-line sequence of reversible word operations and compares the result with embedded constants.

The key decision is not "VM -> emulate everything". First ask whether the flag-relevant VM path is a composition of bijections over a fixed-width word. If it is, solve the validator backwards algebraically and use emulation only as a verifier.

## Recognition signals

Load this reference when several of these appear together:

- fixed-width bytecode records in `.rodata` or another data section;
- a compact interpreter/dispatcher with register-like VM state;
- input-load opcodes followed by arithmetic/bitwise operations and compare-immediate opcodes;
- per-round constants embedded directly in bytecode;
- operations such as add/subtract, XOR, rotate, multiply by an odd constant;
- a rolling `previous` or accumulator value carried between rounds;
- a final state/hash/mixer derived from the recovered input and reused to decrypt or reveal output;
- brute force, full symbolic execution, or a complete emulator would be much more work than the visible arithmetic suggests.

A common shape is:

```text
input[i]
  -> multiply by constant
  -> combine with previous state
  -> rotate
  -> add constant
  -> compare with expected constant
```

If every step is invertible, recover `input[i]` directly from the expected value.

## 1. Prove the bytecode structure before solving

Do not infer an instruction format from visual repetition alone. Establish:

1. instruction width;
2. byte order;
3. opcode byte;
4. destination/source fields;
5. immediate width;
6. terminator or bytecode length;
7. dispatcher semantics.

For an apparent fixed-width stream, write the smallest parser possible and print records before assigning meaning.

Conceptual example:

```python
import struct

RECORD = struct.Struct("<BBBBI")

for off in range(start, end, RECORD.size):
    op, dst, src, flags, imm = RECORD.unpack_from(blob, off)
    print(hex(off), hex(op), dst, src, hex(imm))
```

The layout above is only a template. Derive the real record format from the target.

Cross-check parsed fields against dispatcher code. For example, an opcode believed to be `load immediate` should visibly index the same destination field and read the same immediate width in native code.

## 2. Lift only the flag-relevant VM semantics

Do not devirtualize the entire machine unless necessary.

Start with opcodes on the validation path:

```text
LOAD_IMM
LOAD_INPUT
MOV
MUL_IMM
XOR
ROL/ROR
ADD/SUB
COMPARE
STATE_UPDATE
HALT
```

Record each handler as an equation, including exact word width.

Example notation:

```text
r[d] = imm
r[d] = input[k]
r[d] = r[s]
r[d] = r[d] * m mod 2^w
r[d] = r[d] XOR r[s]
r[d] = ROL_w(r[d], s)
r[d] = r[d] + c mod 2^w
compare r[d] with e
```

Do not omit masking semantics. Native 32-bit arithmetic naturally wraps modulo `2^32`; a decompiler may hide that fact behind ordinary-looking C arithmetic.

## 3. Classify every operation by invertibility

For a `w`-bit word, the following operations are bijections when their stated conditions hold.

| Forward operation | Inverse | Condition |
|---|---|---|
| `y = x + c mod 2^w` | `x = y - c mod 2^w` | always |
| `y = x - c mod 2^w` | `x = y + c mod 2^w` | always |
| `y = x XOR c` | `x = y XOR c` | always |
| `y = ROL_w(x,r)` | `x = ROR_w(y,r)` | always |
| `y = ROR_w(x,r)` | `x = ROL_w(y,r)` | always |
| `y = x * m mod 2^w` | `x = y * m^{-1} mod 2^w` | `gcd(m,2^w)=1` |
| `y = NOT(x)` | `x = NOT(y)` | always |

For modulus `2^w`, multiplication by `m` is invertible exactly when `m` is odd.

Python gives a convenient inverse:

```python
inv = pow(m, -1, 1 << w)
```

But check the condition first:

```python
from math import gcd
assert gcd(m, 1 << w) == 1
```

### Operations that are usually lossy

Be suspicious of:

- `AND` masks that clear bits;
- logical shifts that discard bits;
- multiplication by an even constant modulo `2^w`;
- truncation to a smaller width;
- table lookups with collisions;
- modulo reduction by an unrelated non-bijective modulus;
- comparisons that expose only a predicate rather than the full expected word.

One lossy step does not automatically make the challenge hard, but it means direct one-to-one inversion is no longer sufficient. At that point consider bounded enumeration, SMT, or emulation around only the lossy part.

## 4. Reverse a transformation in the exact opposite order

Suppose a VM round computes:

```text
y = ROL_w((x * m) XOR p, r) + a mod 2^w
```

and compares `y` with known constant `e`.

If `m` is invertible, solve:

```text
u1 = e - a mod 2^w
u2 = ROR_w(u1, r)
u3 = u2 XOR p
x  = u3 * inverse(m) mod 2^w
```

The most common implementation mistake is to apply inverses in forward order. Function composition reverses:

```text
F = A o R o X o M
F^-1 = M^-1 o X^-1 o R^-1 o A^-1
```

Write both equations explicitly before coding.

## 5. Rotation helpers must preserve width

Use width-aware helpers and mask after the operation.

```python
MASK32 = (1 << 32) - 1

def rol32(x, r):
    r &= 31
    return ((x << r) | (x >> (32 - r))) & MASK32

def ror32(x, r):
    r &= 31
    return ((x >> r) | (x << (32 - r))) & MASK32
```

Handle `r == 0` correctly in languages where shifting by the word width is undefined or behaves differently.

For a generic helper:

```python
def rol(x, r, w):
    r %= w
    mask = (1 << w) - 1
    if r == 0:
        return x & mask
    return ((x << r) | (x >> (w-r))) & mask

def ror(x, r, w):
    r %= w
    mask = (1 << w) - 1
    if r == 0:
        return x & mask
    return ((x >> r) | (x << (w-r))) & mask
```

## 6. Identify the meaning of rolling state precisely

A repeated round often depends on a value called conceptually `previous`, but determine what it actually is.

Possible definitions include:

```text
previous transformed result
previous expected constant
previous raw input
rolling hash state
register copied from previous round
```

These are not interchangeable.

Trace the VM dataflow across one full round boundary. A useful table is:

| Round | Input source | Previous source | Multiplier | Rotate | Add | Expected | Next previous |
|---|---|---|---|---|---|---|---|
| 0 | `input[0]` | init constant | ... | ... | ... | ... | ... |
| 1 | `input[1]` | ... | ... | ... | ... | ... | ... |

If the next round uses the known expected result as `previous`, rounds can often be inverted independently in forward index order. If it uses a function of the unknown prior input, recover the dependency in the correct order.

## 7. Parse repeated validator blocks instead of hardcoding constants

Once instruction semantics stabilize, identify the structural pattern for one input round and extract parameters automatically.

Conceptual workflow:

```text
LOAD_INPUT i
MUL_IMM m_i
XOR previous
ROL r_i
ADD a_i
COMPARE e_i
COPY/STATE transition
```

Then generate tuples:

```python
rounds = [
    # (index, multiplier, rotation, add_constant, expected, previous_source)
]
```

This is more robust than manually transcribing dozens of constants from a disassembler.

Do not assume every round has identical instruction count. Match semantic opcodes or build a tiny basic-block decoder when needed.

## 8. Minimal algebraic solver template

After extracting per-round parameters:

```python
MASK = (1 << W) - 1

for rnd in rounds:
    m = rnd.multiplier
    rot = rnd.rotation % W
    add = rnd.add_constant
    expected = rnd.expected
    previous = resolve_previous(rnd)

    z = (expected - add) & MASK
    z = ror(z, rot, W)
    z ^= previous

    if m % 2 == 0:  # for modulus 2^W
        raise ValueError("multiplier is not invertible; switch strategy")

    x = (z * pow(m, -1, 1 << W)) & MASK
    recovered.append(x)
```

Immediately enforce target input bounds:

```python
assert all(lo <= x <= hi for x in recovered)
```

A candidate outside the parser's allowed range is evidence that the lifted equation, width, endianness, round boundary, or previous-state interpretation is wrong.

## 9. Forward verification is mandatory

Never trust inverse math alone. Re-run the recovered value through the exact forward equation:

```python
def forward(x, previous, m, rot, add, w):
    mask = (1 << w) - 1
    y = (x * m) & mask
    y ^= previous
    y = rol(y, rot, w)
    y = (y + add) & mask
    return y

assert forward(x, previous, m, rot, add, W) == expected
```

Then validate the full recovered input against the original unmodified binary when possible.

Use three levels of proof:

```text
per-operation math check
→ per-round forward equation
→ original program success path
```

## 10. Prefer algebraic inversion before emulation or SMT when the path is bijective

Decision rule:

```text
custom VM discovered
  -> recover validation-path opcodes
  -> is the path straight-line or dependency-simple?
       no  -> emulator / symbolic execution / trace
       yes
  -> are all relevant transforms invertible?
       yes -> algebraic inversion first
       partly -> invert known suffix/prefix and solve only lossy core
       no -> emulator / SMT / bounded search
```

Why this matters:

- less implementation surface than a full emulator;
- avoids modeling irrelevant VM opcodes;
- deterministic and easy to verify;
- exposes wrong semantics immediately through round checks;
- often turns an apparent VM challenge into a few equations.

An emulator is still useful after the algebra is understood, especially as a regression oracle.

## 11. Hybrid strategy for partially invertible validators

Do not abandon inversion because one step is lossy.

Example:

```text
input
→ invertible prefix
→ 8-bit table lookup with small ambiguity
→ invertible suffix
→ compare constant
```

Invert the suffix from the expected constant to constrain the table output, enumerate only the small set of preimages, then reverse/verify the prefix.

Likewise for an even multiplication modulo `2^w`, solve the congruence and enumerate the finite residue family rather than brute-forcing the full input domain.

The general principle is:

> Push known constants backwards through every bijective layer before invoking a solver.

## 12. Distinguish VM validation state from post-validation state

Some binaries maintain a second state while validating input, for example:

```text
state = state * C + input[i] mod 2^k
```

or another rolling hash/mixer.

Recovering accepted input may only solve the first stage. Trace where the rolling state is used after validation.

Possible uses:

- decrypt an embedded ciphertext;
- seed a PRNG;
- derive a key or keystream;
- select a resource offset;
- transform the final flag buffer.

Recompute this state from the recovered input with exact width and update order.

Do not substitute the per-round comparison value for the rolling hash unless native dataflow proves they are the same variable.

## 13. Recognize mixer constants as fingerprints, not proofs

Constants associated with known mixers can be useful clues. For example, a sequence of well-known 64-bit mixing constants may suggest a SplitMix-style finalizer.

Use such constants to locate and understand the post-validation routine, but derive the exact target implementation from disassembly/decompilation.

A familiar constant does not prove:

- the entire standard algorithm is present;
- the same initialization is used;
- the same number of rounds is used;
- state is incremented in the standard order.

Fingerprint -> inspect -> reproduce -> verify.

## 14. Keep validation and decryption widths separate

A common construction uses different word sizes for different stages:

```text
validator arithmetic: 32-bit
rolling state:          64-bit
flag mixer:             64-bit
input elements:          8-bit
```

Model each width explicitly.

Do not let Python's arbitrary-precision integers silently erase native overflow semantics:

```python
MASK32 = 0xffffffff
MASK64 = 0xffffffffffffffff

v32 = expr & MASK32
s64 = expr & MASK64
```

This single issue explains many "the algebra looks right but verification fails" cases.

## 15. Input parser constraints are part of the proof

Before solving, inspect how the native program parses values:

- decimal or hexadecimal;
- signed or unsigned;
- byte/word/dword storage;
- range checks;
- exact element count;
- separators;
- duplicate/permutation constraints.

If the algebra returns a small permutation-like sequence, that can be a useful sanity check only if the parser/challenge logic supports it. Do not impose uniqueness or permutation assumptions that are not present in code.

## 16. Useful static workflow

```bash
file ./chall
strings -a -n 5 ./chall | head -200
objdump -d -M intel ./chall > disasm.txt
readelf -SW ./chall
objdump -s -j .rodata ./chall > rodata.txt
```

Then answer:

1. where is the dispatcher?
2. where does bytecode begin/end?
3. what is the instruction record?
4. which opcodes touch input?
5. which opcode performs comparison/failure?
6. which state survives between rounds?
7. what code executes only after all comparisons pass?

Use Ghidra/IDA/Binary Ninja when xrefs and decompilation help, but keep the final solver driven by target-derived constants.

## 17. Build a small bytecode decoder before a full emulator

A decoder/disassembler is often enough:

```python
OP = {
    # target-derived opcode -> mnemonic
}

for ins in parse_stream(blob):
    print(f"{ins.off:08x} {OP.get(ins.op, 'UNK'):10} d={ins.dst} s={ins.src} imm={ins.imm:#x}")
```

This makes repeated validator blocks obvious and reduces transcription errors.

Only implement execution semantics if algebraic lifting is insufficient.

## 18. Common dead ends

### Full emulator too early

Symptom: hours spent implementing branches, calls, opcodes, and VM runtime details that never affect validation.

Fix: slice from compare/failure opcodes backwards to input loads and lift only those handlers.

### Symbolic execution before semantics

Symptom: state explosion or solver expressions full of interpreter machinery.

Fix: devirtualize the short arithmetic path manually and express the validator directly.

### Brute-forcing byte inputs

Even a small per-byte domain grows rapidly across many positions. If the compare exposes a full transformed word and the transform is bijective, inversion is exact and cheaper.

### Missing modular wrap

Symptom: recovered values are almost plausible but forward checks fail.

Fix: mask at the exact native width after every operation whose implementation wraps.

### Multiplying by a non-existent inverse

`pow(m,-1,2**w)` is valid only when `gcd(m,2**w)=1`. For power-of-two modulus this means odd `m`.

### Wrong rolling dependency

Symptom: round zero works and later rounds fail.

Fix: trace what value is copied into the previous-state register at the round boundary.

### Stopping when accepted input is found

Symptom: recovered sequence passes validation but no flag appears offline.

Fix: trace post-validation use of rolling state, ciphertext, or mixer routines.

### Treating known mixer constants as a drop-in algorithm

Fix: reproduce the exact target routine and verify against an observed intermediate value or original binary.

## 19. Evidence checklist

Record in `PROGRESS.md`:

- binary format/architecture/protections relevant to analysis;
- bytecode section and how its location was derived;
- instruction width/endianness/field layout;
- opcode-to-semantics mapping for the validation slice;
- exact word widths and masks;
- per-round parameters;
- proof each multiplier/operation is invertible;
- backward equation;
- recovered input constraints;
- forward-verification result for every round;
- rolling-state recurrence and final state if relevant;
- post-validation decryption/mixer semantics;
- validation against the original binary.

## 20. Compact solve template

```text
triage binary
→ locate VM dispatcher + bytecode
→ infer fixed-width instruction records
→ lift only validation opcodes
→ write forward equation for one round
→ classify operations as bijective/lossy
→ push expected constants backwards through inverse operations
→ recover each input element
→ forward-verify every round
→ recompute any rolling state
→ reverse post-validation output transform
→ test complete candidate in original binary
```

## Provenance

This playbook was generalized from the Bahtera Siber `Adat Istiadat Raja` reverse-engineering writeup. The source challenge used a fixed-width custom VM whose validation rounds combined input multiplication, XOR with prior state, word rotation, addition, and comparison; odd multipliers made the round transform invertible modulo a power of two. The accepted input also fed a separate rolling state used by a later flag-decryption routine.

Challenge-specific bytecode offsets, opcode numbers, constants, recovered input values, final state, mixer constants, ciphertext, and flag are intentionally omitted. Always derive them from the supplied target.
