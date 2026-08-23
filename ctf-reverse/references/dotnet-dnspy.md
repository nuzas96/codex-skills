# .NET Reverse Engineering (dnSpy / ILSpy / de4dot)

Use when the target is a managed .NET assembly (C#, VB.NET, F#) and the main task is to recover program logic, string/config decoders, resources or validation routines.

## Identification

Confirm CLR metadata / `mscoree.dll` / COM descriptor rather than relying on PE appearance alone. Identify framework/runtime and likely obfuscator with tools such as Detect It Easy.

## Workflow

1. Open in dnSpyEx/ILSpy and go to the managed entry point.
2. Map namespaces/classes/resources before reading individual methods.
3. Search string literals, resource access, crypto/network/file APIs and challenge markers.
4. Trace validation/decryption/config routines through xrefs/usages.
5. If obfuscated, remove only the layer blocking analysis.
6. Cross-check confusing decompiler output with IL.

## Obfuscation

Common protections include renaming, encrypted strings/resources, control-flow flattening, proxy calls, anti-debug/anti-tamper and virtualization/native stubs.

`de4dot` can help with older/common protectors, but do not assume it supports every current variant. Always compare the cleaned assembly's relevant behavior with the original.

## Resources and Static Config

Managed assemblies often keep important challenge data in:

- `.resources` / embedded files;
- static fields/constructors;
- Base64/encrypted string blobs;
- application settings/config;
- serialized resources.

Use IL (`ldstr`, field initialization, resource APIs) when high-level decompilation hides where a value originates.

## Debugging

For CTFs, use the debugger only when a specific runtime value cannot be recovered statically. Break at a string/config decoder or validation boundary, inspect arguments/return value, record the result, and return to offline reasoning.

## Native Boundary

If a managed method P/Invokes or loads a native DLL containing the real logic, pivot that function to native reverse tooling. Keep the managed caller/signature as context.

## Malware Context

For malicious .NET samples, this file owns managed-code mechanics. C2/config/staging behavior belongs to `ctf-malware` after the relevant routines are understood.

## Common Failure Modes

- Treating all PE files as native and missing CLR metadata.
- Trusting decompiled C# when IL shows different control flow/types.
- Running de4dot blindly and assuming the output is semantically identical.
- Ignoring embedded resources/static constructors.
- Debugging the whole program instead of the one decoder/validator needed.

## Provenance

Consolidated from the original Apache-2.0 `reverse-engineering-dotnet-malware-with-dnspy` skill and existing `ctf-reverse` .NET/platform notes. Original source remains on `archive/pre-restructure-20260823`.
