# Legacy Evidence Lessons

- If an initial scan is empty, verify VM networking and run a full TCP scan before changing hypotheses.
- Enumerate separate web ports independently and follow redirects/vhosts.
- Check FTP hidden files, SMB/NFS shares, site images, and backups before password attacks.
- Validate credentials against named in-scope accounts/services and retain their source.
- After foothold, prioritize configured privilege paths (`sudo`, SUID/capabilities, services, cron/timers, writable paths, local listeners) before kernel exploits.
- Root scripts that reconstruct and execute process command lines can permit argument injection; prove the exact execution transformation.
- Root jobs copying user-controlled trees may preserve dangerous modes or change ownership; verify the actual copy semantics.
- Sudo wildcard/path rules can cross argument boundaries or dereference symlinks; audit the exact argv match and target open behavior.
- `stat`/`access` followed by `open` can create TOCTOU opportunities; prove the race and use bounded automation.
- A password prompt, callback, mutated binary, or partial shell is not privilege proof. Require effective identity or protected-file access.
- Keep pivots scoped and document internal routes and tunnels.

