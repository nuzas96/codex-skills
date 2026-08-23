# Rust Binary Reverse Engineering

Use when a native target is Rust-compiled and Rust-specific layout/boilerplate makes ordinary C-style decompilation misleading.

## Recognition

Useful indicators include `core::panicking`, `std::rt::lang_start`, panic/unwrap strings, Cargo registry paths, mangled Rust symbols and statically linked standard-library code.

## Why Rust Looks Different

- binaries are often large because std/crates are statically linked;
- monomorphization creates many specialized generic functions;
- `Result`/`Option` and panic paths add control-flow noise;
- `String`/`Vec`/`&str` use pointer/length/capacity-style layouts rather than C null termination;
- async/Tokio code can obscure the logical call chain.

Do not mistake library boilerplate for challenge logic.

## Workflow

1. Confirm Rust indicators and architecture.
2. Extract surviving crate/path/symbol strings for dependency clues.
3. Find user-code anchors through challenge strings, network/file APIs, input parsing and success/failure paths.
4. Demangle/rename relevant Rust symbols where available.
5. Model fat pointers/slices/Vec/String correctly when decompiler types are wrong.
6. Ignore panic/drop/allocator glue unless it affects control flow.
7. Reference-compile a tiny Rust snippet when you need to recognize a runtime/container pattern.

## Crate Clues

Crate names can quickly suggest functionality (`reqwest`, `tokio`, `aes`, `chacha20`, `serde`, etc.), but they are hints only. Trace actual callers before concluding a capability is used.

## Strings

String literals are contiguous bytes but references often carry explicit length. A decompiler may display adjacent strings as one C string or miss boundaries. Use xrefs plus pointer/length arguments rather than null terminators alone.

## Common CTF Patterns

- validation hidden behind iterator/combinator chains;
- static tables/resources referenced through slices;
- serde JSON/config parsing;
- async state-machine boilerplate around a small core routine;
- custom crypto expressed through crate abstractions.

## Common Failure Modes

- Reading std/runtime functions instead of user code.
- Treating Rust strings as C strings.
- Interpreting every imported crate as active challenge logic.
- Fighting decompiler-generated `Result`/drop glue instead of tracing data dependencies.
- Assuming symbols always survive stripping.

## Provenance

Consolidated from the original Apache-2.0 `reverse-engineering-rust-malware` skill and existing `ctf-reverse` Rust/language notes. Original source remains on `archive/pre-restructure-20260823`.
