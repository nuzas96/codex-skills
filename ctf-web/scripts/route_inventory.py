#!/usr/bin/env python3
"""List literal Flask/FastAPI and Express/Fastify route declarations in local source."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


EXTENSIONS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "vendor", "dist", "build", "__pycache__"}
PYTHON_ROUTE = re.compile(
    r"^\s*@(?P<owner>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\."
    r"(?P<verb>get|post|put|patch|delete|options|head|route|api_route)\s*\(\s*"
    r"(?P<quote>['\"])(?P<path>[^'\"\n]+)(?P=quote)(?=\s*[,)])", re.IGNORECASE
)
PYTHON_DJANGO = re.compile(
    r"^\s*(?:path|re_path)\s*\(\s*(?P<quote>['\"])(?P<path>[^'\"\n]+)(?P=quote)(?=\s*,)", re.IGNORECASE
)
NODE_ROUTE = re.compile(
    r"\b(?P<owner>[A-Za-z_$][\w$]*)\s*\.\s*(?P<verb>get|post|put|patch|delete|options|head)"
    r"\s*\(\s*(?P<quote>['\"`])(?P<path>[^'\"`\n]+)(?P=quote)(?=\s*[,)]|$)", re.IGNORECASE
)
NODE_CHAIN_ROUTE = re.compile(
    r"\b(?P<owner>[A-Za-z_$][\w$]*)\s*\.\s*route\s*\(\s*"
    r"(?P<quote>['\"`])(?P<path>[^'\"`\n]+)(?P=quote)(?=\s*\))", re.IGNORECASE
)


def _strip_js_line_comment(line: str) -> str:
    quote = None
    escaped = False
    for index, char in enumerate(line):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "/" and index + 1 < len(line) and line[index + 1] == "/":
            return line[:index]
    return line


def _strip_js_comments(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    in_block = False
    for line in lines:
        current = line
        while current:
            if in_block:
                end = current.find("*/")
                if end < 0:
                    current = ""
                    break
                current = current[end + 2 :]
                in_block = False
                continue
            if current.lstrip().startswith("//"):
                current = ""
                break
            start = current.find("/*")
            if start < 0:
                current = _strip_js_line_comment(current)
                break
            current = current[:start]
            in_block = True
        cleaned.append(current)
    return cleaned


def inventory(root: Path, max_file_bytes: int = 1_000_000) -> tuple[list[dict], int]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"source root is not a directory: {root}")
    rows: list[dict] = []
    skipped_large = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        if path.stat().st_size > max_file_bytes:
            skipped_large += 1
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        suffix = path.suffix.lower()
        if suffix != ".py":
            lines = _strip_js_comments(lines)
        for number, line in enumerate(lines, 1):
            if suffix == ".py" and line.lstrip().startswith("#"):
                continue
            matches = []
            if path.suffix.lower() == ".py":
                match = PYTHON_ROUTE.search(line)
                if match:
                    verb = match.group("verb").upper()
                    route_path = match.group("path")
                    method_source = "static-declaration"
                    runtime_note = None
                    if verb in {"ROUTE", "API_ROUTE"}:
                        methods_arg = re.search(r"\bmethods\s*=\s*(?:\[([^]]*)\]|\(([^)]*)\))", line, re.IGNORECASE)
                        has_methods_arg = re.search(r"\bmethods\s*=", line, re.IGNORECASE)
                        explicit_methods = None
                        if methods_arg:
                            explicit_body = methods_arg.group(1) if methods_arg.group(1) is not None else methods_arg.group(2)
                            explicit_methods = re.findall(r"['\"]([A-Za-z]+)['\"]", explicit_body)
                        if has_methods_arg and explicit_methods is not None:
                            verb = ",".join(method.upper() for method in explicit_methods) or "ROUTE"
                            method_source = "explicit" if explicit_methods else "explicit-unknown"
                        elif has_methods_arg:
                            # Do not claim Flask's default for a dynamic or
                            # unsupported explicit methods expression.
                            verb = "ROUTE"
                            method_source = "explicit-unknown"
                            if match.group("verb").lower() == "route":
                                runtime_note = "Explicit methods expression is not statically understood; inspect the runtime URL map."
                        elif match.group("verb").lower() == "route":
                            # Flask's route() defaults to GET. HEAD/OPTIONS can
                            # be synthesized at runtime, depending on rule and
                            # app configuration, so static source scanning must
                            # not claim an observed runtime method map.
                            verb = "GET"
                            method_source = "flask-default"
                            opts = re.search(r"provide_automatic_options\s*=\s*(True|False)", line, re.IGNORECASE)
                            if opts and opts.group(1).lower() == "false":
                                runtime_note = "Static declaration only: rule explicitly disables automatic OPTIONS; Flask may still add HEAD for GET. Runtime app configuration is unverified."
                            elif opts and opts.group(1).lower() == "true":
                                runtime_note = "Static declaration only: rule enables automatic OPTIONS; Flask may add HEAD for GET. Runtime app configuration is unverified."
                            else:
                                runtime_note = "Flask may add HEAD for GET and automatic OPTIONS unless disabled; inspect app/rule configuration or runtime URL map."
                        else:
                            verb = "GET"
                            method_source = "framework-default"
                        if match.group("verb").lower() == "route" and method_source == "explicit":
                            opts = re.search(r"provide_automatic_options\s*=\s*(True|False)", line, re.IGNORECASE)
                            opts_value = opts.group(1).lower() if opts else None
                            if "OPTIONS" in explicit_methods:
                                runtime_note = "Static declaration only: OPTIONS is explicit; Flask may add HEAD when GET is allowed. Runtime method map is unverified."
                            elif opts_value == "false":
                                runtime_note = "Static declaration only: rule explicitly disables automatic OPTIONS; Flask may still add HEAD when GET is allowed. Runtime app configuration is unverified."
                            elif opts_value == "true":
                                runtime_note = "Static declaration only: rule enables automatic OPTIONS; Flask may add HEAD when GET is allowed. Runtime app configuration is unverified."
                            else:
                                runtime_note = "Static declaration only: Flask may add HEAD when GET is allowed; automatic OPTIONS depends on app configuration and provide_automatic_options."
                    matches.append(("python-decorator", verb or "ROUTE", route_path))
                else:
                    match = PYTHON_DJANGO.search(line)
                    if match:
                        matches.append(("django-urlconf", "ROUTE", match.group("path")))
            else:
                for match in NODE_ROUTE.finditer(line):
                    matches.append(("node-router", match.group("verb").upper(), match.group("path")))
                if not matches:
                    match = NODE_CHAIN_ROUTE.search(line)
                    if match:
                        matches.append(("node-router-chain", "ROUTE", match.group("path")))
            for framework, method, route_path in matches:
                rows.append({
                    "file": path.relative_to(root).as_posix(),
                    "line": number,
                    "framework_hint": framework,
                    "method": method,
                    "method_source": method_source if suffix == ".py" and framework == "python-decorator" else "static-declaration",
                    "runtime_methods": None,
                    **({"runtime_method_note": runtime_note} if suffix == ".py" and framework == "python-decorator" and runtime_note else {}),
                    "path_literal": route_path,
                })
    return rows, skipped_large


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--max-file-bytes", type=int, default=1_000_000)
    args = parser.parse_args()
    if args.max_file_bytes <= 0:
        parser.error("--max-file-bytes must be positive")
    try:
        rows, skipped = inventory(args.root, args.max_file_bytes)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps({
        "scope": ".",
        "routes": rows,
        "skipped_oversize_files": skipped,
        "coverage_note": "Static literal declarations only; inspect mounts, dynamic routes, handlers, middleware and authorization checks in source.",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
