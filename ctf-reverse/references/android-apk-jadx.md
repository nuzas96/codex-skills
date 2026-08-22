# Android APK Reverse Engineering (JADX / apktool)

Use when a CTF supplies an APK or Android application and the primary blocker is understanding app logic, resources, manifest components, Java/Kotlin code or embedded native libraries.

## First Pass

1. Identify package/version/min/target SDK and APK structure.
2. Decode `AndroidManifest.xml` and resources with apktool/aapt.
3. Decompile Java/Kotlin with JADX.
4. Search for challenge-relevant strings, URLs, flags, crypto, native methods and hidden components.
5. Trace from UI/intent entry point to the flag-relevant routine rather than reading every class.

## Manifest / Component Triage

Record:

- activities, services, receivers, providers;
- exported state and required permissions;
- intent filters/deep links;
- application class;
- debuggable/backup/network security config;
- native libraries under `lib/<abi>/`.

Target SDK matters because Android component/export/security defaults change across versions.

## JADX Workflow

Use JADX source as a semantic aid, not authoritative bytecode. If decompilation looks broken:

- compare smali from apktool;
- inspect method bytecode/control flow;
- disable/adjust deobfuscation assumptions;
- search usages/xrefs from strings/resources/components.

High-value searches include `Cipher`, `SecretKeySpec`, Base64, native/JNI calls, HTTP clients, hardcoded paths, SharedPreferences, assets/raw resources and challenge-specific terms.

## Obfuscation

For renamed classes/methods, anchor on stable APIs, resource IDs, string decryptors, manifest component names and call relationships. Recover the central string decoder instead of manually renaming the entire app.

## Native Libraries

If the important routine crosses JNI into `.so`, switch that subproblem to `ghidra-native.md` (or other native tooling). Track the Java native method signature to the exported/registered JNI function.

## Malware Context

If the APK is malicious, this reference still owns Android program structure/tooling. Return decoded endpoints/config/behavior to `ctf-malware` for malware-specific interpretation.

## Common Failure Modes

- Reading thousands of JADX classes before following the UI/component entry path.
- Trusting malformed decompiler output over smali.
- Ignoring resources/assets because the Java looks obfuscated.
- Missing JNI/native logic.
- Applying current Android exported-component assumptions without checking target SDK.

## Provenance

Consolidated from the original Apache-2.0 `reverse-engineering-android-malware-with-jadx` skill and existing `ctf-reverse` Android/platform notes. Original source remains on `archive/pre-restructure-20260823`.
