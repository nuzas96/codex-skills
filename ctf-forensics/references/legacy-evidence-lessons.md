# Legacy Evidence Lessons

Load for damaged SQLite/WAL, VHD/NTFS recovery, pixel paths, Android backups, USB HID, or fragment assembly.

- A zero-byte SQLite database may make WAL/sidecar data primary evidence. Validate headers, carve measured structures, reconstruct pages, and use recovery/raw b-tree methods as appropriate.
- Repair GPT/NTFS/container structure from backups before blind carving; preserve runlists, cluster chains, deleted-record provenance, and CRCs.
- Pixel-locality hints imply a traversal/permutation hypothesis. Determine dimensions, tiling, channels, adjacency, and seed source before generic stego brute force.
- Keep traversal seed and encryption keystream derivation separate; save inspectable channel planes, masks, traversal images, and decoded streams.
- For raw/LiME memory, begin with exact marker offsets and bounded carving, then escalate to framework plugins if the dump supports them.
- Decode USB HID reports in capture order and preserve raw reports beside reconstructed text.
- For Android backups, preserve the chain password/key derivation -> decrypt -> decompress -> app DB/WAL/DEX -> validated database parameters.
- Never fill missing multi-fragment bytes or visually plausible UUID characters by guessing.

