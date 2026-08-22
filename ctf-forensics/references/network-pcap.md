# Network / PCAP Forensics

Use when the challenge provides PCAP/PCAPNG, network traces, USB-over-packet capture, TLS/HTTP/DNS/SMB traffic, or when a protocol stream must be reconstructed.

## First Pass with tshark/Wireshark

1. `capinfos` / file metadata: packet count, duration, capture interfaces and link type.
2. Protocol hierarchy and endpoint/conversation statistics.
3. Identify dominant/unusual protocols, hosts, ports and time windows.
4. Follow/reassemble the smallest relevant stream.
5. Export protocol objects only when that protocol actually carries files.
6. Preserve raw bytes for custom protocols/encodings.

Do not start by scrolling every packet in Wireshark.

## Useful Views

- DNS queries/responses and label lengths.
- HTTP methods/hosts/URIs/headers/bodies.
- TLS SNI, certificates and handshake metadata.
- TCP stream indices and retransmission/order.
- SMB/FTP/HTTP exported objects.
- plaintext auth only when protocol supports it.
- packet timestamps/inter-arrival times for timing channels.

## CTF-Specific Pattern Classes

### Stream reconstruction

Use `follow,tcp,...` or targeted fields. If data crosses packets, reassembly order matters; never decode each packet payload independently unless the protocol frames allow it.

### DNS covert channels

Look for long/high-entropy labels, unusual query volume, sequential subdomains, record-type changes and timing. Establish normal domain traffic first.

### Timing channels

Export timestamps and plot/difference inter-packet intervals. A binary/covert timing channel often appears as distinct latency clusters. Avoid reading timing bits by eye for large captures.

### Encoded/custom protocol

Infer framing from repeated lengths/magic/commands. Save stream bytes and write a small parser. If encryption appears, move only the crypto step to `ctf-crypto` after framing is understood.

### Peripheral captures

USB HID, Bluetooth and MIDI packets may require device/report reconstruction rather than ordinary network interpretation. Route to `peripheral-capture.md` when report bytes encode keyboard/mouse/grid state.

## Object Extraction

`tshark --export-objects` works for supported protocols but validate extracted files by magic and hashes. For unsupported/custom transfers, reconstruct the correct stream and strip protocol framing manually.

## TLS

Encrypted application data is not automatically a dead end. Look for provided key logs, RSA keys (legacy cases), session secrets, browser artifacts or application-level keys elsewhere in the challenge. SNI/certificates/timing remain visible even without decryption.

## Baseline Before 'Suspicious'

Ports such as 1337/4444 or long DNS names are not proof by themselves. In CTFs, prioritize challenge-specific anomalies: unique host, protocol only used once, sudden burst, embedded flag marker, or traffic tied to another recovered artifact.

## Common Failure Modes

- Reading packets individually instead of reassembling streams.
- Exporting every object before narrowing the time/host/protocol.
- Treating an unusual port as proof of malicious traffic.
- Ignoring capture link type/interface and parsing payload at wrong offsets.
- Missing covert data in timing, TCP flags, DNS labels or peripheral report bytes.
- Switching to crypto before reconstructing exact ciphertext/framing.

## Provenance

Consolidated from the original `performing-network-forensics-with-wireshark` Apache-2.0 skill and existing `ctf-forensics/network*.md` references. Original source remains frozen on `archive/pre-restructure-20260823`.
