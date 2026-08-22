# ljagiello/ctf-skills Local Library

Session learning: the external `ljagiello/ctf-skills` repo is useful as a category-specific CTF reference library, but it should be loaded on demand to keep token cost low.

## Installed layout

The repo is installed as a local git clone at:

```text
/home/nuzhmi/.hermes/skills/ctf-skills
```

Hermes sees these local skills:

- `solve-challenge` — dispatcher/triage when the category is unclear
- `ctf-web` — HTTP apps, APIs, browser/client, auth, SQLi, XSS, SSTI, SSRF, XXE, JWT, uploads, deserialization-adjacent web chains
- `ctf-pwn` — native memory corruption, shellcode, ROP, heap, format strings, seccomp/kernel/sandbox escape once the bug class is known
- `ctf-reverse` — compiled/packed/obfuscated targets, APK/WASM/firmware/custom VM/bytecode, anti-debug, dynamic instrumentation
- `ctf-crypto` — RSA/AES/ECC/PRNG/lattices/ZKP/hash/MAC/math crypto attacks
- `ctf-forensics` — PCAP, disk/memory images, stego, logs, Volatility, deleted file recovery, signal/audio/video artifacts
- `ctf-misc` — fallback for pyjails, bash jails, encodings, RF/SDR, Unicode, games, esolangs, weird hybrid puzzles
- `ctf-osint` — geolocation, public-source investigation, DNS/archive/social/user enumeration
- `ctf-malware` — C2 traffic, obfuscated scripts, PE/.NET malware-like configs, YARA/shellcode/malfind workflows
- `ctf-ai-ml` — adversarial ML, model extraction, prompt injection, LLM/LoRA/model puzzles
- `ctf-writeup` — final structured writeup after solve

## Loading policy

Do not preload all of these. Treat them as a reference shelf:

1. If the category is unclear, load `solve-challenge` first.
2. If the category is clear, load only the matching category skill.
3. Use linked reference files inside the selected skill only when a concrete clue points there.
4. Keep `PROGRESS.md` as the live source of truth; the external skill library informs technique selection, not workspace state.

## Installation/update notes

The repo can be refreshed with:

```bash
git -C /home/nuzhmi/.hermes/skills/ctf-skills pull --ff-only
```

If reinstalling from scratch, clone the repo under a category folder:

```bash
git clone --depth 1 https://github.com/ljagiello/ctf-skills /home/nuzhmi/.hermes/skills/ctf-skills
```

Then verify with:

```bash
hermes skills list | grep -E 'ctf-|solve-challenge'
```

## Pitfall learned

`hermes skills install <raw-SKILL.md>` may prompt for confirmation and/or block community CTF skills because security scanning sees expected CTF content: `pip install`, `sudo mount`, traversal examples, exploit snippets, or allowed Bash tools. Do not encode that as "the installer is broken". The durable workaround is either:

- use `--yes --force --category ctf-skills` only after review, or
- install as a local git clone under `~/.hermes/skills/ctf-skills` and verify via `skills_list` / `skill_view`.

For this user, the local clone route is preferred because it preserves the whole reference tree and supports on-demand linked-file lookup while avoiding repeated install prompts.
