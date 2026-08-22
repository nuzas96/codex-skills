# Modern Pwn Chains

## Contents

- Two-phase format string and ret2libc
- Partial return overwrite under limited ASLR
- Two-stage SROP
- UAF callback overwrite
- Raw eBPF program-array execution

## Two-Phase Format String and ret2libc

When one interaction provides a format string and a later interaction overflows the same stack frame, preserve state across rounds:

1. Use positional `%p` probes that remain within the non-overflowing input limit.
2. Identify the canary by its low null byte and validate consistency across the same process.
3. Leak a libc return address, identify the exact symbol-plus-offset using the supplied libc, and compute the base.
4. Reach the vulnerable interaction again without restarting the service.
5. Overflow through padding, restore the canary, then execute a target-derived ret2libc chain.
6. Add a standalone `ret` when System V stack alignment requires it.

Do not hard-code argument indices or libc deltas. Derive them with a local copy, cyclic patterns, GDB, and the exact remote libc when provided.

## Partial Return Overwrite Under Limited ASLR

If only one or two low bytes of a saved return address are writable, inspect page alignment and entropy. A useful gadget may share most high bytes with the original return target. Overwrite only the predictable suffix and brute-force the remaining small entropy per fresh process.

Workflow:

1. Determine the exact overwrite width and whether input terminators add bytes.
2. Compare the original return address and desired gadget at page granularity.
3. Calculate success probability from unknown nibbles; set a bounded retry budget.
4. Make the payload self-reporting, preferably reading the flag directly instead of opening a fragile interactive shell.
5. Reconnect for each attempt if ASLR rerolls per process.

For parser targets, preserve a valid outer file and place the overflow in an extensible chunk such as an MP4 box. Recalculate size fields and byte order exactly.

## Two-Stage SROP

SROP is useful when a syscall path and stack overflow exist but ordinary gadgets are scarce.

1. Trigger `rt_sigreturn` by arranging the architecture-specific syscall number in the return register.
2. First frame: perform a large read into writable memory and pivot `rsp` there.
3. Deliver a second frame plus continuation data.
4. Second frame: invoke a permissive memory syscall or direct ORW sequence, respecting the target ABI's register order.
5. Continue into shellcode or a syscall-only chain.

Validate every frame field against the architecture and actual syscall entry. A plausible-looking frame with misplaced arguments silently fails.

## UAF Callback Overwrite

For menu programs with freed objects, inspect whether a later allocation of the same size reuses the chunk and can replace a function pointer:

1. Allocate an object containing a callback.
2. Free it while retaining an index or pointer.
3. Allocate controlled data in the same size class.
4. Place the target function address at the callback offset.
5. Invoke the stale object's method.

Confirm allocator reuse and structure layout dynamically; add grooming only when the simple same-bin reuse is unreliable.

## Raw eBPF Program-Array Execution

If an accessible `BPF_MAP_TYPE_PROG_ARRAY` contains a privileged or flag-reading program, execution may be possible through a tail call even when the original program handle is inaccessible.

Without libbpf/BCC:

1. Use the `bpf()` syscall to create or load a minimal trampoline program.
2. Obtain the accessible map FD from the challenge environment.
3. Emit eBPF instructions that load the map reference and call `bpf_tail_call(ctx, map, index)`.
4. Attach or run the trampoline through an allowed program type/hook.
5. Capture output from the target program's expected channel.

Construct instructions with explicit opcode, destination/source registers, offset, and immediate fields. Read the verifier log on every load failure. Validate kernel version and permissions before assuming a verifier bypass is required.

Source basis: reusable abstractions from the DalCTF 2026 organizer writeups, <https://github.com/DalCTF/DalCTF2026>.
