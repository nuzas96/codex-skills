# FUSE/path-hash filesystem pwn playbook

Use when a pwn challenge exposes a custom filesystem, FUSE daemon, object store, or virtual block layer where pathnames map into storage/inodes by hash. Built from SekaiCTF 2025 `vkfs`, but general enough for CTF filesystem exploitation.

## 1. Recognition

High-value red flags:
- File identity/inode is derived from `hash(path)` or truncated coordinates rather than allocated inode structs.
- Directory entries are manually packed: small inode field + NUL-terminated filename.
- `rename`, `link`, `unlink`, `rmdir`, or hardlink accounting update directory entries and backing storage separately.
- Backing storage is exotic: mmap, sparse memory, GPU/Vulkan memory, FUSE passthrough, custom block allocator.
- Exploit/solver brute-forces filenames to satisfy coordinate/hash constraints.

Do not dismiss filename brute force as noise. In path-hash filesystems it is often the exploit primitive.

## 2. First-pass mapping

Trace these symbols/classes first:
1. path -> hash -> coordinate/inode conversion
2. coordinate/inode -> backing storage mapping
3. directory entry encode/decode layout
4. create/mknod/mkdir allocation path
5. rename/link/unlink/rmdir cleanup path
6. read/write/pread offsets and size checks

Questions to answer:
- How many bits of hash become inode/coordinate?
- Are parent directory and basename hashed together or separately?
- Does inode truncation permit collisions?
- Are directory entries trusted more than path recomputation?
- Are nlink/refcounts authoritative for freeing backing memory?
- Is deletion zeroing based on `strlen` or stored length?

## 3. Filename brute-force strategy

When coordinate constraints exist, write a generator before debugging memory corruption.

Template:
```python
import hashlib, itertools, string

alphabet = string.ascii_letters + string.digits + '_-'
prefix = '/fixed/dir/'

def coord(path: bytes):
    h = hashlib.sha256(path).digest()
    # Replace with challenge-specific truncation/bit slicing.
    return int.from_bytes(h[:2], 'little')

def ok(c):
    return (c & 0xfff0) == 0x1000

for n in range(1, 8):
    for s in itertools.product(alphabet, repeat=n):
        name = ''.join(s).encode()
        c = coord(prefix.encode() + name)
        if ok(c):
            print(name, hex(c))
            raise SystemExit
```

Preserve:
- directory depth,
- slash placement,
- filename length,
- character set constraints,
- parent path used by the hash.

A tiny prefix/path change can invalidate all payload filenames.

## 4. Operation choreography

Useful syscall sequence families:

### Collision/stale dirent setup
1. `mkdir(A)`
2. `mknod(A/x)` or create file with target coordinate
3. `link(A/x, B/y)` to increase references
4. `rename(B/y, A/z)` to rewrite dirents in same/cross parent path
5. `unlink(A/x)` to drop original while stale dirent remains
6. `open(A/z)` or direct path to stale coordinate
7. `pread(fd, buf, large_size, offset)` to leak backing memory

### Same-parent rename stress
- Same-parent rename often reuses one directory buffer for old and new entry updates.
- Look for code that sets `secondbuf = old_parent_data` and then writes both old/new entries.
- Test overwriting an existing target vs non-existing target; code paths differ.

### Cross-parent rename stress
- Cross-parent rename can update old parent, new parent, inode nlink, and backing storage separately.
- Crash/interrupt/error between updates can leave stale entries.

## 5. Dirent corruption checks

Inspect for:
- deletion size computed as `sizeof(ino) + strlen(filename)` instead of stored record length,
- no compaction after deletion,
- duplicate filename handling,
- packed entries without bounds check on filename length,
- trusting dirent inode instead of recomputing from path,
- zeroing only the name but leaving inode bytes,
- using `uint16_t`/`uint32_t` inode truncation.

Debugging commands:
```bash
strace -f -e trace=file,read,write,openat,rename,link,unlink ./mount_or_client
python3 - <<'PY'
# dump packed dirent bytes if you can read the backing file/memory
PY
```

## 6. Backing-memory angle

If storage is mmap/GPU/sparse/custom:
- Map coordinate -> memory binding.
- Check when memory is bound/unbound/reused.
- Determine whether file reads can cross logical file bounds into backing pages.
- Test `pread` at large sizes and offsets after stale mapping setup.
- Look for page/block granularity mismatches: file size small, backing block large.

## 7. Exploit discipline

Record each successful primitive separately:
1. path collision found,
2. stale dirent created,
3. opened stale inode,
4. OOB/stale read confirmed,
5. flag/secret offset located.

Avoid jumping straight to final payload. Filesystem exploits are choreography-sensitive; one missing syscall changes state.

## 8. Pitfalls

- Mount daemons cache state; restart between attempts or add cleanup.
- FUSE kernel cache can hide bugs. Try `-o direct_io`, `-o kernel_cache` toggles if available.
- Hash brute-force payloads are environment-specific; never reformat filenames casually.
- Exotic backends like Vulkan may require the same GPU/driver behavior as challenge infra.
