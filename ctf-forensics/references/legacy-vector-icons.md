# Legacy Rez and Haiku Vector Icons

Use this reference when a classic Mac Rez resource definition contains a `VECTOR:ICON` resource or hex data whose first decoded bytes are `ncif`.

## Recognize and extract

- In Rez text, look for a declaration such as `resource(35,"VECTOR:ICON") #'VICN' array { ... }` and `$"..."` hexadecimal string chunks.
- The hex bytes `6E 63 69 66` decode in order to the four ASCII bytes `ncif`, the HVIF signature. Do not reverse the bytes or infer lengths from host endianness.
- Extract the resource's hex strings in source order and validate the decoded signature before choosing an HVIF parser. A Rez resource ID is not the payload length.

The parameterized helper extracts one resource and rejects ambiguous IDs, odd-length or non-hex strings, missing signatures, and truncated resource blocks:

```bash
python3 "$HOME/.codex/skills/ctf-forensics/scripts/extract_hvif_rdef.py" \
  suspect.rdef extracted.hvif [--resource-id ID]
```

## Validate and render

`icon2icon` in [`threedeyes/hvif-tools`](https://github.com/threedeyes/hvif-tools) converts HVIF to SVG or PNG and reports parse failures:

```bash
icon2icon extracted.hvif preview.svg
icon2icon extracted.hvif preview.png --width 512 --height 512
```

The tool does not extract Rez resources; run the helper first. Its general `icon2icon` target builds on Linux with CMake 3.16+, a C++11 compiler, and the repository's NanoSVG/STB submodules. The separate `iom2hvif` converter is Haiku-only; do not mistake that platform-specific tool for a requirement of `icon2icon`. The project is MIT-licensed. Verify the converter's exit status and inspect the rendered output; the signature alone does not prove the complete vector stream is valid.

If `icon2icon` is unavailable, keep the raw resource intact, confirm the signature and byte count, then inspect the HVIF parser/format source or use another verified HVIF reader. Do not start by manually reverse-engineering every byte. A converter error is a parse/validation failure, not proof that the extraction byte order is wrong; compare resource chunk order and lengths before changing them.

## Provenance and limits

- [PRONOM fmt/1791: Haiku Vector Icon Format](https://www.nationalarchives.gov.uk/PRONOM/fmt/1791) identifies HVIF as a vector image format associated with Haiku and notes encoded icons in `.rdef` files; its record lists a source date of 2022-10-25. Search-indexed PRONOM content was available after the page's direct request returned HTTP 403.
- [`hvif-tools` README and MIT license](https://github.com/threedeyes/hvif-tools): source reviewed at commit `3789a261230fd6faad0dfda3b7b2743a2d878125` (retrieved 2026-10-29). A local Linux build and conversions were tested; upstream README feature claims are not treated as proof without execution.
- The extractor is original parameterized code and contains no challenge-specific IDs, payloads, or answers.
