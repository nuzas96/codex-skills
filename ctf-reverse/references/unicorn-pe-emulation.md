# Bare Unicorn for PE Key-Derivation Emulation

When Qiling is too heavy or you only need to emulate a single function (not the whole OS layer), use bare Unicorn directly. Common case: malware-like CTF binaries (PyInstaller-extracted `Mailware.exe`, ransomware simulators, packer stubs) that compute an RC4/AES key from a filename via complex SSE/SIMD obfuscation, then decrypt an embedded resource containing the flag. Static analysis fails because hand-tracing `andps`/`packuswb` chains is impractical.

## When to Use

- Function uses SSE/SIMD heavily and you can't get Ghidra decompilation to match
- The function depends on a global state set by an init function you don't want to fully emulate
- You only need a few bytes of output (key, decrypted flag) — no need to drive the whole binary
- Binary is Windows PE (x86-64) and you want to avoid Windows-specific Qiling rootfs issues

## The Five PE Emulation Pitfalls

### Pitfall 1: vaddr ≠ raddr (the most common bug)

PE sections have two addresses: `VirtualAddress` (where the section lives in memory when loaded) and `PointerToRawData` (where it lives in the file). When emulating, you MUST map the section at its virtual address, not its raw file offset.

```python
# WRONG — maps .rdata at file offset
mu.mem_map(0x1000, 0x100000)
mu.mem_write(0x1000, file_bytes[0xda00:0xda00+0x9e00])  # .rdata at vaddr 0xf000, raddr 0xda00

# RIGHT — map at the right virtual base
import pefile
pe = pefile.PE('binary.exe')
image_base = pe.OPTIONAL_HEADER.ImageBase  # 0x140000000 for MSVC x64
for section in pe.sections:
    vaddr = image_base + section.VirtualAddress
    size = max(section.Misc_VirtualSize, section.SizeOfRawData)
    data = section.get_data()
    mu.mem_map(vaddr, align_up(size, 0x1000))
    mu.mem_write(vaddr, data)
```

**Symptom of this bug:** Constants at known virtual addresses (like `0x14000f600`) read as garbage — the bytes you wrote there are from a different section or zero. `movdqa` loads produce wrong xmm register state. Decrypted output is gibberish.

### Pitfall 2: String table offset translation

When you read bytes from the PE file at some offset to inspect a constant, **the file offset is NOT the virtual address**. Translate:

```
vaddr = ImageBase + Section.VirtualAddress + (file_offset - Section.PointerToRawData)
```

Example: `.rdata` with `VirtualAddress=0xf000`, `PointerToRawData=0xda00`. Bytes at file offset `0xe000` are at virtual address `0x14000e000` (since `0xe000 - 0xda00 = 0x600`, so `0xf000 + 0x600 = 0xf600`, plus `ImageBase 0x140000000`).

**Quick verification:** Read 16 bytes at vaddr `0x14000f600` and at file offset `0xe000`. They should match. If not, you computed the wrong offset.

### Pitfall 3: IAT calls crash without stubbing

Most Windows x64 binaries import dozens of functions via the IAT (Import Address Table). The IAT lives at a known address (e.g., `0x14000f040`). When the binary does `call [rip+0x...]` to an IAT entry, Unicorn has no idea what to do — it tries to execute whatever's at that memory.

**Fix:** Intercept indirect CALL instructions and dispatch based on the target address:

```python
from unicorn import *
from unicorn.x86_const import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

IAT_HANDLERS = {
    0x14000f040: lambda ql, mu: 0,                          # GetSystemTimeAsFileTime → return 0
    0x14000f068: lambda ql, mu: (mu.reg_write(UC_X86_REG_RAX, 0x14001d000) or 16)[1] or 16,  # GetModuleFileNameW → return ptr+len
    0x14000f070: lambda ql, mu: 5,                          # CloseHandle → return nonzero
    0x14000f078: lambda ql, mu: 0,                          # GetLastError → return 0
    # ...
}

def hook_indirect_call(uc, address, size, user_data):
    insn = next(Cs(CS_ARCH_X86, CS_MODE_64).disasm(
        uc.mem_read(address, size), address))
    if insn.mnemonic == 'call':
        # Read target address from IAT entry referenced by the call
        # (for [rip+disp32], compute target = next_ip + disp32, then deref)
        target = compute_indirect_target(uc, insn)
        handler = IAT_HANDLERS.get(target)
        if handler:
            ret = handler(uc, uc)
            uc.reg_write(UC_X86_REG_RAX, ret)
            # Skip the call by setting RIP to next instruction
            uc.reg_write(UC_X86_REG_RIP, address + size)

mu.hook_add(UC_HOOK_CODE, hook_indirect_call, None, 1, 0, UC_X86_INS_CALL)
```

**Alternative (simpler):** Pre-write a `ret` instruction at every IAT entry address, then use a code hook at the IAT addresses themselves to set RAX and advance RIP past the ret.

### Pitfall 4: Global variables need initialization

Many functions read globals set by an init function you didn't emulate. Two fixes:

1. **Emulate the init function first.** If it's at `0x140001000`, call it before the function of interest with the right argument in `edx`/`rcx`.
2. **Pre-write the constants** if you can figure them out from static analysis. In Mailware, function at `0x140001000` set two constants at known addresses:
   ```python
   mu.mem_write(0x140019af8, struct.pack('<I', 0xaf40a519))
   mu.mem_write(0x140019afc, struct.pack('<I', 0xdc7a5768))
   ```

**Symptom of this bug:** First 8 bytes of key differ from your hand-trace; high 8 bytes (from a separate function) match. Often the constants are SIMD masks or S-box seeds.

### Pitfall 5: Memory fault hook for unmapped regions

