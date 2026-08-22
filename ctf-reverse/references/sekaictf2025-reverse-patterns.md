# SekaiCTF 2025 — Reverse Patterns

Source: https://github.com/project-sekai-ctf/sekaictf-2025. Extracted from author solution writeups/scripts under `reverse/*/solution/`.

---

## 1. AVX512 ternary-logic checker as a Boolean circuit (`what-in-ternation`)

**Pattern:** A checker expands each input bit into SIMD lanes, then uses mostly `vpternlogd` plus `vpermb` / `vpermi2b` shuffles. This is usually not numeric SIMD; it is a Boolean circuit encoded in vector instructions.

**Recon / Detect:** AVX512-heavy program where final success depends on one low bit, with many `vpternlogd` immediates and byte-permutation instructions. Inputs become 0/1 bytes or bits spread across ZMM registers.

**Exploit / Solve:** Disassemble only the checker range with `iced-x86`/Capstone. Model each ZMM register as a list of Z3 `Bool`s. Implement `vpternlogd` immediates as Boolean formulas, shuffles as list permutations, and stack stores/loads as register snapshots. Constrain final output bit to true and ask Z3 for a model.

**Tell:** If the instruction set is small and repetitive, emulate the IR into constraints instead of single-stepping all possible inputs. `vpternlogd imm` is a truth-table gate; `vpermb` is wiring.

## 2. Windows CFG/XFG table as maze walkability (`miku-music-machine`)

**Pattern:** Control Flow Guard / eXtended Flow Guard is used as challenge logic. A grid of function pointers represents cells; moving into an invalid cell calls a function removed from the CFG/XFG valid-target table, causing process termination.

**Recon / Detect:** Windows PE, indirect calls through a `cells[]` array, many near-identical `cell<N>` functions, crashes with `STATUS_STACK_BUFFER_OVERRUN` on some moves, and load-config CFG/XFG metadata present.

**Exploit / Solve:** Dump CFG/XFG valid targets (`dumpbin /loadconfig`, PE parser, or IDA/Ghidra load config). Cells present in the table are passable; missing ones are walls. Identify switches by finding `cell<N>` bodies containing `xor byte ptr [rip+offset], imm` instead of NOP padding; map target offsets to the low byte of another cell's XFG hash. BFS/shortest-path search the maze while toggling gates, then encode directions into the expected 2-bit input and apply any final XOR mask.

**Tell:** Security mitigations can be intentionally repurposed as an oracle/state machine. A CFG/XFG crash is not necessarily anti-exploit; it may be the wall detector.

## 3. Compiler AST/plugin challenge as resource-flow + ILP/golf (`alchemy-master`)

**Pattern:** A compiler plugin hooks MSVC internals (`ReadFunction`, `tagFUNC*`) and scores AST tuple kinds as reactions in an alchemy/resource game. The input is source code; the solver must produce specific compiler node counts.

**Recon / Detect:** Plugin DLL, MSVC PDB symbols are useful, logic iterates AST/function tuples, and challenge output is material/count based rather than direct string checking.

**Exploit / Solve:** Hook or instrument the same compiler function while compiling small C++ snippets to map tuple-kind IDs to constructs. In this writeup: `2130=SimpleStmt`, `2201=FunctionCallStmt`, `2210=ThrowStmt`, `2156=ReturnStmt`, with harder alternatives such as `2327=DestructorEHBlock` and epilogue-related nodes. Model material conversions as linear constraints/ILP, then hand-golf source lines to hit exact counts under compiler constraints.

**Tell:** When source code is the input to a compiler/plugin challenge, generate a dictionary of syntax construct -> internal node sequence first, then solve counts. Do not reverse every AST node manually.

## 4. Android APK API HMAC from signing certificate (`sekaibank-signature`)

**Pattern:** An APK-backed API requires an `X-Signature` header computed from request method/path/body using a key derived from the APK signing certificate hash, not a hardcoded app secret.

**Recon / Detect:** Decompiled Android network client has formula like `HMAC_SHA256(method + "/api" + path + body, sha256(app_signature))`; unauthenticated API replies `X-Signature header is required`.

**Exploit / Solve:** Extract signer certificate SHA-256 (`apksigner verify --print-certs`, `keytool -printcert -jarfile`, or print-apk-signature). Recreate exact canonical string including `/api` prefix and raw JSON body, then send the HMAC hex in `X-Signature`.

**Tell:** If an Android challenge uses request signing, check whether the key is derivable from public APK metadata (certificate digest/package signature) before hunting secrets in code.
