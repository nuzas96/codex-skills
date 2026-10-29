# Static AVR GPIO signal recovery

Use this when AVR firmware visibly drives GPIO pins or LED outputs and the simulator is unavailable or unnecessary. Treat the output signal as a hypothesis to validate, not as proof that the firmware emits a flag.

## Workflow

1. Preserve the original HEX/ELF and hash it. Check Intel HEX record checksums and load addresses before interpreting code. Identify the MCU when possible; I/O addresses and register meanings are device-specific.
2. Run `avr-objdump -h -d -S firmware.elf` (or disassemble a reconstructed ELF) and inspect data with `avr-objdump -s -j .data`. Start with the reset/main path, not every instruction.
3. Map `DDRx`, `PORTx`, and `PINx` addresses using the matching MCU documentation. Find setup writes that make a pin an output, then follow repeated `out`, `sts`, `sbi`, and `cbi` operations and their controlling branches. Exclude unrelated timer, stack, and status-register writes.
4. Trace the bit source and loop order: shifts/bit masks reveal MSB-first versus LSB-first; conditional set/clear paths reveal polarity. A logical one may drive the pin low (active-low). Record the assumed idle level and whether the first transition is a data bit or framing.
5. Follow delay calls/loops and count output slots. Fixed slot durations suggest a bit clock; data-dependent delays, pulse-width encoding, framing, or transitions only on changes require separate timing analysis. Do not infer bytes from transition count alone.
6. Reconstruct candidate bits under explicit polarity, phase, bit-order, and framing assumptions. Keep each candidate tied to the instructions that support it. Check for printable/structured output and independently compare against another known observation or a simulator only when available.
7. If the bytes do not validate, revisit register mapping, branch polarity, sample phase, idle/start/stop bits, byte order, clock divider, and whether the output is actually a serial encoding. Report ambiguity rather than choosing a flag-looking string.

## Limits and false positives

- `out` can target non-GPIO I/O registers; use the correct MCU register map and nearby `DDRx` evidence.
- GPIO writes can implement control signals, delays, buses, or debugging LEDs rather than answer data.
- Optimized C may move constants into flash/PROGMEM, inline loops, combine writes, or use different instructions; locate control flow rather than relying on one opcode pattern.
- Static disassembly alone may not resolve indirect calls, runtime-generated data, interrupts, peripheral timing, or externally driven inputs. Use a bounded simulator/emulator or logic capture when those facts affect the decode.
- A method validated on a few fixtures is not a general-purpose decoder. Preserve alternate interpretations until a verifier or independent observation resolves them.

## Development validation

The associated regression examples are authored benign ATmega328P programs with known output, compiled using avr-gcc. They exercise different GPIO ports, bit directions, active levels, and delay shapes. Their test vectors are not challenge data. This reference records a static-analysis workflow, not a claim of automatic decoding across AVR firmware.

## Sources

- Microchip, [ATmega328P datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf), I/O port configuration and register descriptions; use the target MCU's own datasheet when the part differs.
- GNU Binutils, [`objdump` documentation](https://sourceware.org/binutils/docs/binutils/objdump.html), disassembly/source display options.
- avr-libc, [`<util/delay.h>` reference](https://www.nongnu.org/avr-libc/user-manual/group__util__delay.html), busy-wait delay and `F_CPU` assumptions.
