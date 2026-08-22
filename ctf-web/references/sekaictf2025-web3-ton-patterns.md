# SekaiCTF 2025 — Web3 / TON Patterns

Source: https://github.com/project-sekai-ctf/sekaictf-2025. Extracted from `blockchains/ticket-master/solution/README.md` and related blockchain challenge notes.

---

## 1. TON `addr_var` vs `addr_std` address-encoding bypass (`ticket-master`)

**Pattern:** TON smart-contract code compares address slices with `equal_slices_bits`, but TON supports multiple address encodings. The data bits can compare differently even though message delivery normalizes `addr_var` destination addresses to `addr_std`.

**Recon / Detect:** FunC / TON challenge, checks involving `equal_slices_bits(recipient, account::coin_minter)` or similar raw-slice address comparison, and older `@ton/sandbox` / `@ton/core` versions.

**Exploit / Solve:** Encode the protected minter/target address as `addr_var` to bypass the raw slice comparison. When the internal message is delivered, `addr_var` in `dest` is automatically replaced/normalized to `addr_std`, so the message still reaches the intended account.

**Version Caveat:** This primitive is version-specific. Since TON global version 10, `addr_var` is not allowed in external-message `dest`, and `LDMSGADDR(Q)` / `PARSEMSGADDR(Q)` no longer support `addr_var`. Verify challenge dependency/global versions before committing to it.

**Tell:** When an address check compares serialized slices rather than canonical account identity, try alternate encodings and parser/version differences.

## 2. User-controlled forward payload as arbitrary internal-message gadget (`ticket-master`)

**Pattern:** A redemption/exchange function builds a safe default payload only when the caller supplies no payload. If a payload is present, it parses `response_address` and `forward_payload` from attacker-controlled data, turning a benign service counter into an arbitrary internal-message sender.

**Recon / Detect:** Code shape:

```func
if payload.cell_null?() {
    forward_payload = begin_cell().store_op(op::message) ... .end_cell();
} else {
    slice payload = payload.begin_parse();
    response_address = payload~load_msg_addr();
    forward_payload = payload~load_ref();
}
```

**Exploit / Solve:** Supply a payload whose response address is the minter/target and whose forward payload is a mint/admin operation. In `ticket-master`, this lets the service counter mint enough tickets for the exploit contract, then exchange for the flag.

**Tell:** In smart-contract CTFs, any optional callback/forward-payload feature should be audited as a confused-deputy message gadget: who sends the message, to whom, with what op body, and whose authority is checked?
