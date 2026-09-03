# Active Directory Intrusion Reconstruction from PCAP

Use this reference when the primary evidence is a **PCAP/PCAPNG** from a Windows Active Directory environment and the job is to reconstruct an intrusion across protocols such as LDAP, Kerberos, WinRM, SMB/SMB2 and HTTP/PowerShell staging.

This is a **forensics-first correlation workflow**. The goal is not to run AD attacks against a live domain. The goal is to prove what the capture actually shows, distinguish observation from inference, and build a defensible attack timeline.

## Recognition signals

Strong signals include several of the following in one capture:

- a host serving Kerberos, LDAP, SMB and/or WinRM, consistent with a domain controller;
- another host initiating repeated directory queries or authentication attempts toward it;
- LDAP Simple Bind traffic, possibly exposing a username/password in plaintext;
- directory enumeration of `sAMAccountName`, `userPrincipalName`, `memberOf`, `userAccountControl`, SPNs or privileged groups;
- a user with `DONT_REQ_PREAUTH` followed by Kerberos AS-REQ / AS-REP traffic;
- HTTP on TCP/5985 or HTTPS on 5986 with WSMan/WinRM semantics;
- SMB access to an attacker-controlled share, especially a reverse-direction file pull from the victim;
- tool/payload names such as Mimikatz or PowerShell script staging;
- HTTP requests for `.ps1`, `.bat`, `.exe`, encoded payloads or second-stage URLs;
- a challenge asking for the **attack chain**, compromised account, payload, persistence, or final recovered secret rather than exploitation of a live AD domain.

Fast route:

```text
PCAP
  -> identify hosts and AD service roles
  -> isolate LDAP authentication/enumeration
  -> decode account-control evidence
  -> correlate Kerberos AS activity
  -> correlate WinRM remote-management session
  -> inspect SMB transfer direction and filenames
  -> recover HTTP/PowerShell staging artifacts
  -> decode nested payloads
  -> build timestamped evidence timeline
  -> separate observed / inferred / unproven claims
```

## Core forensic insight: reconstruct relationships, not isolated packets

An AD intrusion is usually spread across several protocols. One packet rarely proves the whole story.

Treat the capture as a sequence of related evidence:

```text
credential exposure / authentication
        |
        v
directory enumeration
        |
        v
weak-account discovery
        |
        v
Kerberos response suitable for offline attack
        |
        v
remote-management access
        |
        v
post-exploitation tool transfer
        |
        v
payload staging / secondary retrieval
```

The exact chain must come from timestamps, host direction, principals and artifacts in the capture. Do not force every PCAP into this sequence.

## 1. Establish capture scope and host roles

Start with metadata, protocol hierarchy, endpoints and conversations:

```bash
capinfos capture.pcap

tshark -r capture.pcap -q -z io,phs

tshark -r capture.pcap -q -z endpoints,ip -z conv,tcp
```

Then produce a compact AD-oriented view:

```bash
tshark -r capture.pcap \
  -Y 'ldap || kerberos || smb2 || tcp.port==5985 || tcp.port==5986 || http' \
  -T fields \
  -e frame.number -e frame.time_epoch \
  -e ip.src -e ip.dst \
  -e _ws.col.Protocol \
  -e tcp.srcport -e tcp.dstport
```

Infer roles from **service behavior and direction**, not IP address order.

A likely domain controller commonly appears as the host receiving combinations of:

- Kerberos: 88/TCP or UDP;
- LDAP: 389/TCP or UDP;
- LDAPS: 636/TCP;
- SMB: 445/TCP;
- WinRM: 5985/TCP or 5986/TCP;
- DNS: 53;
- other Windows domain services depending on the environment.

Record:

```text
Host A: probable DC because ...
Host B: probable attacker/workstation because ...
Confidence: high / medium / low
```

Do not call a host "attacker" merely because it opens many connections. Tie the role to suspicious authentication, enumeration, payload staging or other challenge evidence.

## 2. Inspect LDAP authentication before directory enumeration

LDAP can provide two different evidence classes:

1. **authentication evidence** - Bind requests/responses;
2. **directory evidence** - searches and returned account attributes.

Inspect LDAP verbosely:

```bash
tshark -r capture.pcap -Y ldap -V > ldap.txt
rg -ni 'bindRequest|bindResponse|resultCode|simple|searchRequest|searchResEntry|sAMAccountName|userPrincipalName|memberOf|userAccountControl' ldap.txt
```

### Plaintext Simple Bind

If an LDAP **Simple Bind** is sent over unencrypted LDAP, the bind name and password can be visible in the capture.

Treat a credential as validated only when the corresponding BindResponse shows success, for example a successful LDAP result code.

