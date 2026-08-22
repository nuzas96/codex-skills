# iOS Runtime Reverse Engineering with Frida

Use when an iOS CTF app requires runtime method discovery/tracing or a specific value/branch is easier to observe dynamically than recover statically.

## Static Before Dynamic

Identify binary architecture, Objective-C/Swift classes/symbols, strings and the likely validation/crypto/network routine first. Frida should answer a concrete question, not replace all static analysis.

## Runtime Enumeration

For Objective-C-compatible classes, use the ObjC runtime to enumerate matching classes and `$ownMethods`. For Swift, identify bridged classes or exported/mangled symbols and demangle names where possible.

`frida-trace` is useful to discover calls matching a narrow class/method pattern. Avoid tracing every method in a large app.

## Hooking Workflow

```text
static clue / target method
 -> attach/spawn app
 -> log arguments/return values
 -> correlate with UI/action
 -> capture one hidden runtime value or branch decision
 -> reproduce it offline when possible
```

Record method signature and type conventions. Objective-C hook arguments begin with `self` and selector before explicit parameters.

## Native APIs

When the app uses CommonCrypto/Security/native helpers, hook only the exact API needed to learn algorithm parameters or data flow. Avoid dumping unrelated sensitive runtime state.

## Swift Notes

Pure Swift code may not be exposed through `ObjC.classes`. Use symbols/exports/static xrefs and Frida interceptor addresses based on the actual binary. Swift mangling/runtime layouts vary; do not copy symbol names from another build.

## Static Complement

Ghidra/Hopper/IDA can locate native functions and xrefs; Frida can validate runtime values. Use both directions:

- static -> runtime: verify hypothesis;
- runtime -> static: identify address/method, then understand surrounding logic.

## Common Failure Modes

- Starting with broad runtime secret dumping instead of a challenge-specific method.
- Assuming all Swift classes are Objective-C visible.
- Copying offsets/symbols between builds.
- Modifying return values before first recording original behavior.
- Failing to reproduce the discovered algorithm/value offline.

## Provenance

Consolidated from the original Apache-2.0 `reverse-engineering-ios-app-with-frida` skill and existing `ctf-reverse` mobile/dynamic notes. Original source remains frozen on `archive/pre-restructure-20260823`.
