# Mobile App Runtime / IPC Security for CTFs

Use when an Android/iOS CTF app requires analysis of exported IPC components, runtime trust checks, or TLS pinning that prevents observing the app's challenge protocol. Keep testing limited to the supplied/authorized app and lab device/emulator.

## Ownership

- static APK structure/Java/Kotlin -> `android-apk-jadx.md`;
- iOS runtime method tracing -> `ios-frida.md`;
- native `.so`/Mach-O routines -> `ghidra-native.md`;
- this reference -> mobile security behavior around IPC and transport trust.

## Android IPC / Intents

### Start from Manifest

Enumerate activities, services, receivers and providers with exported state, intent filters and required permissions. Check target SDK because Android export defaults/requirements changed across versions.

For each exported component ask:

1. Can another app invoke it?
2. Is a permission required and what protection level?
3. Does it re-check authentication/authorization internally?
4. Which extras/data URI fields influence object/action selection?
5. Does it return/read sensitive challenge data?

### Minimal Lab Testing

Use ADB/Drozer-style component invocation only against the challenge app/emulator. Change one intent extra/data field at a time and observe whether a protected state/flag path becomes reachable.

Content providers require separate checks for URI permissions, projection/selection/path handling and ownership. If a provider field reaches SQL/path parsing, route that subproblem to the matching Web reference rather than duplicating injection knowledge here.

### PendingIntents / Broadcasts

For PendingIntent, inspect whether it is mutable and how the recipient can influence the wrapped intent. For broadcasts, distinguish explicit vs implicit and permission-protected receivers. The exploitability depends on actual app/SDK semantics, not only "exported=true".

## Mobile TLS Pinning (CTF Observation Use)

When a challenge app's protocol is hidden behind certificate pinning, first identify the implementation:

- Android Network Security Config;
- OkHttp `CertificatePinner`;
- custom `X509TrustManager` / Conscrypt path;
- iOS `NSURLSession` trust challenge;
- TrustKit/Alamofire/custom `SecTrust`.

Prefer static config/code analysis first. In an authorized CTF emulator/device, Objection/Frida can be used to instrument the **specific** validation path so the app's challenge traffic becomes observable. Verify success by confirming the intended app request appears in the lab proxy and that app behavior otherwise remains unchanged.

Do not preload generic universal-hook payloads when one known pinning function can be instrumented directly; library/framework versions change method signatures.

## Runtime Instrumentation Discipline

Use Frida to answer one question: which method makes the trust/IPC decision, which argument controls it, or what request data is sent. Record original behavior before changing return values. Keep hooks target-specific and version-derived.

## Common Failure Modes

- Testing exported components without checking required permissions.
- Assuming `android:exported` semantics without target SDK context.
- Treating every mutable PendingIntent as exploitable without a controllable use path.
- Using a broad TLS hook script when the app uses a custom/native pinning library.
- Confusing transport observation with a vulnerability; in CTFs pinning bypass may simply enable protocol analysis.
- Duplicating SQL/path/browser attack content instead of routing to the owning category/reference.

## Provenance

Consolidated for CTF/lab use from the original Apache-2.0 `testing-android-intents-for-vulnerabilities` and `performing-mobile-app-certificate-pinning-bypass` skills. Complete originals remain frozen on `archive/pre-restructure-20260823`.
