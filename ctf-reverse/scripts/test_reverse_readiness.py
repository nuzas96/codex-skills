#!/usr/bin/env python3
"""Small deterministic tests for reverse_readiness.py using a benign ELF32 fixture."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from reverse_readiness import inspect_binary, recommend_qemu, run


class ReverseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assembler = shutil.which("as")
        cls.linker = shutil.which("ld")
        if not cls.assembler or not cls.linker or not shutil.which("readelf"):
            raise unittest.SkipTest("binutils are required for the benign ELF32 fixture")
        cls.temp = tempfile.TemporaryDirectory(prefix="ctf-reverse-readiness-")
        cls.root = Path(cls.temp.name)
        source = cls.root / "hello.s"
        source.write_text(
            ".global _start\n.section .text\n_start:\n"
            "mov $1, %eax\nmov $0, %ebx\nint $0x80\n"
        )
        subprocess.run([cls.assembler, "--32", "-o", str(cls.root / "hello.o"), str(source)],
                       check=True, timeout=5)
        subprocess.run([cls.linker, "-m", "elf_i386", "-static", "-o", str(cls.root / "hello32"),
                        str(cls.root / "hello.o")], check=True, timeout=5)
        source.write_text(".global dummy\n.section .text\ndummy:\nret\n")
        subprocess.run([cls.assembler, "--32", "-o", str(cls.root / "dummy.o"), str(source)],
                       check=True, timeout=5)
        subprocess.run([cls.linker, "-m", "elf_i386", "-shared", "-soname", "libdummy.so",
                        "-o", str(cls.root / "libdummy.so"), str(cls.root / "dummy.o")],
                       check=True, timeout=5)
        subprocess.run([cls.linker, "-m", "elf_i386", "--dynamic-linker", "/lib/ld-linux.so.2",
                        "-L" + str(cls.root), "-o", str(cls.root / "dynamic32"),
                        str(cls.root / "hello.o"), "-ldummy"], check=True, timeout=5)
        subprocess.run([cls.linker, "-m", "elf_i386", "--dynamic-linker", "/definitely/missing/ld-i386.so",
                        "-L" + str(cls.root), "-o", str(cls.root / "missing-loader32"),
                        str(cls.root / "hello.o"), "-ldummy"], check=True, timeout=5)
        cls.binary = cls.root / "hello32"

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def test_parses_architecture_and_reports_tools_without_running_binary(self):
        report = inspect_binary(self.binary)
        self.assertEqual(report["elf"]["class"], "ELF32")
        self.assertEqual(report["elf"]["machine"], "Intel 80386")
        self.assertIsNone(report["elf"]["interpreter"])
        self.assertFalse(report["execution"]["target_was_executed"])
        self.assertFalse(report["execution"]["native_compatibility_confirmed"])
        self.assertEqual(report["execution"]["recommended_qemu"], "qemu-i386")
        self.assertGreater(report["report_elapsed_ms"], 0)
        if report["tools"]["checksec"]:
            self.assertEqual(report["protections"]["status"], 0, report["protections"]["output"])

    def test_nonexistent_target_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "regular file"):
            inspect_binary(self.root / "missing")

    def test_qemu_selection_accounts_for_elf_width_and_endianness(self):
        self.assertEqual(recommend_qemu("RISC-V", "ELF32", "2's complement, little endian"), "qemu-riscv32")
        self.assertEqual(recommend_qemu("RISC-V", "ELF64", "2's complement, little endian"), "qemu-riscv64")
        self.assertEqual(recommend_qemu("MIPS R3000", "ELF32", "2's complement, little endian"), "qemu-mipsel")
        self.assertEqual(recommend_qemu("MIPS", "ELF64", "2's complement, big endian"), "qemu-mips64")

    def test_dynamic_linker_presence_and_missing_loader_are_reported(self):
        present = inspect_binary(self.root / "dynamic32")["elf"]
        missing = inspect_binary(self.root / "missing-loader32")["elf"]
        self.assertEqual(present["interpreter"], "/lib/ld-linux.so.2")
        self.assertEqual(missing["interpreter"], "/definitely/missing/ld-i386.so")
        self.assertFalse(missing["interpreter_exists_on_host"])

    def test_tool_timeout_is_reported_without_unbounded_wait(self):
        result = run(["python3", "-c", "import time; time.sleep(5)"], timeout=0.05)
        self.assertTrue(result.get("timed_out"))
        self.assertIsNone(result["status"])


if __name__ == "__main__":
    unittest.main()
