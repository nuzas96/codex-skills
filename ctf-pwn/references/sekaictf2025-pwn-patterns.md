# SekaiCTF 2025 — Pwn Patterns

Source: https://github.com/project-sekai-ctf/sekaictf-2025. Extracted from author solution writeups/scripts under `pwn/*/solution/`.

---

## 1. MIPS PIC `$gp` partial overwrite as fake-GOT pivot (`outdated`)

**Pattern:** A signed integer index writes two bytes OOB relative to a stack variable. On MIPS PIC binaries, do not only look upward for saved `$ra`/`$s8`; a saved `$gp` value may sit below the local variable and gets reloaded after function calls.

**Recon / Detect:** MIPS little-endian PIE/ASLR target, global-pointer-relative loads for GOT/string addresses, an OOB short/int write with negative index, and a function that calls `exit()` instead of returning. In GDB/QEMU, break after a call and inspect whether `$gp` is restored from stack.

**Exploit / Solve:** Put a fake GOT-like table in a global buffer at a known PIE-relative address. First `$gp` overwrite redirects `puts("constant")` into a leak primitive such as `puts_blue(&GOT['puts'])` and redirects `exit()` back to `main()` for a second shot. After libc leak, second fake table maps the same call site to `system("/bin/sh")`.

**Tell:** If a MIPS exploit seems blocked because saved return registers are never used, audit `$gp` reloads after every call. `$gp` controls both function pointers and PIC-relative constant-string arguments.

## 2. No-leak heap arbitrary write by allocating tcache metadata into `.bss` (`speedpwn-2`)

**Pattern:** Clear heap OOB/arbitrary write but no initial leak; PIE disabled and GOT writable. Instead of needing a heap/libc leak first, steer allocator metadata so a future allocation lands in `.bss` near the GOT.

**Recon / Detect:** No PIE, partial RELRO/GOT overwrite possible, heap OOB write can corrupt tcache state, but no obvious leak primitive.

**Exploit / Solve:** Use the heap OOB to manipulate `tcache_perthread` / tcache entries so malloc returns a chunk in `.bss` a few qwords before GOT. Overwrite `free@GOT` to `printf@plt`, trigger `free(user_controlled_format)` to leak addresses, then overwrite `free@GOT` again to `system` and free a `/bin/sh` string.

**Tell:** When no leak exists but PIE is disabled, ask whether allocator corruption can target a static writable region first, then convert an existing call (`free`) into a format-string leak before the final hook.

## 3. C++ raw `char*` input overflow (`learning-oop`)

**Pattern:** `std::cin >> ptr` into a raw `char *`/heap buffer has the same unbounded semantics as scanf `%s` unless width/size checks are imposed.

**Recon / Detect:** C++ menu/OOP challenge, heap object fields, raw pointer buffers, stream extraction operator used directly.

**Exploit / Solve:** Treat as heap overflow into adjacent object metadata/vtable/function pointer depending on layout. Confirm with cyclic input under GDB rather than assuming C++ streams are safe.

**Tell:** Any direct extraction into `char*` is a red flag even when the rest of the code uses C++ abstractions.