Unicorn raises `UC_ERR_READ_UNMAPPED` for unmapped memory. Add a hook to either map the page on demand or log/raise with the faulting address:

```python
def hook_mem_invalid(uc, access, address, size, value, user_data):
    # Map a default page and continue, or raise with context
    page = address & ~0xfff
    uc.mem_map(page, 0x1000)
    return True  # Continue execution

mu.hook_add(UC_HOOK_MEM_UNMAPPED, hook_mem_invalid)
```

## Minimal Working Template

```python
from unicorn import *
from unicorn.x86_const import *
import pefile

def emulate_pe_function(binary_path, func_rva, input_buf, input_len_rva):
    pe = pefile.PE(binary_path)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    image_size = pe.OPTIONAL_HEADER.SizeOfImage

    mu = Uc(UC_ARCH_X86, UC_MODE_64)

    # 1. Map all PE sections at their virtual addresses
    for section in pe.sections:
        vaddr = image_base + section.VirtualAddress
        size = max(section.Misc_VirtualSize, section.SizeOfRawData)
        size = (size + 0xfff) & ~0xfff
        mu.mem_map(vaddr & ~0xfff, size + 0x1000)
        mu.mem_write(vaddr, section.get_data()[:size])

    # 2. Map stack
    STACK_BASE = 0x80000000
    mu.mem_map(STACK_BASE, 0x100000)
    mu.reg_write(UC_X86_REG_RSP, STACK_BASE + 0x80000)

    # 3. Map scratch area for IAT stubs / globals
    SCRATCH = 0x180000000
    mu.mem_map(SCRATCH, 0x10000)

    # 4. Stub IAT entries (write 'ret' at each IAT address)
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            iat_addr = image_base + entry.struct.FirstThunk + imp.idx * 8
            # Write address of our stub function
            mu.mem_write(iat_addr, struct.pack('<Q', SCRATCH + 0x100 + imp.idx * 16))

    # 5. Set up input
    INPUT_ADDR = image_base + input_len_rva
    mu.mem_write(INPUT_ADDR, input_buf)

    # 6. Set up args (x64: rcx, rdx, r8, r9)
    mu.reg_write(UC_X86_REG_RCX, INPUT_ADDR)
    mu.reg_write(UC_X86_REG_RDX, len(input_buf))

    # 7. Add code hook for tracing (optional)
    def trace(uc, address, size, user_data):
        insn_bytes = uc.mem_read(address, size)
        # print(f"0x{address:x}: {insn_bytes.hex()}")
    mu.hook_add(UC_HOOK_CODE, trace)

    # 8. Add mem fault hook
    def fault(uc, access, addr, size, value, ud):
        return False  # Raise with addr
    mu.hook_add(UC_HOOK_MEM_UNMAPPED, fault)

    # 9. Run
    target = image_base + func_rva
    try:
        mu.emu_start(target, image_base + func_rva + 0x1000, timeout=10*UC_SECOND_SCALE)
    except UcError as e:
        print(f"Emulation failed: {e}")

    # 10. Read output (e.g., 16-byte key at a known address)
    return mu.mem_read(KEY_OUTPUT_ADDR, 16)
```

## Anti-Tamper Pattern: 4-Byte Null Magic + Checksum

A common anti-tamper in malware-like binaries: after RC4 decryption, the first 4 bytes of the plaintext MUST be `00 00 00 00` (a "magic" string). If they aren't, the function exits early. The remaining `0x40` bytes' 32-bit checksum (computed via `punpcklbw`/`paddd` sum) is compared with the value at offset `0x40`. If both pass, the decrypted data is used to construct the flag.

**Detection:** In the disassembly, look for `cmp dword ptr [rXX], 0` followed by `je skip` near the start of the decryption-handling code. The string address for `cmp` will look suspicious — it's a 4-byte region that should decode to `00 00 00 00` (often zero in your dump if you print it as ASCII because all four bytes are null).

**Verification after decryption:**
```python
assert decrypted[:4] == b'\x00\x00\x00\x00', "magic fail"
# Compute the 32-bit checksum (sum of first 0x40 bytes with byte-to-word unpacking)
import struct
words = struct.unpack('<16I', decrypted[:0x40])
checksum = sum(words) & 0xffffffff
assert checksum == struct.unpack('<I', decrypted[0x40:0x44])[0], "checksum fail"
```

## RC4 Detection Heuristic

A function that uses SSE for S-box init typically has:
- `paddd` (packed add of doublewords) on xmm constants
- `andps` (bitwise AND of packed singles, used as bitmask on packed bytes)
- `packuswb` (pack with unsigned saturation — converts words to bytes)
- A table of constants at end of function (the S-box permutation)

If you see all four, the function is initializing an RC4 S-box via SSE. The constants at the function's end (e.g., at `0x14000f5e0`) are NOT the S-box — they're the unpacking LUTs.

## Common Decryption Call Site

```asm
; Standard pattern: rcx=key_addr, edx=key_len, r8=data_ptr
mov  rcx, 0x140019b00    ; key storage
mov  edx, 0x10           ; key length (always 16 for AES-128 / RC4 with 16-byte key)
lea  r8, [rip + data]    ; data pointer (from LockResource or similar)
call 0x140001260         ; decryption function
```

The key length (`edx=0x10`) is a strong hint that the cipher is RC4 with a 16-byte key (or AES-128). RC4 with 16-byte keys is rare in practice — usually RC4 keys are 5-16 bytes — so check both.

## References

- See [tools-dynamic.md](tools-dynamic.md) for Frida/angr alternatives
- See [tools-emulation.md](tools-emulation.md) for Qiling (higher-level OS emulation)
- See [patterns-ctf.md](patterns-ctf.md) for RC4 static-analysis patterns
