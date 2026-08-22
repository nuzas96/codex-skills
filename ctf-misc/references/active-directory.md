# Active Directory CTF Playbook

Use for authorized CTF/lab challenges whose primary environment is an Active Directory domain and the solve depends on relationship/path analysis, Kerberos service accounts, or AD CS certificate-template misconfiguration. Keep AD as a Misc subfamily rather than creating many top-level technique skills.

## First Map the Domain

Record:

- current principal and groups;
- domain/controllers/trusts;
- reachable hosts/services;
- SPNs and service accounts;
- ACL/delegation relationships;
- certificate authorities/templates when AD CS exists.

Prefer a graph/path model over running every AD technique independently.

## BloodHound: Route Finder

BloodHound/SharpHound-style collection is useful to answer: **what is the shortest plausible path from the owned principal to the challenge objective?**

High-value relationship classes include:

- group membership;
- local admin/session edges;
- `GenericAll`, `GenericWrite`, `WriteDACL`, password-reset/control edges;
- delegation;
- DCSync-equivalent rights;
- GPO relationships;
- Kerberoastable/AS-REP-roastable users;
- AD CS-related paths when supported by the data model.

Mark only genuinely controlled principals as owned. Treat graph edges as hypotheses that still require environmental validation.

## Kerberoasting Branch

Recognition: a user/service account has an SPN and the current domain user can request a service ticket.

CTF workflow:

1. enumerate SPN-bearing **user** accounts;
2. prioritize accounts that connect to the graph objective;
3. request the relevant TGS in the authorized lab;
4. export it in an offline-cracking format;
5. crack offline only when password weakness is plausibly intended;
6. feed any recovered credential back into the BloodHound/path model.

Hashcat modes depend on Kerberos encryption type (for example RC4 TGS-REP differs from AES). Determine the ticket type rather than copying a mode blindly.

Do not Kerberoast every account if only one has a useful path to the challenge target.

## AD CS ESC1 Branch

ESC1-like misconfiguration requires a vulnerable certificate template, not merely the presence of AD CS.

Check the core conditions:

- enrollee can supply subject/SAN;
- template permits an authentication-capable EKU (client auth / smart-card / PKINIT / suitable equivalent);
- low-privileged principal has enrollment rights;
- approval/authorized-signature constraints do not prevent issuance;
- CA/template is actually enabled/issuable.

In a controlled CTF lab, tools such as Certipy/Certify can enumerate these properties and request a certificate using the template. The meaningful primitive is **certificate identity differs from requester due to template policy**, after which certificate-based authentication can demonstrate the intended privilege path.

Always derive CA/template/principal names from the target; never reuse example domain constants.

## How the Branches Compose

```text
initial domain account
  -> collect/understand relationships
  -> BloodHound identifies candidate path
       -> SPN service user? -> Kerberoasting branch
       -> vulnerable AD CS template? -> ESC1 branch
       -> ACL/delegation/GPO edge? -> investigate that edge
  -> new controlled principal
  -> re-run shortest-path reasoning
  -> challenge objective
```

This prevents technique-first wandering.

## Evidence to Record

- owned principal(s);
- decisive graph edge/path;
- SPN/template/CA involved;
- ticket/certificate identity and encryption/template properties;
- which new principal/access was actually validated;
- why that access reaches the flag/objective.

## Common Failure Modes

- Running BloodHound collection but never reducing it to a concrete path.
- Kerberoasting every SPN regardless of privilege/path relevance.
- Calling a template ESC1 from one flag without checking enrollment/EKU/approval conditions.
- Treating a theoretical BloodHound edge as validated access.
- Continuing with unrelated AD attacks after a new credential/certificate should change the shortest path.

## Provenance

Consolidated for CTF/lab use from the original Apache-2.0 `exploiting-active-directory-with-bloodhound`, `performing-kerberoasting-attack`, and `exploiting-active-directory-certificate-services-esc1` skills. Complete originals remain frozen on `archive/pre-restructure-20260823`.
