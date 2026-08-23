# XXE and XML Parser Abuse

Use when the application parses XML directly or indirectly through SOAP, SVG, DOCX/XLSX/PPTX, RSS/Atom, XML configuration, converters, or XML-backed upload pipelines.

## First Identify the Parser Surface

Evidence includes:

- `Content-Type: application/xml`, `text/xml`, `application/soap+xml`;
- SOAP/WSDL endpoints;
- XML errors or entity/DTD terminology;
- uploads of XML-based formats;
- source/dependencies showing XML parser/converter libraries.

Some JSON endpoints accept alternate XML content types. Test this only when content negotiation/framework behavior makes it plausible.

## Decision Tree

```text
XML reaches parser
  -> DTD accepted?
  -> external general entity resolved?
  -> external parameter entity resolved?
  -> reflected or blind?
  -> file:// / HTTP / other scheme supported?
  -> smallest file/SSRF proof
  -> only then build OOB/document-upload chain
```

## Basic File / SSRF Oracle

Use a harmless, small local file or controlled HTTP endpoint first. If entity expansion is reflected, you already have a strong oracle. If not, use an out-of-band DNS/HTTP callback to distinguish "not reflected" from "not resolved".

Do not begin by exfiltrating a multiline secret through a complex external DTD when a one-request proof has not established entity resolution.

## General vs Parameter Entities

Some parsers block general external entities but still resolve external parameter entities during DTD processing. Test them separately when source/version suggests DTD processing remains enabled.

External DTD chains are useful for blind extraction because they can read a local resource and construct an outbound request. Encoding/line-break/scheme restrictions vary by parser.

## XML-Based Uploads

DOCX/XLSX/PPTX are ZIP containers containing XML; SVG is directly XML. Determine **which member the server actually parses**. Editing an arbitrary XML member does nothing if the processing pipeline never opens it.

Workflow:

1. start from a valid document;
2. identify parsed XML member from source/errors/behavior;
3. inject smallest external-entity proof;
4. repackage without breaking container structure;
5. observe reflected/OOB effect.

Converters such as CairoSVG, office libraries, XSLT/Xalan, or custom XML transforms can introduce parser-specific behaviors covered by existing `server-side-advanced*.md` notes.

## XXE -> SSRF

If HTTP entities resolve, treat the primitive like SSRF: enumerate only target-relevant internal services, metadata, or local application endpoints. Route deeper URL/resolver mismatches to server-side SSRF/modern-chain references.

## PHP / Wrapper Notes

On PHP-backed XML paths, stream wrappers can affect readability/encoding, but support depends on the parser/runtime configuration. Use `php://filter` only when PHP wrappers are genuinely involved.

## XInclude / XSLT / Alternative XML Features

A blocked DOCTYPE does not mean every XML expansion mechanism is disabled. Source/library evidence may point to XInclude, XSLT document functions, schema imports, or other resolver hooks. Test the feature the application actually invokes.

## Common Failure Modes

- Declaring "XXE fixed" because one general-entity payload is blocked.
- Treating every ZIP-based office upload as parsed XML.
- Breaking DOCX/XLSX container layout while editing.
- Using a large sensitive file before proving a small file/callback primitive.
- Ignoring parser/version differences and outbound-network restrictions.
- Confusing XML injection with XXE when no external resolution occurs.

## Provenance

Consolidated from the original `testing-for-xxe-injection-vulnerabilities` Apache-2.0 skill plus `ctf-web/server-side-2.md` and advanced XML/parser notes. Original source is preserved on `archive/pre-restructure-20260823`.
