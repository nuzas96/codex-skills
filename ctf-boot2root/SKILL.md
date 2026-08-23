---
name: ctf-boot2root
description: "Solve authorized Boot-to-Root, VulnHub, HTB-style, and CTF machine challenges through the complete lifecycle: VM/network discovery, full service enumeration, foothold, credential reuse and pivoting, lateral movement, Linux or Windows privilege escalation, and reproducible user/root or system proof. Use with ctf-solve for whole scoped-machine objectives."
---

# CTF Boot2Root — V2 Router

Use `ctf-solve` for progress and evidence discipline. This skill owns the machine lifecycle that spans several services and access levels.

## Lifecycle

1. Confirm scope, target addressing, networking mode, and whether offline disk extraction is forbidden.
2. Discover the host and run full TCP enumeration before concluding the attack surface is small; add targeted UDP only when evidence warrants it.
3. Enumerate every exposed service independently and record versions, hostnames, redirects, shares, and authentication policy.
4. Build the smallest verified foothold and prove identity, host, working directory, and command channel.
5. Enumerate local identities, credentials, routes, listeners, services, shares, containers, and internal hosts; pivot only within stated scope.
6. Evaluate privilege paths in configuration-first order, using kernel/native exploitation only when evidence supports it.
7. Prove each access transition and retrieve user/root or system objectives from their real paths.

Read [references/lifecycle.md](references/lifecycle.md) for the complete enumeration-to-proof workflow. Read [references/legacy-evidence-lessons.md](references/legacy-evidence-lessons.md) for preserved field lessons.

## Focused category pivots

- Web application foothold -> `ctf-web` for the web primitive, then return here for host lifecycle.
- Native local/kernel exploit -> `ctf-pwn` for exploit construction.
- Binary or custom service semantics -> `ctf-reverse`.
- AD domain path -> `ctf-misc/references/active-directory.md` while this skill retains host-level lifecycle ownership.
- Disk/memory evidence rather than live compromise -> `ctf-forensics`.

Do not activate every category speculatively. Add one only when the observed blocking primitive requires it.

## Completion

Complete only after recording the exact discovery, foothold, lateral/pivot steps if any, privilege-escalation cause, effective identity proof, and user/root or system flag provenance.
