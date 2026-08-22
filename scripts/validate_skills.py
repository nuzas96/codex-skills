#!/usr/bin/env python3
"""Validate the codex-skills repository structure.

No third-party dependencies are required. Run from any directory:

    python3 scripts/validate_skills.py

Exit codes:
    0: no errors (warnings may remain)
    1: structural errors found
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CORE_V2_SKILLS = {
    "ctf-solve",
    "ctf-web",
    "ctf-pwn",
    "ctf-reverse",
    "ctf-crypto",
    "ctf-forensics",
    "ctf-osint",
    "ctf-malware",
    "ctf-misc",
    "ctf-ai-ml",
    "ctf-writeup",
    "ctf-skill-upgrade",
    "agent-maintenance",
}

# These V1 top-level entrypoints should disappear only after their unique content,
# scripts, references, assets and attribution have a canonical V2 destination.
LEGACY_TOP_LEVEL_SKILLS = {
    "analyzing-browser-forensics-with-hindsight",
    "analyzing-docker-container-forensics",
    "analyzing-malicious-pdf-with-peepdf",
    "ctf-desktop-workspace",
    "ctf-modern-chains",
    "ctf-stuck-recovery",
    "ctf-writeup-repository-study",
    "deobfuscating-javascript-malware",
    "deobfuscating-powershell-obfuscated-malware",
    "exploiting-active-directory-certificate-services-esc1",
    "exploiting-active-directory-with-bloodhound",
    "exploiting-http-request-smuggling",
    "exploiting-insecure-deserialization",
    "exploiting-jwt-algorithm-confusion-attack",
    "exploiting-nosql-injection-vulnerabilities",
    "exploiting-oauth-misconfiguration",
    "exploiting-prototype-pollution-in-javascript",
    "exploiting-race-condition-vulnerabilities",
    "exploiting-template-injection-vulnerabilities",
    "exploiting-websocket-vulnerabilities",
    "hermes-context-compression",
    "performing-content-security-policy-bypass",
    "performing-directory-traversal-testing",
    "performing-file-carving-with-foremost",
    "performing-firmware-extraction-with-binwalk",
    "performing-graphql-introspection-attack",
    "performing-jwt-none-algorithm-attack",
    "performing-kerberoasting-attack",
    "performing-memory-forensics-with-volatility3",
    "performing-mobile-app-certificate-pinning-bypass",
    "performing-network-forensics-with-wireshark",
    "performing-sqlite-database-forensics",
    "performing-steganography-detection",
    "performing-web-application-firewall-bypass",
    "performing-web-cache-poisoning-attack",
    "performing-windows-artifact-analysis-with-eric-zimmerman-tools",
    "progress-discipline",
    "reverse-engineering-android-malware-with-jadx",
    "reverse-engineering-dotnet-malware-with-dnspy",
    "reverse-engineering-ios-app-with-frida",
    "reverse-engineering-malware-with-ghidra",
    "reverse-engineering-ransomware-encryption-routine",
    "reverse-engineering-rust-malware",
    "solve-challenge",
    "testing-android-intents-for-vulnerabilities",
    "testing-for-business-logic-vulnerabilities",
    "testing-for-xxe-injection-vulnerabilities",
    "token-efficient-cli-workflows",
    "web-ctf",
}

MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
NAME_RE = re.compile(r"^name:\s*['\"]?([^'\"\s]+)['\"]?\s*$", re.MULTILINE)
DESCRIPTION_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


@dataclass
class Finding:
    level: str
    path: Path
    message: str


def frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    return text[4:end]


def iter_skill_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.glob("*/SKILL.md")):
        if ".git" not in path.parts:
            yield path


def normalize_link_target(raw: str) -> str:
    target = raw.strip().strip("<>")
    # Markdown allows an optional quoted title after the URL/path.
    if " \"" in target:
        target = target.split(" \"", 1)[0]
    elif " '" in target:
        target = target.split(" '", 1)[0]
    return target


def validate_markdown_links(path: Path, text: str, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for raw in MD_LINK_RE.findall(text):
        target = normalize_link_target(raw)
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        if target_path.startswith("/"):
            # Environment-specific absolute paths are documentation, not repo links.
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            # References intentionally outside the repository are not validated here.
            continue
        if not resolved.exists():
            findings.append(Finding("ERROR", path, f"broken relative link: {target}"))
    return findings


def validate_skill(path: Path, root: Path, max_lines: int, max_bytes: int) -> tuple[list[Finding], str | None]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = frontmatter(text)

    if fm is None:
        findings.append(Finding("ERROR", path, "missing or unterminated YAML frontmatter"))
        return findings, None

    name_match = NAME_RE.search(fm)
    if not name_match:
        findings.append(Finding("ERROR", path, "frontmatter is missing a simple 'name:' value"))
        skill_name = None
    else:
        skill_name = name_match.group(1)
        directory_name = path.parent.name
        if skill_name != directory_name:
            findings.append(
                Finding("ERROR", path, f"frontmatter name '{skill_name}' != directory '{directory_name}'")
            )

    if not DESCRIPTION_RE.search(fm):
        findings.append(Finding("ERROR", path, "frontmatter is missing description"))

    line_count = text.count("\n") + 1
    byte_count = len(text.encode("utf-8"))
    if line_count > max_lines:
        findings.append(Finding("WARN", path, f"router has {line_count} lines (target <= {max_lines})"))
    if byte_count > max_bytes:
        findings.append(Finding("WARN", path, f"router is {byte_count} bytes (target <= {max_bytes})"))

    findings.extend(validate_markdown_links(path, text, root))
    return findings, skill_name


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate codex-skills V2 structure")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--max-lines", type=int, default=500)
    parser.add_argument("--max-bytes", type=int, default=24000)
    parser.add_argument(
        "--strict-migration",
        action="store_true",
        help="treat remaining V1 top-level SKILL.md entrypoints as errors instead of warnings",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    findings: list[Finding] = []
    names: dict[str, list[Path]] = {}
    skills = list(iter_skill_files(root))

    if not skills:
        print("ERROR: no top-level */SKILL.md files found", file=sys.stderr)
        return 1

    for skill_file in skills:
        skill_findings, name = validate_skill(skill_file, root, args.max_lines, args.max_bytes)
        findings.extend(skill_findings)
        if name:
            names.setdefault(name, []).append(skill_file)

    for name, paths in sorted(names.items()):
        if len(paths) > 1:
            findings.append(Finding("ERROR", paths[0], f"duplicate skill name '{name}' in {len(paths)} files"))

    top_level_dirs = {path.parent.name for path in skills}
    for required in sorted(CORE_V2_SKILLS - top_level_dirs):
        findings.append(Finding("ERROR", root, f"missing V2 core skill entrypoint: {required}/SKILL.md"))

    migration_level = "ERROR" if args.strict_migration else "WARN"
    for legacy in sorted(LEGACY_TOP_LEVEL_SKILLS & top_level_dirs):
        findings.append(
            Finding(
                migration_level,
                root / legacy / "SKILL.md",
                "legacy V1 top-level entrypoint still active; audit/migrate before deactivation",
            )
        )

    unknown = top_level_dirs - CORE_V2_SKILLS - LEGACY_TOP_LEVEL_SKILLS
    for directory in sorted(unknown):
        findings.append(
            Finding(
                "WARN",
                root / directory / "SKILL.md",
                "unclassified top-level skill; decide whether it is a true V2 domain/task",
            )
        )

    errors = 0
    warnings = 0
    for finding in findings:
        rel = finding.path
        try:
            rel = finding.path.resolve().relative_to(root)
        except (ValueError, OSError):
            pass
        print(f"{finding.level}: {rel}: {finding.message}")
        errors += finding.level == "ERROR"
        warnings += finding.level == "WARN"

    print()
    print(f"Skills: {len(skills)}")
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    print(f"Active legacy entrypoints: {len(LEGACY_TOP_LEVEL_SKILLS & top_level_dirs)}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