Evidence model:

```text
Observed:
- bind identity appears in plaintext
- password field appears in plaintext
- server returns successful bind response

Conclusion:
- the captured credential successfully authenticated to LDAP
```

Do not generalize this to SASL-protected LDAP, Kerberos-integrated authentication, LDAPS or StartTLS. Those may not expose the password in plaintext.

## 3. Extract directory-enumeration evidence

After a successful bind, look for searches that reveal:

- distinguished names / OUs;
- `sAMAccountName`;
- `userPrincipalName`;
- `memberOf`;
- `userAccountControl`;
- `servicePrincipalName`;
- administrative group membership;
- account descriptions or other challenge-specific attributes.

A fast text-oriented pass is often enough:

```bash
rg -ni 'CN=|OU=|DC=|sAMAccountName|userPrincipalName|memberOf|userAccountControl|servicePrincipalName' ldap.txt
```

Do not jump straight from "account appears in LDAP" to "account is compromised". Directory visibility and account control are separate questions.

## 4. Decode `userAccountControl` as a bitmask

`userAccountControl` is a combination of flags. Never compare the entire decimal value to one memorized constant.

For AS-REP-roastability, the important bit is:

```text
DONT_REQ_PREAUTH = 0x400000
```

Test it bitwise:

```python
uac = 0x410200  # example composite value
print(bool(uac & 0x400000))
```

The correct logic is:

```text
(uac & 0x400000) != 0
```

not:

```text
uac == 0x400000
```

A composite value can include `NORMAL_ACCOUNT`, password-policy flags and `DONT_REQ_PREAUTH` simultaneously.

When documenting the finding, preserve both the raw value and the decoded bit:

```text
Observed userAccountControl: <decimal/hex>
Decoded relevant bit: DONT_REQ_PREAUTH set
Forensic implication: account is configured to allow Kerberos AS exchange without normal pre-authentication
```

## 5. Correlate Kerberos AS-REQ / AS-REP activity

Now inspect Kerberos traffic around the directory finding:

```bash
tshark -r capture.pcap -Y kerberos -V > kerberos.txt
rg -ni 'AS-REQ|AS-REP|etype|cname|realm|principal|error-code' kerberos.txt
```

Useful evidence includes:

- account/principal name;
- source and destination hosts;
- AS-REQ followed by AS-REP;
- encryption type;
- absence/presence of errors;
- timing relative to prior LDAP enumeration.

### Forensic AS-REP-roasting inference

A strong reconstruction is:

```text
LDAP evidence: target account has DONT_REQ_PREAUTH
        +
Kerberos evidence: AS request for that account receives AS-REP
        +
Timing/direction: request originates from suspicious host
        =
traffic is consistent with an AS-REP-roasting step
```

`etype 23` is RC4-HMAC and is commonly associated with offline-crackable Kerberos material in CTF/lab scenarios, but the encryption type alone does not prove an attack.

Most importantly:

**an AS-REP response does not prove the password was cracked.**

To claim password recovery, require later evidence such as:

- a recovered credential artifact;
- successful authentication as that principal;
- a tool output captured elsewhere;
- a challenge-provided artifact that explicitly contains the cracked secret.

## 6. Correlate WinRM without inventing hidden commands

WinRM commonly appears on:

```text
5985/tcp -> HTTP WSMan
5986/tcp -> HTTPS WSMan
```

Useful filters:

```bash
tshark -r capture.pcap \
  -Y 'tcp.port==5985 || tcp.port==5986' \
  -T fields \
  -e frame.number -e frame.time_epoch \
  -e ip.src -e ip.dst \
  -e http.request.method -e http.request.uri
```

Requests to a URI such as `/wsman` strongly support WinRM use.

However, NTLM/Kerberos/SPNEGO and message-level protection can make the PowerShell command body unavailable in plaintext.

Correct evidence statement:

```text
Observed: remote-management session to WinRM/WSMan after credential/Kerberos activity.
Not observed: exact PowerShell command content inside the protected session.
```

Do not fill that gap with a guessed command. Correlate **effects after the session** instead:

- new outbound SMB connection;
- file transfer;
- HTTP payload request;
- DNS lookup;
- process/tool artifact elsewhere in the evidence;
- registry/event-log evidence if other artifacts are provided.

## 7. Inspect SMB directionality and file operations

SMB evidence becomes much more useful when you track **who connected to whom**.

Inspect verbose SMB/SMB2 output:

```bash
tshark -r capture.pcap -Y smb2 -V > smb2.txt
rg -ni 'IPC\$|share|filename|Create Request|Read Request|mimikatz|\\\\' smb2.txt
```

Questions to answer:

