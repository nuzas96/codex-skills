#!/usr/bin/env python3
"""Report ELF format, host compatibility, and available reverse tools without executing the target."""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


QEMU_BY_MACHINE = {
    "Intel 80386": "qemu-i386",
    "Advanced Micro Devices X86-64": "qemu-x86_64",
    "AArch64": "qemu-aarch64",
    "ARM": "qemu-arm",
    "MIPS": "qemu-mips",
    "MIPS R3000": "qemu-mips",
    "PowerPC": "qemu-ppc",
    "PowerPC64": "qemu-ppc64",
}
QEMU_NAMES = (
    "qemu-i386", "qemu-x86_64", "qemu-aarch64", "qemu-arm", "qemu-armeb",
    "qemu-mips", "qemu-mipsel", "qemu-mips64", "qemu-mips64el",
    "qemu-ppc", "qemu-ppc64", "qemu-ppc64le", "qemu-riscv32", "qemu-riscv64",
)


def recommend_qemu(machine: str | None, elf_class: str | None, data_encoding: str | None) -> str | None:
    little_endian = bool(data_encoding and ("little endian" in data_encoding.lower() or "lsb" in data_encoding.lower()))
    if machine == "RISC-V":
        return "qemu-riscv32" if elf_class == "ELF32" else "qemu-riscv64" if elf_class == "ELF64" else None
    if machine and machine.startswith("MIPS"):
        bits = "64" if elf_class == "ELF64" else ""
        endian = "el" if little_endian else ""
        return f"qemu-mips{bits}{endian}"
    if machine == "PowerPC64" and little_endian:
        return "qemu-ppc64le"
    return QEMU_BY_MACHINE.get(machine)


def run(command: list[str], timeout: float = 4.0, env: dict[str, str] | None = None) -> dict:
    started = time.monotonic()
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            timeout=timeout, check=False, env=env,
        )
        return {
            "status": result.returncode,
            "output": result.stdout.strip()[:12000],
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
        }
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return {"status": None, "output": output[:12000], "timed_out": True,
                "elapsed_ms": round((time.monotonic() - started) * 1000, 2)}
    except OSError as exc:
        return {"status": None, "output": str(exc), "elapsed_ms": round((time.monotonic() - started) * 1000, 2)}


def find_headless() -> str | None:
    candidates: list[str] = []
    on_path = shutil.which("analyzeHeadless")
    if on_path:
        candidates.append(on_path)
    ghidra_home = os.environ.get("GHIDRA_HOME")
    if ghidra_home:
        candidates.append(str(Path(ghidra_home) / "support" / "analyzeHeadless"))
    candidates.extend(glob.glob("/usr/share/ghidra*/support/analyzeHeadless"))
    candidates.extend(glob.glob("/opt/ghidra*/support/analyzeHeadless"))
    for item in candidates:
        if os.path.isfile(item) and os.access(item, os.X_OK):
            return str(Path(item).resolve())
    return None


