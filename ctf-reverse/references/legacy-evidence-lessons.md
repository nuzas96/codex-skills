# Legacy Evidence Lessons

Load for validators, layered APK encodings, custom VMs, flattened control flow, or strict remote protocols.

- Work backward from the genuine compare/success sink; dump referenced constants and validate recovered input against the unpatched checker.
- Reconstruct stack strings and PRNG/XOR/per-byte transforms in a standalone script instead of eyeballing strings.
- For APK layers, identify the responsible activity/class/DEX and test UTF-8 versus UTF-16 endianness explicitly.
- For flattened or anti-debug checkers, break immediately before comparison, dump expected/actual buffers, then explain the transformation.
- For custom VMs, recover dispatch and compare semantics, observe per-index expectations when useful, then emulate only the required instruction set.
- Parser errors can reveal structured input fields, nesting, and types; mutate one path at a time.
- Confirm opcode bytes and surrounding disassembly before patching; account for PIE and tool syntax.
- A local success marker or patched branch is not proof of the genuine flag or remote acceptance.

