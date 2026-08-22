# DalCTF2026 — Misc Patterns

Source: https://github.com/DalCTF/DalCTF2026

---

## 1. eBPF tail call via prog_array (misc/lost_my_flag_printer)

**Pattern:** a privileged eBPF program is loaded into a `BPF_MAP_TYPE_PROG_ARRAY` map, and you have access to the map but can't read the flag file directly. Write your own BPF program that `bpf_tail_call()`s into the privileged program and observes its side effects (e.g. it writes to a perf ring buffer you can `mmap`).

**Key syscalls:**
```c
#include <linux/bpf.h>
int bpf(enum bpf_cmd cmd, union bpf_attr *attr, unsigned int size);
// commands: BPF_PROG_LOAD, BPF_MAP_CREATE, BPF_MAP_UPDATE_ELEM,
//            BPF_OBJ_GET_FD_BY_ID, BPF_PROG_TEST_RUN, BPF_PROG_ATTACH
```

**Tail call inside your program:**
```c
// pseudocode equivalent: bpf_tail_call(ctx, prog_array_map_fd, index);
// raw bytecode:
//   r1 = ctx
//   r2 = map_fd  (or map_ptr if you looked it up)
//   r3 = index   (e.g. 0)
//   call bpf_tail_call
//   // if it returns, tail call failed — fall through to your code
```

**Pattern:**
1. Find the existing prog_array fd (`/proc/<pid>/fd` or `BPF_OBJ_GET_FD_BY_ID`).
2. The privileged program is *already* in the map by the target setup — you don't need to insert it.
3. Load your program that tail-calls into index 0.
4. Attach to a hook you can trigger (e.g. `socket_filter` on a socket you open).
5. Observe the privileged program's side effects (perf buffer, kprobe trace) to read the flag.

**Resources:**
- https://chomp.ie/Blog+Posts/Kernel+Pwning+with+eBPF+-+a+Love+Story
- https://feyor.sh/blog/ebpf-on-hard-mode/
- https://docs.kernel.org/userspace-api/ebpf/syscall.html

**Recognise:** challenge mentions eBPF, "loaded program", flag file unreadable, hint words "tail call" / "prog_array" / "BPF map".

---

## 2. APNG alpha-channel per-frame stego (misc/steg)

**Pattern:** file is APNG (animated PNG). The flag is hidden in the alpha channel of pixel (0,0) across frames — each frame's alpha byte is one character of the flag.

**Why it works:** static-image viewers see only frame 0's pixel (0,0) alpha and miss the rest. APNG-aware tools (PIL with `seek()`) iterate.

**Recon:**
```bash
file challenge.png
# may show "PNG image data" — APNG isn't always identified by `file`
python3 - <<'PY'
from PIL import Image
img = Image.open('challenge.png'); img.seek(0); n = 0
while True:
    n += 1
    try: img.seek(n)
    except EOFError: break
print('frames:', n + 1)
PY
```

**Extraction:**
```python
from PIL import Image
img = Image.open("challenge.png")
chars = []
for i in range(num_frames):  # e.g. 16
    img.seek(i)
    frame = img.copy().convert("RGBA")
    for pixel in frame.getdata():
        r, g, b, a = pixel
        chars.append(chr(a))
        break  # only first pixel per frame
print("Flag:", "".join(chars))
```

**Variations seen in the wild:**
- Alpha at (0,0) — most common.
- Alpha at a fixed (x, y) per challenge.
- LSB of pixel data per frame (not alpha — but same iteration trick).
- Palette change per frame instead of pixel alpha.

**Tells:** file extension `.png` but PIL reports multiple frames; file size large for a small image (multiple frames × palette entries); first frame shows nothing interesting — you MUST iterate.
