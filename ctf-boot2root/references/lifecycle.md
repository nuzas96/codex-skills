# Boot2Root Lifecycle

## 1. Scope and network discovery

- Confirm authorized target/range and challenge rules.
- Verify attacker interface, route, ARP/neighbor state, NAT/host-only/bridged mode, and target IP.
- Use host discovery appropriate to the local segment, then a full TCP scan followed by targeted service/version scripts.
- Record vhosts, redirects, certificates, hostnames, and unusual ports. Do not declare a host unreachable from a top-ports scan alone.

## 2. Service enumeration and foothold

- HTTP(S): inspect each port, vhosts, source/assets, backups, repositories, credentials, upload/auth flows, admin panels, and APIs.
- FTP/SMB/NFS: test allowed anonymous/guest access, enumerate hidden files/shares/exports, and preserve credential or key provenance.
- SSH/WinRM/RDP/databases/admin tools: determine authentication policy and test only evidence-backed credentials.
- Inspect clue-bearing media with metadata/strings/container tools when the challenge makes it part of access discovery.
- Prove a foothold with effective identity, hostname, working directory, and a stable command response.

## 3. Post-foothold and movement

- Enumerate users/groups, homes, shell/environment, OS/kernel, credentials/config/history, processes, listeners, routes, mounts, containers, and internal hosts.
- Test credential reuse deliberately across in-scope services only when source or hints support it.
- For pivots, document the route, tunnel/proxy command, internal target, and scope justification.
- Treat lateral movement as a new access transition requiring identity and host proof.

## 4. Privilege escalation

Check configuration-first:

1. `sudo -l`, sudo version, and argument/path/environment constraints;
2. SUID/SGID and file capabilities;
3. cron, timers, services, writable scripts/directories, PATH and environment loading;
4. secrets/configuration, local databases, service credentials, sockets, backups, and mounts;
5. containers/virtualization boundaries;
6. kernel/CVE or native exploitation only when exact version and constraints support it.

For every candidate record privileged owner/context, attacker-controlled input, trigger, harmless proof, and rollback/side effect. A SUID binary or writable file is only a lead until execution flow is proven.

## 5. Proof and writeup

- Confirm effective UID/root or SYSTEM/Administrator identity before claiming success.
- Read objectives from their actual protected locations through the verified primitive.
- Preserve user and root/system flag provenance separately.
- Record failed techniques and why they failed.
- Do not bypass the intended live route by offline mounting/extraction when forbidden.