- Which host initiated TCP/445?
- Which server hosted the share?
- Which share was accessed?
- Which filename was opened/read/written?
- Did the victim pull a file from the suspicious host, or did the suspicious host push to the victim?

A reverse-direction pattern can be decisive:

```text
victim/DC -> suspicious host:445
          -> attacker-controlled share
          -> read tool.exe
```

This supports **tool transfer/staging**.

It does **not** by itself prove the transferred executable ran. Execution requires additional corroboration.

## 8. Recover HTTP and PowerShell staging artifacts

List HTTP requests with enough fields to preserve direction and client identity:

```bash
tshark -r capture.pcap -Y http.request \
  -T fields \
  -e frame.number -e frame.time_epoch \
  -e ip.src -e ip.dst \
  -e http.request.method \
  -e http.host \
  -e http.request.uri \
  -e http.user_agent
```

High-value signals include:

- `.ps1`, `.bat`, `.cmd`, `.exe`, `.dll` requests;
- PowerShell-related User-Agent strings;
- direct IP-hosted staging servers;
- unusual external hosts appearing only after remote-management activity;
- Base64/encoded command material.

Export HTTP objects when the payload body is present in the capture:

```bash
mkdir -p http-objects
tshark -r capture.pcap --export-objects http,http-objects
file http-objects/* 2>/dev/null
sha256sum http-objects/* 2>/dev/null
```

Then inspect scripts statically:

```bash
rg -ni 'base64|FromBase64String|EncodedCommand|Invoke-WebRequest|iwr|curl|wget|Start-Process|cmd.exe|powershell' http-objects/
```

## 9. Decode nested payloads outside-in

When a recovered script contains another encoded payload or URL, preserve the chain:

```text
PCAP HTTP response
  -> stage-1 script
  -> Base64/encoded command
  -> decoded downloader/launcher
  -> stage-2 URL or filename
  -> secondary script/binary
```

For Base64 in PowerShell, first determine whether the data represents raw bytes, UTF-8 text or UTF-16LE (`-EncodedCommand` commonly uses UTF-16LE).

Example decoding pattern:

```python
import base64

data = base64.b64decode(blob)
for enc in ('utf-8', 'utf-16le'):
    try:
        print(enc, data.decode(enc))
    except UnicodeDecodeError:
        pass
```

Validate the decoded output by syntax, recognizable commands, URLs, magic bytes or downstream behavior.

## 10. Distinguish captured evidence from later external retrieval

Sometimes stage 1 only contains a URL to a public repository or web server, while the stage-2 body is **not** present in the PCAP.

If you later retrieve that resource from the live Internet, label it correctly:

```text
PCAP-observed:
- exact URL requested/referenced by stage 1

Externally retrieved later:
- current contents of that URL at analysis time
- retrieval timestamp
- hash of downloaded object
```

Do not silently treat a later live download as byte-for-byte proof of what the attacker received during the capture. Public resources can change.

When the stage-2 object is actually present in the PCAP, the captured bytes are authoritative.

## 11. Handle simple final encodings last

After the intrusion chain is reconstructed, the final challenge secret may still use a lightweight transform such as:

- Base64;
- hex;
- XOR;
- reversed text;
- ROT/caesar;
- compressed or archived payload.

Do not let a trivial final transform distract from the forensic chain that proves where the data came from.

For reversal:

```python
print(text[::-1])
```

Verify the result against expected format or challenge semantics.

## 12. Build a defensible timeline

Use a compact evidence table:

| Time/frame | Source -> destination | Protocol | Observed artifact | Inference | Confidence |
|---|---|---|---|---|---|
| ... | ... | LDAP | successful Simple Bind | credential authenticated | high |
| ... | ... | LDAP | UAC includes `DONT_REQ_PREAUTH` | account roastable | high |
| ... | ... | Kerberos | AS-REQ -> AS-REP | consistent with AS-REP roasting | high |
| ... | ... | WinRM | `/wsman` session | remote management used | high |
| ... | ... | SMB | victim reads tool from remote share | tool transferred | high |
| ... | ... | HTTP | PowerShell downloads stage | payload staging | high |
| ... | ... | external | later retrieval of referenced URL | corroboration only | medium |

This prevents a common forensic failure: narrating a plausible attack chain that contains steps the evidence never actually proved.

## 13. Evidence confidence ladder

Use these labels internally or in the final writeup:

### Observed
Directly visible in the capture:

- packet direction;
- bind identity/password when plaintext;
- LDAP success result;
- returned account attributes;
- Kerberos message type/principal/etype;
- WinRM endpoint/flow;
- SMB share and filename operations;
- HTTP request/response body;
- captured script bytes.

