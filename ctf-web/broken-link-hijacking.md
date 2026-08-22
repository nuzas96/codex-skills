# CTF Web - Broken Link Hijacking & Supply Chain Takeover

Goes beyond [Subdomain Takeover](#subdomain-takeover) in `field-notes.md` — covers dead external resources (expired domains, deprecated CDN packages, unclaimed social handles, S3 buckets) that a target app still references. Claiming any of these gives you full XSS, content injection, or phishing capability on the target's domain.

**Use this file when:**
- Recon finds a target app loading JS/CSS/images from a third-party domain/CDN
- A `whois` lookup shows an external dependency is unregistered or expired
- A subdomain points to a service where no resource exists (GH Pages 404, S3 NoSuchBucket, Heroku no app)
- An npm/unpkg package referenced by the app has been deprecated or removed

## Attack Surfaces

| Surface | What you claim | Impact on target |
| ------- | -------------- | ---------------- |
| Expired JS domain | Register domain, serve malicious JS | Full XSS on every page that loads the script |
| Deprecated npm package | `npm publish` new version with backdoor | XSS on every consumer via CDN |
| S3 bucket in CNAME | `aws s3 mb` to recreate | Content injection, data theft from uploads |
| GitHub Pages dangling | Create matching `<org>.github.io` | Phishing on `*.target.com` subdomain |
| Unclaimed social handle | Register the handle | Brand impersonation, OAuth flow abuse |
| Dangling Azure blob | Recreate container | Static asset defacement |

## Workflow

### 1. Discover External References

```bash
# All external URLs in page source
curl -s http://target.com | grep -oP 'https?://[^"'\''> ]+' | sort -u > all_links.txt

# External JS / CSS / image references
curl -s http://target.com | grep -oP 'src="https?://[^"]+' | sort -u
curl -s http://target.com | grep -oP 'href="https?://[^"]+' | sort -u

# Wayback Machine — find historical references that may have been removed
curl -s "https://web.archive.org/web/timemap/link/http://target.com" | \
  grep -oP 'https?://[^>]+' | sort -u > historical_links.txt

# Burp: Site Map > Filter by MIME or "External" host
# Or use: npx broken-link-checker http://target.com --recursive
```

### 2. Identify Dead / Claimable Resources

```bash
# WHOIS — unregistered or expired?
for domain in $(cat external_domains.txt); do
  whois "$domain" 2>/dev/null | grep -qi "no match\|not found\|available" && \
    echo "[CLAIMABLE DOMAIN] $domain"
done

# HTTP status — 404 / 000 = dead
while read url; do
  status=$(curl -o /dev/null -s -w "%{http_code}" "$url" --max-time 5)
  [ "$status" = "000" ] || [ "$status" = "404" ] && echo "[DEAD] $url ($status)"
done < all_links.txt

# Dangling CNAME — DNS points to service but service has no resource
for sub in $(cat subdomains.txt); do
  cname=$(dig +short CNAME "$sub")
  if [ -n "$cname" ]; then
    resolved=$(dig +short "$cname")
    [ -z "$resolved" ] && echo "[DANGLING] $sub -> $cname (unresolved)"
  fi
done
```

### 3. Service-Specific Takeover Fingerprints

Match the service error page to the dangling target. If you can recreate the resource, you own that subdomain.

```bash
# GitHub Pages — "There isn't a GitHub Pages site here"
curl -s https://subdomain.target.com | grep -q "There isn't a GitHub Pages site here" && \
  echo "[GITHUB PAGES TAKEOVER]"

# AWS S3 — "NoSuchBucket"
curl -s http://subdomain.target.com | grep -q "NoSuchBucket" && echo "[S3 TAKEOVER]"

# Azure Blob — "The specified container does not exist"
curl -s http://subdomain.target.com | grep -q "The specified container does not exist" && \
  echo "[AZURE BLOB TAKEOVER]"

# Heroku — "No such app"
curl -s http://subdomain.target.com | grep -q "No such app" && echo "[HEROKU TAKEOVER]"

# Shopify — "Sorry, this shop is currently unavailable"
curl -s http://subdomain.target.com | grep -q "currently unavailable" && \
  echo "[SHOPIFY TAKEOVER]"

# Comprehensive fingerprint list:
# https://github.com/EdOverflow/can-i-take-over-xyz

# Automated scanner
subjack -w subdomains.txt -c fingerprints.json -t 100 -o takeover_candidates.txt
subfinder -d target.com -silent | nuclei -t http/takeovers/ -o takeovers.txt
```

### 4. NPM / CDN Package Hijack (Most Underrated)

If the target loads a specific version of an npm package via `unpkg` or `jsdelivr`, and the package is deprecated, **you can claim it**.

```bash
# Find CDN references
curl -s http://target.com | grep -oP 'unpkg\.com/[^@/]+(@[^/]+)?' | sort -u
curl -s http://target.com | grep -oP 'cdn\.jsdelivr\.net/npm/[^@/]+' | sort -u

# Check if package is deprecated on npm
npm view <package> deprecated
npm view <package> time.unpublished  # Was it unpublished?

# If deprecated: npm publish a new version with backdoor
# npm login (as the original author if you can prove identity transfer, or as new maintainer if transferred)
# Update package source with malicious code, then: npm publish
# Next time the target loads https://unpkg.com/<package>@latest, your code runs.
```

**Caveat:** npm has deprecation policies. Actual unpublish is hard after 72h. The window for hijack is narrow but real for packages that were transferred and then abandoned.

### 5. PoC and Report

For CTF, demonstrate control by serving benign proof-of-concept content:

```bash
# For S3: create the bucket
aws s3 mb s3://target-assets --region us-east-1
echo '<html><h1>Broken Link Hijack PoC — claim verified</h1></html>' > index.html
aws s3 cp index.html s3://target-assets/index.html --acl public-read

# For GitHub Pages: create <org>.github.io with CNAME file pointing to target subdomain
# Then HTTPS provisioning at GitHub Settings > Pages > Custom domain
```

**Report structure:**
```
## Broken Link Hijacking Report
- Target: http://target.com
- External dependencies: 145
- Dead links: 12
- Hijackable resources: 3

| # | Resource | Type | Status | Impact |
|---|----------|------|--------|--------|
| 1 | analytics.expired.com | JS | Domain available | Full XSS |
| 2 | assets.target.com -> S3 | Static | Bucket deleted | Content injection |
| 3 | blog.target.com -> GH Pages | Subdomain | No repo | Subdomain takeover |

### Remediation
- Remove references to dead external resources
- Delete dangling CNAME records
- Add Subresource Integrity (SRI) for external scripts: <script src="..." integrity="sha384-..." crossorigin="anonymous">
- CSP that restricts script-src to known-good origins
- Periodically audit external dependencies (Dependabot, npm audit)
```

## Key Differences from Subdomain Takeover

| Subdomain Takeover (existing) | Broken Link Hijacking (this file) |
| ----------------------------- | --------------------------------- |
| Subdomain CNAME → service | Any external resource (CDN, JS, image) |
| Claiming a service account | Registering a domain or claiming a package |
| Cookie / OAuth / phishing | XSS / content injection / supply chain |
| Find dangling DNS | Find dead/expired/unclaimed anywhere |
| Tools: subfinder, subjack | Tools: broken-link-checker, can-i-take-over-xyz |

## Common CTF Patterns

1. **Recon challenge** — "Find all external dependencies of the app" → automate link extraction + WHOIS sweep
2. **Bug bounty style** — App loads analytics.js from `cdn-deprecated.com` that expired → claim and serve cookie-stealing XSS
3. **Supply chain OSINT** — Investigate a "mysterious dependency" in the JS bundle and discover it's a hijackable npm package
4. **Cross-tier chain** — Subdomain takeover → cookie theft → admin bypass → RCE

## Tools Reference

- `broken-link-checker` (npx) — automated external link validation
- `subjack` — subdomain takeover detection
- `nuclei -t http/takeovers/` — template-based takeover scanning
- `can-i-take-over-xyz` (GitHub) — fingerprint DB for takeover-able services
- `BadDNS` — DNS audit + takeover detection
- `Wayback Machine` / CDX API — historical URL discovery
