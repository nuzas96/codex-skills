# SekaiCTF 2025 hard pwn patterns

Source: `project-sekai-ctf/sekaictf-2025` second pass, focused on zero/near-zero pwn challenges.

## vkfs — FUSE/Vulkan sparse-memory filesystem exploitation via path-hash inode steering

Observed files: `pwn/vkfs/dist/src/vkfs.c`, `pwn/vkfs/solution/exp.c`, `generate_payload.py`.

Pattern:
- The challenge implements a FUSE filesystem backed by Vulkan sparse image memory. File identity is derived from `path_coord(path)` / `coord_ino(coord)`, ultimately from hashes of full paths.
- Directory entries are a packed `uint16_t ino + NUL-terminated filename` array. Entry movement/removal uses `strlen(filename)` and `memset(dirent, 0, sizeof(uint16_t)+strlen(filename))`, which is fragile when dirents are corrupted, renamed, or packed tightly.
- `rename`, `link`, `unlink`, and hardlink accounting can make directory entries point to attacker-chosen inodes/coordinates while freeing or reusing the underlying Vulkan memory binding.
- The solution brute-forces filenames whose SHA-256-derived coordinates satisfy exact bit conditions, e.g. matching a target directory entry's bucket/mip/block class or forcing inode-like values `0x1000` / `0x2000`.
- After arranging collisions and stale dirents, it opens a crafted path and `pread(..., 0xffa8)` to read sensitive memory/flag-adjacent content through the filesystem abstraction.

Recognition checklist:
1. Filesystem/path challenge derives storage coordinates from a hash of the path rather than from allocated inode objects.
2. Directory entries store short inode IDs separately from full filenames.
3. `rename/link/unlink` update dirents and nlink/memory bindings in separate steps.
4. There are sparse memory bindings or custom block mappings underneath normal FUSE operations.
5. Exploit includes filename brute force for hash-coordinate constraints: keep those generators; they are part of the primitive, not noise.

Practical workflow:
- First map the path-hash function and coordinate/inode truncation.
- Brute-force printable filename bytes for target coordinate classes before debugging memory corruption.
- Use ordinary syscalls (`mkdir`, `mknod`, `rename`, `link`, `unlink`, `open`, `pread`) to drive the bug; do not assume you need direct Vulkan API access.
- Trace `rename` with same-parent vs cross-parent paths; this code reuses `old_parent_data` as `secondbuf` for same-parent and writes both old/new parent buffers.

Pitfalls:
- The exploit payload bytes in filenames are not shellcode; they are hash-steering artifacts plus packed dirent corruption targets.
- Because coordinates are hash-derived, small path prefix changes invalidate the payload. Preserve exact directory depth and filename lengths while adapting.

## WIC — zero-solve Windows 0day challenge had no local artifact in repo

Observed file: `pwn/wic/README.md` only.

The repository does not include the VM image or exploit/writeup, only an external Windows QCOW2 URL, login hint, and an X/Twitter hint. Do not create a fake technique note from this alone. If this challenge is revisited, download the VM separately, snapshot it, disable updates as instructed, and treat it as Windows local privilege/kernel or service pwn triage.

Minimal triage route when artifact is available:
1. Snapshot the VM before booting; Windows updates can destroy the intended vuln surface.
2. Inventory monthly patch level and services exposed to the remote harness.
3. Use the provided hint URL as a lead, but verify against the VM build.
4. Preserve crash PoCs and WinDbg notes separately before trying to weaponize.

## Umiyuri Kaikeitan — self-encrypted Windows pages redirected by overflowing packer metadata

Observed files: `pwn/umiyuri-kaikeitan/challenge/src/main.cpp`, `challenge/app/app.py`, `solution/gen.py`.

Pattern:
- The Windows binary is protected by a custom packer. During static initialization it finds `.text`, derives per-page XOR keys from a PRNG seeded with `PJSK`, encrypts each page, marks encrypted pages `PAGE_NOACCESS`, and installs a vectored exception handler.
- On execute-access violation inside `.text`, the handler decrypts the faulting page with `codeStatus[idx].key[]`, marks it executable, and resumes. This turns page faults into lazy code decryption.
- `main()` reads attacker-supplied `data.txt`, XOR-decodes it with the repeating key `PJSK`, and writes bytes into a fixed 65536-byte global `staticStorage` without bounds checks. `codeStatus[]` is the adjacent global metadata after `staticStorage`.
- The exploit first places Windows shellcode in `staticStorage`, then overflows into selected `codeStatus` entries. It sets fake XOR keys so that when specific encrypted pages fault and are “decrypted”, existing ciphertext transforms into short patch stubs:
  - make a code page writable/executable via `VirtualProtect`,
  - pass a pointer/length covering the shellcode buffer,
  - jump into the decoded shellcode, which runs `cmd /C "start flag.png"` for the sandbox screenshot goal.
- The submitted `data.txt` is pre-XORed with `PJSK` because the program decodes the upload before the overflow lands.

Recognition checklist:
1. A protector stores per-page encryption/decryption keys in writable global metadata.
2. A VEH/SEH access-violation handler decrypts executable pages on demand.
3. User-controlled file/input is copied into a large global buffer near that metadata.
4. You can overwrite keys/status rather than directly patching code bytes; the next page fault becomes the write primitive.
5. Challenge goal is visual/sandbox output, so payload may need to open/display a file instead of spawning an interactive shell.

Practical workflow:
- Map global layout in the compiled binary: input buffer, status/key array, and target page indices.
- Derive original per-page keys from the packer PRNG or dump them after initialization.
- Choose target pages that will execute naturally after input parsing; compute `new_key = old_ciphertext_qword ^ desired_patch_qword ^ original_key` for each qword patched by the decrypt loop.
- Keep the submitted file encoding layer separate from the runtime patch layer: first build decoded payload, then apply the program’s upload XOR.

Pitfalls:
- The payload bytes are not a simple overflow return address. The exploit corrupts a decryption oracle so normal control flow decrypts code into attacker-chosen stubs.
- Anti-debug checks (`IsDebuggerPresent`, `CheckRemoteDebuggerPresent`, PEB flags, `NtSetInformationThread`) run from the handler path; patch or emulate them when debugging locally.
- Screenshot/sandbox challenges may require “display flag.png” shellcode, not stdout exfiltration.
