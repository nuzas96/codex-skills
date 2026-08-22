# kernelpwn — Linux Kernel Exploitation Playbook

Source: https://github.com/smallkirby/kernelpwn (shallow cloned to `/tmp/upgrade-2026-06-22b/kernelpwn`)

This is a methodology/playbook repo, not a writeup repo — structured around *techniques* and *situational checklists*, not individual challenges. Read the technique doc when you have a kernel challenge, not the writeups.

---

## 1. modprobe_path (run root shell with ONLY AAW — no leak needed)

**Pattern:** overwrite `modprobe_path` kernel global with path to your evil script. Trigger kernel to execve the script as root by running a file with malformed magic bytes. This is the most reliable LPE when you have arbitrary-address-write but no leak.

**Conditions:**
1. AAW (any kind — UAF on kernel heap, ROP write, struct corruption)
2. Can write 2 files: one with malformed format (`\xff\xff\xff\xff`), one shell script
3. Can execve the latter file
4. `CONFIG_STATIC_USERMODEHELPER` is NOT enabled (most CTF setups don't)

**Key trick — works WITHOUT leak:**
- `modprobe_path` has only **1-byte KASLR entropy** (it's a kernel `.data` pointer).
- If you have AAW, bruteforce the 1 byte by re-running the exploit ~16 times. No `dmesg`/info leak needed.
- Example: LINE CTF 2021 `pprofile` — solved with brute-force.

**Principle (Linux ≥ 3.x):**
- `execve()` → `do_execve()` → `search_binary_handler()` walks `formats` list.
- Each `linux_binfmt` has a `.load_binary` callback. When ALL loaders reject the file (because magic bytes don't match any), the kernel falls back to invoking `modprobe_path` to ask userspace for help loading an unknown format module.
- `request_module("binfmt-%04x", magic)` → `call_modprobe()` → `__request_module()` → forks `/bin/sh -c <modprobe_path>` as root.
- Since `modprobe_path` is a userspace-controllable string, pointing it at your evil script gives you root.

**Tell:**
- Kernel challenge with AAW but no obvious info leak primitive.
- Running a binary with `\xff\xff\xff\xff` as the first 4 bytes doesn't crash and doesn't give a useful error — instead the kernel tries to load a module.

---

## 2. tty_struct exploitation (heap-based, kmalloc-1024)

**Pattern:** open `/dev/ptmx` → kernel allocates `tty_struct` (size ~0x2B8 → kmalloc-1024 slab). Various `ioctl` operations (e.g. `TIOCSTI` to push chars to TTY input, `TIOCGWINSZ` to write window size struct back to userspace) make it possible to overflow, leak, or get code execution by corrupting `tty_struct`.

**Recon:**
- `open("/dev/ptmx", O_RDWR | O_NOCTTY)` allocates `tty_struct` (kmalloc-1024).
- `ioctl(fd, TIOCSTI, &c)` — push char `c` to the TTY input queue.
- `ioctl(fd, TIOCSWINSZ, &ws)` — set window size (writes `ws.ws_row`/`ws.ws_col` into the struct, can OOB-write to adjacent slab if struct is corrupted).
- `ioctl(fd, TIOCCONS, NULL)` — redirect console output.

**Why useful:**
- `tty_struct` has function pointers (`tty->ops->write`, `tty->ops->ioctl`). If you can corrupt `tty_struct` and trigger one of these ops, you have RIP control.
- `tty_struct.ops` is read-only after init → usually you corrupt other fields (`tty->driver_data`, `tty->ldisc_data`) to chain into another struct with function pointers (e.g. `tty_ldisc`, `tty_file_private`).

**Tell:**
- Challenge gives you open of `/dev/ptmx`.
- Slab fuzzing in kmalloc-1024 region.
- Any `ioctl` available on a TTY fd.

---

## 3. userfaultfd for stable race conditions (the modern way)

**Pattern:** register a memory region with `userfaultfd` so that when the kernel tries to fault-in a page in that region, control returns to userspace (NOT a kernel panic, NOT a SIGBUS). Use this to pause kernel code mid-operation, modify shared state from another thread, then resume the kernel code.

**Why it's a game-changer:**
- Classic TOCTOU races require precise timing — fragile.
- With `userfaultfd`, you PAUSE the kernel thread at the exact page boundary. Race window is "as long as you want" until you unblock the uffd handler.

**Setup (3 syscalls):**
```c
#include <sys/syscall.h>
#include <linux/userfaultfd.h>

int uffd = syscall(SYS_userfaultfd, O_NONBLOCK | O_CLOEXEC);
struct uffdio_api api = {.api = UFFD_API, .features = 0};
ioctl(uffd, UFFDIO_API, &api);  // advances state to RUNNING

struct uffdio_register reg = {
    .range = {.start = (unsigned long)page_aligned_addr, .len = PAGE_SIZE},
    .mode = UFFDIO_REGISTER_MODE_MISSING,
};
ioctl(uffd, UFFDIO_REGISTER, &reg);

// In a dedicated handler thread:
for (;;) {
    struct pollfd pfd = {.fd = uffd, .events = POLLIN};
    poll(&pfd, 1, -1);
    struct uffd_msg msg;
    read(uffd, &msg, sizeof(msg));
    // ↳ control returns here when kernel faults on our registered page.
    // ↳ modify shared state from another thread NOW.
    // ↳ respond with UFFDIO_COPY to provide the page and unblock kernel.
    struct uffdio_copy copy = {
        .dst = msg.arg.pagefault.address & ~0xFFF,
        .src = (unsigned long)some_data,
        .len = PAGE_SIZE,
    };
    ioctl(uffd, UFFDIO_COPY, &copy);
}
```

**Constraints:**
- Must be root OR have `vm.unprivileged_userfaultfd=1` (kernel ≥ 5.11 added this — most CTFs allow it for non-root).
- Pre-5.2 kernels: unprivileged uffd is allowed by default.

**Tell:**
- Kernel challenge hints "race condition" or "TOCTOU".
- Need to corrupt a struct that the kernel is in the middle of reading.

---

## 4. leak via panic (jmp &flag)

**Pattern:** if you control RIP and the kernel runs without KASLR, just `jmp <address of flag string>`. The CPU fetches instructions from the flag buffer → invalid opcodes → kernel panic → kernel panic handler dumps the bytes it tried to execute as a "Code:" section in `dmesg`.

**Pre-requisites:**
- NOKASLR (or full memory knowledge — slab addresses leakable some other way)
- Kernel uses initramfs (so flag is at known offset from kernel base)
- Full RIP control
- Goal is to read the flag (not actual LPE)

**Why it works:** kernel panic message includes the bytes around the crashing instruction pointer — including the bytes the CPU tried to decode as code, which are your flag bytes.

**Tell:**
- SECCON CTF 2021 `kone_gadget` — intended solution was different, but this trick was discovered as a shortcut.
- You're stuck on "I have RIP control but can't get code execution because of SMEP/SMAP/KPTI" — try this trick first.

---

## 5. Modern SLUB freelist hardening (kernel ≥ 5.4 — affects all post-2020 CTFs)

**Pattern:** since April 2020 (patch `3202fa62fb43`), SLUB freelist pointers are stored in the **MIDDLE** of freed objects (word-aligned), not at the start. Standard `free(ptr); edit(ptr[0])` attacks no longer work for heap overflow → freelist corruption.

**Code change (simplified):**
```c
} else if (freepointer_area > sizeof(void *)) {
    /* Store freelist pointer near middle of object to keep
       it away from the edges of the object to avoid small
       sized over/underflows from neighboring allocations. */
    s->offset = ALIGN(freepointer_area / 2, sizeof(void *));
}
```

**Implications for exploit:**
- Naive `subq $8, %rsp` / partial-overwrite tricks on heap overflow don't reach the freelist pointer anymore — need overflow of ~half the object size to reach it.
- For small objects (e.g. kmalloc-32) where `freepointer_area = 32 - 16 = 16` (after header), this may not activate (freepointer stays at offset 0).
- For kmalloc-128+: freelist pointer is at ~offset 56-60 (middle).

**Tell:**
- Kernel version ≥ 5.4 in challenge.
- Heap overflow of fixed offset — older writeups' heap spray/overwrite tricks won't work as documented.

---

## 6. Kernel exploitation checklist — situational (the most-used reference file)

**Pattern:** `kernelpwn/checklist/README.md` is a decision tree: "given that SMEP/SMAP/KASLR/FGKASLR are enabled and I have X, what can I do?". Faster than the technique docs for first-pass triage.

**Key situational queries it answers:**

| I have... | SMEP/SMAP | KASLR | FGKASLR | Try first |
|-----------|-----------|-------|---------|-----------|
| AAR | either | off | n/a | Direct read primitives |
| AAR | either | on | any | leak KASLR base via `kbase` / `dmesg` |
| AAW | either | off | n/a | `modprobe_path` (no leak needed) |
| AAW | either | on | any | `modprobe_path` with 1-byte KASLR bruteforce |
| UAF on `msg_msg` | either | on | any | msg_msg heap spray → `pipe_buffer` overwrite |
| Stack overflow (kstack) | off | n/a | n/a | classic ret2usr |
| Stack overflow (kstack) | on | n/a | n/a | ROPgadgets from kernel image |
| Heap overflow | off | n/a | n/a | freelist corruption → `tty_struct`/`pipe_buffer` |
| Heap overflow | on | n/a | n/a | freelist corruption → `cred` struct overwrite |

**Tell:** ALWAYS read `kernelpwn/checklist/README.md` first when starting a kernel challenge. The decision tree short-circuits to the right technique doc 80% of the time.

---

## 7. FGKASLR detection (without reverse engineering)

**Pattern:** FGKASLR (function-granular KASLR, kernel ≥ 5.7+) randomizes each function's start independently. Detect by section count in the kernel ELF:

```bash
$ readelf -S ./vmlinux | wc -l
# FGKASLR off → ~30-40 sections
# FGKASLR on  → 30000+ sections (one per randomized function)
```

**Why it matters:** with FGKASLR, ROP gadgets are useless because function addresses are randomized. You need leak-based approaches (e.g., leak via `__ksymtab_*`) before any ROP can land.

**Tell:**
- Kernel version ≥ 5.7.
- Section count is ~30k+ in `vmlinux`.

---

## 8. Isolated SLAB cache (`GFP_KERNEL_ACCOUNT`)

**Pattern:** kernel ≥ 5.9 introduced per-cgroup isolated SLAB caches for `GFP_KERNEL_ACCOUNT` allocations (e.g. `tty_struct`, `pipe_buffer`, `cred`). Object layout is the same; isolation just means cross-cache spray is harder.

**Implications:**
- Spray targeting `kmalloc-cg-*` caches instead of `kmalloc-*` (use `cat /proc/slabinfo` to find the right one).
- Reclaim is different — `kmalloc-cg-*` doesn't reclaim to `kmalloc-*` on memory pressure.

**Tell:**
- `/proc/slabinfo` shows `kmalloc-cg-32`, `kmalloc-cg-64`, etc.
- Kernel version ≥ 5.9.

**Reference:** duasynt.com/blog/linux-kernel-heap-feng-shui-2022 by Michael S + Vitaly Nikolenko.

---

## Quick references index

- `kernelpwn/technique/modprobe_path.md` — full AAW LPE without leak
- `kernelpwn/technique/tty_struct.md` — heap-based kernel struct exploitation
- `kernelpwn/technique/userfualtfd.md` — race condition stabilization
- `kernelpwn/technique/leak_via_panic.md` — RIP control → flag via panic dump
- `kernelpwn/checklist/README.md` — situation-based decision tree (read first)
- `kernelpwn/start-kernel-pwning/README.md` — kernel build + QEMU setup
- `kernelpwn/reference/README.md` — external links (Will's Root, kileak, ptr-yudai, Alexander Popov)

## Tools to have

- `gdb` with pwndbg + `vmlinux-gdb.py` (use [kallsyms-finder](https://github.com/marin-m/vmlinux-to-elf))
- `extract-vmlinux` script from kernel source
- `pahole` for struct layout inspection
- `musl-gcc` for compiling static exploit binaries (no glibc dependency for initramfs)