### Strongly inferred
Supported by multiple observed artifacts:

- probable domain-controller role;
- AS-REP-roasting step after `DONT_REQ_PREAUTH` discovery;
- remote-management foothold preceding post-exploitation activity;
- attacker-hosted SMB staging share.

### Unproven until corroborated
Do not claim without more evidence:

- exact password cracking method;
- exact WinRM command when message content is protected;
- execution of every transferred binary;
- persistence merely because a script contains a persistence command;
- current live contents of a URL being identical to historical captured contents.

## 14. Useful one-pass extraction bundle

For a first reproducible bundle:

```bash
mkdir -p triage

capinfos capture.pcap > triage/capinfos.txt

tshark -r capture.pcap -q -z io,phs > triage/protocols.txt

tshark -r capture.pcap -q -z endpoints,ip -z conv,tcp > triage/endpoints.txt

tshark -r capture.pcap -Y ldap -V > triage/ldap.txt

tshark -r capture.pcap -Y kerberos -V > triage/kerberos.txt

tshark -r capture.pcap -Y smb2 -V > triage/smb2.txt

tshark -r capture.pcap -Y http.request \
  -T fields \
  -e frame.number -e frame.time_epoch \
  -e ip.src -e ip.dst \
  -e http.request.method -e http.host \
  -e http.request.uri -e http.user_agent \
  > triage/http-requests.tsv
```

Then search the small outputs instead of repeatedly rescanning the full capture:

```bash
rg -ni 'bind|resultCode|sAMAccountName|userPrincipalName|memberOf|userAccountControl|DONT_REQ|AS-REQ|AS-REP|etype|wsman|IPC\$|share|mimikatz|powershell|\.ps1|\.bat|http' triage/
```

## 15. Field-name/version discipline

Wireshark/tshark field names can change across versions and dissectors.

If a command reports an invalid field, search locally instead of guessing repeatedly:

```bash
tshark -G fields | rg -i 'kerberos|ldap|smb2|http.user|wsman'
```

Use display filters and `-V` output as the stable fallback.

## 16. Common failure modes

- Treating every Windows authentication packet as malicious without establishing a baseline.
- Calling a host the attacker based only on IP address or connection count.
- Finding a plaintext LDAP password but not checking whether the bind succeeded.
- Comparing `userAccountControl` by equality instead of bit-testing flags.
- Calling any AS-REP packet "AS-REP roasting" without tying it to the target account and pre-auth configuration.
- Claiming the AS-REP password was cracked merely because an AS-REP exists.
- Assuming encrypted WinRM means the investigation is blocked; use surrounding effects and later protocol activity.
- Inventing exact PowerShell commands that are not visible in the capture.
- Reading SMB filenames without checking transfer direction.
- Equating file transfer with file execution.
- Downloading a current public payload and presenting it as if those exact bytes came from the historical PCAP.
- Following stage URLs without preserving hashes/provenance.
- Solving the final encoding but failing to reconstruct the evidence chain that produced it.

## 17. Routing boundary: forensics vs offensive AD

Keep this case in `ctf-forensics` when the hard task is:

- reading packet evidence;
- reconstructing host roles;
- correlating LDAP/Kerberos/WinRM/SMB/HTTP;
- proving an attack timeline;
- recovering payloads from the capture.

Use `ctf-misc/references/active-directory.md` when the task changes to **active authorized AD path exploitation**, for example BloodHound pathing, live Kerberoasting, ACL abuse or AD CS exploitation.

Do not duplicate offensive AD methodology here.

## 18. Completion checklist

Before declaring an AD-PCAP reconstruction solved:

- [ ] capture scope and main hosts recorded;
- [ ] probable DC role supported by service evidence;
- [ ] suspicious host role supported by activity, not assumption;
- [ ] LDAP bind success/failure distinguished;
- [ ] important account attributes extracted;
- [ ] `userAccountControl` decoded bitwise;
- [ ] Kerberos principal/message/etype correlated to LDAP evidence;
- [ ] WinRM use separated from unobservable command content;
- [ ] SMB transfer direction and filenames established;
- [ ] HTTP/PowerShell objects exported when present;
- [ ] nested encoding/staging chain preserved;
- [ ] later live downloads clearly marked as external corroboration;
- [ ] timeline distinguishes observed, inferred and unproven claims;
- [ ] final recovered value is traced back to its source artifact.

## Provenance

Generalized from the user-supplied P4KT4M Bahtera Siber writeup for **Lagenda Sultan Kedah Tua** (digital forensics, Active Directory intrusion reconstruction from PCAP), studied 2026-09-04. The reusable methodology was retained; challenge-specific usernames, passwords, IP addresses and flag values were intentionally excluded.
