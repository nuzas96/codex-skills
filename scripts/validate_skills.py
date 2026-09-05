#!/usr/bin/env python3
"""Validate the codex-skills V2 repository structure.

No third-party dependencies are required. Run from any directory:

    python3 scripts/validate_skills.py
    python3 scripts/validate_skills.py --strict-migration

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
    "ctf-boot2root",
    "ctf-writeup",
    "ctf-skill-upgrade",
    "agent-maintenance",
}

ALLOWED_SUPPORT_DIRS = {".git", ".github", "scripts"}

# Frozen V1 top-level directories. Their useful knowledge must have a canonical
# V2 destination before the directory is removed from the V2 branch.
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

def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if ".git" not in path.parts:
            yield path


def normalize_link_target(raw: str) -> str:
    target = raw.strip().strip("<>")
    if " \"" in target:
        target = target.split(" \"", 1)[0]
    elif " '" in target:
        target = target.split(" '", 1)[0]
    return target


def markdown_link_scan_text(text: str) -> str:
    """Remove code regions before interpreting Markdown link syntax.

    Many CTF references contain expressions such as function calls after
    bracket indexing that look like Markdown links to a regex. Fenced code,
    indented code blocks, and inline code spans are therefore excluded from
    link validation.
    """
    output: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        fence = re.match(r"(`{3,}|~{3,})", stripped)

        if fence:
            token = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char = token[0]
                fence_len = len(token)
            elif token[0] == fence_char and len(token) >= fence_len:
                in_fence = False
            output.append("\n" if line.endswith("\n") else "")
            continue

        if in_fence or line.startswith(("    ", "\t")):
            output.append("\n" if line.endswith("\n") else "")
            continue

        output.append(re.sub(r"`[^`\n]*`", "", line))

    return "".join(output)


def validate_markdown_links(path: Path, text: str, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    scan_text = markdown_link_scan_text(text)
    for raw in MD_LINK_RE.findall(scan_text):
        target = normalize_link_target(raw)
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path or target_path.startswith("/"):
            continue
        resolved = (path.parent / target_path).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
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

    return findings, skill_name


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate codex-skills V2 structure")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--max-lines", type=int, default=500)
    parser.add_argument("--max-bytes", type=int, default=24000)
    parser.add_argument(
        "--strict-migration",
        action="store_true",
        help="fail on legacy V1 directories/entrypoints and non-V2 root directories",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    findings: list[Finding] = []
    names: dict[str, list[Path]] = {}
    skills = list(iter_skill_files(root))
    markdown_files = list(iter_markdown_files(root))

    if not skills:
        print("ERROR: no top-level */SKILL.md files found", file=sys.stderr)
        return 1

    for skill_file in skills:
        skill_findings, name = validate_skill(skill_file, root, args.max_lines, args.max_bytes)
        findings.extend(skill_findings)
        if name:
            names.setdefault(name, []).append(skill_file)

    # Validate local relative links in every Markdown document, not only
    # top-level SKILL.md routers. This catches stale links in focused
    # references, broad handbooks, README/CATALOG, and migration/provenance
    # documentation before they reach main.
    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8", errors="replace")
        findings.extend(validate_markdown_links(markdown_file, text, root))

    for name, paths in sorted(names.items()):
        if len(paths) > 1:
            findings.append(Finding("ERROR", paths[0], f"duplicate skill name '{name}' in {len(paths)} files"))

    top_level_skill_dirs = {path.parent.name for path in skills}
    for required in sorted(CORE_V2_SKILLS - top_level_skill_dirs):
        findings.append(Finding("ERROR", root, f"missing V2 core skill entrypoint: {required}/SKILL.md"))

    migration_level = "ERROR" if args.strict_migration else "WARN"

    for legacy in sorted(LEGACY_TOP_LEVEL_SKILLS & top_level_skill_dirs):
        findings.append(
            Finding(
                migration_level,
                root / legacy / "SKILL.md",
                "legacy V1 top-level entrypoint still active",
            )
        )

    physical_dirs = {
        path.name
        for path in root.iterdir()
        if path.is_dir() and path.name not in {"__pycache__"}
    }
    legacy_residue = LEGACY_TOP_LEVEL_SKILLS & physical_dirs
    for legacy in sorted(legacy_residue):
        findings.append(
            Finding(
                migration_level,
                root / legacy,
                "legacy V1 top-level directory still present after migration",
            )
        )

    unknown_skills = top_level_skill_dirs - CORE_V2_SKILLS - LEGACY_TOP_LEVEL_SKILLS
    for directory in sorted(unknown_skills):
        findings.append(
            Finding(
                "ERROR" if args.strict_migration else "WARN",
                root / directory / "SKILL.md",
                "unclassified top-level skill; V2 requires an explicit domain/task owner",
            )
        )

    allowed_root_dirs = CORE_V2_SKILLS | ALLOWED_SUPPORT_DIRS
    unknown_physical_dirs = physical_dirs - allowed_root_dirs - LEGACY_TOP_LEVEL_SKILLS
    for directory in sorted(unknown_physical_dirs):
        findings.append(
            Finding(
                "ERROR" if args.strict_migration else "WARN",
                root / directory,
                "unclassified top-level directory outside the V2 architecture",
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
    print(f"Markdown files checked: {len(markdown_files)}")
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    print(f"Active legacy entrypoints: {len(LEGACY_TOP_LEVEL_SKILLS & top_level_skill_dirs)}")
    print(f"Legacy directories present: {len(legacy_residue)}")
    print(f"Unclassified root directories: {len(unknown_physical_dirs)}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
