# SekaiCTF 2025 — Misc Patterns

Source: https://github.com/project-sekai-ctf/sekaictf-2025. Extracted from author solution writeups/scripts under `misc/*/solution/`.

---

## 1. Pickle implementation discrepancy payloads (`discrepancy`)

**Pattern:** Python has multiple pickle interpreters/checkers with slightly different edge-case behavior: pure Python `pickle.py`, C `_pickle.c`, and `pickletools` disassembler. Very short malformed payloads can error in one implementation but parse in another.

**Recon / Detect:** Challenge asks for pickle payloads that pass/fail different validators, especially with tiny length limits. Look for triage that runs `pickletools.dis`, `pickle.loads` with pure Python, and C accelerator behavior separately.

**Exploit / Solve:** Generate candidate byte strings and classify them by which implementation errors. Known SekaiCTF 2025 payloads (hex / bytes):

- only `pickletools` errors: `28882e` = `b'(\x88.'`; pickletools complains about non-empty stack after `STOP`, unpicklers ignore it.
- only `pickle.py` errors: `8828652e` = `b'\x88(e.'`; empty `APPENDS` segment makes pure Python look for `append` on the item before `MARK` while C/pickletools continue.
- only `_pickle.c` errors: `4620350a2e` = `b'F 5\n.'`; whitespace in `FLOAT` is rejected by C but tolerated elsewhere.
- `pickle.py` + `_pickle.c` errors: `282e` = `b'(.'`; `MARK` can be returned as a value in pickletools model but not actual unpicklers.
- `pickle.py` + `pickletools` errors: `4931000a2e` = `b'I1\x00\n.'`; C `atoi`-style handling stops at NUL, Python integer parsing rejects `1\x00`.

**Tell:** Do not assume `pickletools` is an exact oracle for runtime behavior. For pickle parser challenges, run all three implementations and diff the exception matrix.
