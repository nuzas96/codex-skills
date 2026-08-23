# Legacy Evidence Lessons

Load this reference when source history, uploads, tokens, internal pivots, or ambiguous remote behavior dominate.

- Save HTML/JavaScript first; extract routes, actions, fetch calls, generated IDs, keys, and internal hostnames before broad fuzzing.
- Establish a random-path soft-404 control and filter discovery by body/word/size, not status alone.
- Treat exposed Git, backups, credentials, OpenAPI data, and client keys as starting evidence. Validate them against the intended service and protected behavior.
- Diff GET/POST and baseline/payload responses to discover dynamic upload/result paths.
- Decode sessions/tokens before forging; identify serializer, algorithm, key source, claims, accepted key URLs, and the protected effect.
- Use parser/LFI errors to learn wrappers, path constraints, logging paths, and deployment differences.
- Confirm command execution with deterministic output; a callback or uploaded file alone is not proof.
- After a scoped foothold, inspect repository history, `/etc/hosts`, loopback/private services, proxy configuration, and source notes before repeating public recon.
- Do not assume leaked source and the live deployment match; verify version and behavior empirically.

