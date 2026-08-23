# Legacy Evidence Lessons

Load when exploit reliability, unusual architecture, integer logic, seccomp, or stateful protocols dominate.

- Derive offsets from frame layout and verify with cyclic/core evidence; never transplant addresses across unproven builds or PIE states.
- Check integer multiplication, signedness, negative lengths, quantities, balances, and truncation before assuming memory corruption.
- Decode seccomp BPF and verify syscall numbers for the actual ABI; forgotten modern syscalls may be the intended route.
- Preserve confirmed leak stages when later heap manipulation crashes. A leak does not validate poisoning or final control.
- Model stateful buckets/collisions and object layouts; a crash is not proof of pointer control.
- For unusual architectures or size-golfing services, verify loader, ABI, syscall convention, encoded input constraints, and exact byte length locally.
- Exploit scripts should support local/remote modes, supplied loader/libc, strict prompt synchronization, defensive leak parsing, assertions, and bounded post-exploitation checks.