def inspect_binary(binary: Path, probe_ghidra: bool = False, include_versions: bool = False,
                   timeout: float = 4.0) -> dict:
    started = time.monotonic()
    if not binary.is_file():
        raise ValueError(f"target is not a regular file: {binary}")
    report: dict = {"target": str(binary.resolve()), "size_bytes": binary.stat().st_size}
    file_tool = shutil.which("file")
    readelf = shutil.which("readelf")
    report["tools"] = {
        name: shutil.which(name)
        for name in ("file", "readelf", "checksec", "objdump", "llvm-objdump",
                     "gdb", "gdb-multiarch", "radare2", "qemu-i386", "qemu-x86_64",
                     "qemu-aarch64", "qemu-arm", "qemu-armeb", "qemu-mips", "qemu-mipsel",
                     "qemu-mips64", "qemu-mips64el", "qemu-ppc", "qemu-ppc64", "qemu-ppc64le",
                     "qemu-riscv32", "qemu-riscv64", "java")
    }
    report["ghidra"] = {"analyze_headless": find_headless(), "java_available": bool(report["tools"]["java"])}

    if file_tool:
        report["file"] = run([file_tool, "-b", str(binary)], timeout)
    if readelf:
        header = run([readelf, "-h", "-l", "-d", str(binary)], timeout)
        report["readelf"] = header
        output = header["output"]
        elf_class = re.search(r"Class:\s+(ELF\d+)", output)
        machine = re.search(r"Machine:\s+(.+)", output)
        data_encoding = re.search(r"Data:\s+(.+)", output)
        elf_type = re.search(r"Type:\s+(.+)", output)
        interpreter = re.search(r"Requesting program interpreter:\s*([^]]+)", output)
        report["elf"] = {
            "class": elf_class.group(1) if elf_class else None,
            "machine": machine.group(1).strip() if machine else None,
            "type": elf_type.group(1).strip() if elf_type else None,
            "interpreter": interpreter.group(1).strip() if interpreter else None,
        }
        if interpreter:
            report["elf"]["interpreter_exists_on_host"] = Path(interpreter.group(1).strip()).exists()
        report["elf"]["data_encoding"] = data_encoding.group(1).strip() if data_encoding else None
        expected_qemu = recommend_qemu(report["elf"]["machine"], report["elf"]["class"], report["elf"]["data_encoding"])
        report["execution"] = {
            "host_machine": platform.machine(),
            "native_abi_match_candidate": bool(
                report["elf"]["machine"] and
                ((report["elf"]["machine"] == "Intel 80386" and platform.machine() in {"i386", "i486", "i586", "i686", "x86_64"})
                 or (report["elf"]["machine"] == "Advanced Micro Devices X86-64" and platform.machine() == "x86_64")
                 or (report["elf"]["machine"] == "AArch64" and platform.machine() == "aarch64"))
            ),
            "recommended_qemu": expected_qemu,
            "qemu_available": bool(expected_qemu and shutil.which(expected_qemu)),
            "target_was_executed": False,
            "native_compatibility_confirmed": False,
        }
    checksec = shutil.which("checksec")
    if checksec:
        # Pwntools may contact PyPI unless its update check is disabled. Isolate
        # its config/cache so this diagnostic stays deterministic and offline.
        with tempfile.TemporaryDirectory(prefix="ctf-reverse-checksec-", dir="/var/tmp") as home:
            home_path = Path(home)
            (home_path / ".pwn.conf").write_text("[update]\ninterval=never\n")
            env = {**os.environ, "HOME": home, "XDG_CACHE_HOME": str(home_path / ".cache"),
                   "XDG_CONFIG_HOME": str(home_path / ".config"),
                   "PYTHONUSERBASE": str(Path.home() / ".local")}
            report["protections"] = run([checksec, "--file=" + str(binary)], timeout, env)
    if probe_ghidra:
        headless = report["ghidra"]["analyze_headless"]
        if not headless:
            report["ghidra"]["probe"] = {"status": None, "output": "analyzeHeadless not found"}
        elif not report["ghidra"]["java_available"]:
            report["ghidra"]["probe"] = {"status": None, "output": "Java runtime not found"}
        else:
            # Check launcher readiness without creating a project or importing
            # the target; keep any first-run Java/Ghidra state out of /tmp/home.
            with tempfile.TemporaryDirectory(prefix="ctf-reverse-ghidra-", dir="/var/tmp") as home:
                env = {**os.environ, "HOME": home, "XDG_CONFIG_HOME": str(Path(home) / ".config"),
                       "XDG_CACHE_HOME": str(Path(home) / ".cache")}
                probe = run([headless, "-help"], timeout=timeout, env=env)
                probe["usage_displayed"] = "Headless Analyzer Usage:" in probe["output"]
                probe["ready"] = probe["status"] == 0 or probe["usage_displayed"]
                report["ghidra"]["probe"] = probe
    if include_versions:
        version_commands = {
            "file": ["file", "--version"],
            "readelf": ["readelf", "--version"],
            "objdump": ["objdump", "--version"],
            "gdb": ["gdb", "--version"],
            "qemu": ([report["execution"]["recommended_qemu"], "--version"]
                     if report.get("execution", {}).get("recommended_qemu") else None),
            "java": ["java", "-version"],
        }
        report["tool_versions"] = {}
        for name, command in version_commands.items():
            if command and shutil.which(command[0]):
                result = run(command, timeout)
                report["tool_versions"][name] = {
                    "status": result["status"],
                    "output": result["output"].splitlines()[:4],
                    "elapsed_ms": result["elapsed_ms"],
                }
    report["report_elapsed_ms"] = round((time.monotonic() - started) * 1000, 2)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path, help="ELF to inspect; the target is never executed")
    parser.add_argument("--probe-ghidra", action="store_true",
                        help="explicitly launch analyzeHeadless -help (no project or target import)")
    parser.add_argument("--versions", action="store_true",
                        help="run version commands for available tools (adds process startup time)")
    parser.add_argument("--timeout", type=float, default=4.0,
                        help="per-tool timeout in seconds (default: 4)")
    args = parser.parse_args(argv)
    try:
        if args.timeout <= 0:
            raise ValueError("--timeout must be positive")
        print(json.dumps(inspect_binary(args.binary, args.probe_ghidra, args.versions, args.timeout), indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
