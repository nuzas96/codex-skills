---
name: ctf-osint
description: Solve CTF OSINT challenges using public information: geolocation and image/media clues, social-media identities and timestamps, usernames, DNS/web infrastructure, archives, repositories, public records, map/road systems and related open sources. Use when identifying a real-world person, place, event, organization, account or public digital footprint is the primary path to the flag.
license: MIT
compatibility: Requires web/public-data access and normal metadata/map/search tooling; use APIs or specialized services only when the selected clue requires them.
metadata:
  user-invocable: "false"
---

# CTF OSINT — V2 Router

Use `ctf-solve` for lifecycle/progress. OSINT answers should be evidence chains, not single-search guesses.

## First pass

1. Extract every concrete clue before searching: visible text, language, road markings, architecture, weather, event date, username, ID, domain, metadata, reflections and unique objects.
2. Separate **hard clues** from thematic/story text.
3. Generate a small candidate set and maintain disconfirming evidence as aggressively as confirming evidence.
4. Prefer primary/public records and exact visual matches over SEO pages or reposts.
5. Record query terms, source URLs/identifiers and why each source proves a step.

## Reference router

| Clue / task | Load first | Add only if needed |
|---|---|---|
| place/image/road/building/landscape | `geolocation-and-media.md` | `references/highway-km-marker-geolocation.md` |
| social account/post/user/date/ID | `social-media.md` | web/DNS ref if domain/account correlation needed |
| website/domain/DNS/Wayback/GitHub/public infra | `web-and-dns.md` | social-media ref |
| highway kilometer marker | `references/highway-km-marker-geolocation.md` | `geolocation-and-media.md` |

## Geolocation discipline

Work from high-information features:

- script/language and exact wording;
- road side, lane/curb/guardrail/sign standards;
- utility poles, terrain, vegetation and coast/mountain orientation;
- business/building names;
- transport/route numbers and kilometer markers;
- distinctive religious/civic architecture;
- shadows/weather only as supporting evidence.

For images, crop/refocus distinctive regions for reverse-image matching rather than submitting the entire frame repeatedly. Reflections, signs and background ridgelines can be stronger than the foreground object.

When a route/highway marker is present, map the official road first, then solve distance/direction along that road rather than visually searching an entire country.

## Social-media discipline

Capture exact identifiers and platform semantics:

- username vs display name;
- post/status numeric ID;
- timestamp/timezone;
- reply/repost relationships;
- image variants/CDN paths;
- profile history/aliases;
- linked domains/accounts.

Where platform IDs encode time (for example Snowflake-style IDs), decode them and validate against the visible post date. Use archived/public API data when UI search is incomplete.

## Web / DNS discipline

For a domain or site, correlate:

- DNS records/subdomains;
- certificate transparency when useful;
- Wayback/archive snapshots;
- WHOIS/registration data where public and relevant;
- source/repository references;
- robots/sitemaps/well-known paths;
- username/email/domain reuse.

A current page can be misleading if the challenge points to historical ownership/content; always align source date with challenge date.

## Time reasoning

OSINT challenges often hinge on event timing. Keep separate:

```text
photo/post capture date
publication date
real-world event date
archive snapshot date
```

Do not treat them as interchangeable. When the prompt gives a date, constrain candidate events/venues to that period first.

## Candidate table

For difficult identification challenges, maintain a compact table:

```text
candidate | confirming clues | contradictions | source quality | next test
```

A famous/obvious candidate with one contradiction should not survive merely because it matches the theme.

## Verification before flag

A final identity/location should normally have at least two independent high-quality links, for example:

```text
visual/metadata clue -> exact place
place/date -> exact event
venue record -> home/away participants
award/record -> exact restaurant name
```

Then normalize spelling exactly to the flag format.

## Cross-category pivots

- hidden data must first be extracted from an image/document -> `ctf-forensics`;
- obfuscated code/domain generation must be reversed -> `ctf-reverse`;
- web application exploitation, not public research, becomes primary -> `ctf-web`;
- public clue leads to cryptographic encoding that is the real blocker -> `ctf-crypto`.

## Completion criteria

- final answer is supported by a reproducible evidence chain;
- contradictory candidates were explicitly eliminated;
- dates/names/locations match authoritative or direct sources;
- exact flag normalization is recorded in `PROGRESS.md`.

## V1 migration rule

OSINT remains one top-level domain skill. New techniques belong in `geolocation-and-media.md`, `social-media.md`, `web-and-dns.md`, or a focused internal reference rather than another top-level skill.