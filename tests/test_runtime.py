#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = REPO_ROOT / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

import boss_runtime
from boss_runtime import RUNTIME_COMMANDS, cmd_runtime, resolve_runtime_executable

LOADER = importlib.machinery.SourceFileLoader("boss_cli", str(BIN_DIR / "boss"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
boss_cli = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(boss_cli)


class RuntimeResolutionTests(unittest.TestCase):
    def make_runtime(self, root: Path, command: str, platform: str = "linux") -> Path:
        runtime_bin = root / ".runtime" / "bin"
        runtime_bin.mkdir(parents=True, exist_ok=True)
        executable = runtime_bin / boss_runtime.executable_name(command, platform)
        executable.write_text("#!/bin/sh\n", encoding="utf-8")
        executable.chmod(0o755)
        return executable

    def test_resolves_unix_tools_only_inside_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for command in RUNTIME_COMMANDS:
                with self.subTest(command=command):
                    executable = self.make_runtime(root, command)
                    self.assertEqual(resolve_runtime_executable(command, root, "linux"), executable)

    def test_resolves_windows_shims(self) -> None:
        expected = {
            "bun": "bun.exe",
            "uv": "uv.exe",
            "python": "python.cmd",
            "node": "node.cmd",
            "npm": "npm.cmd",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for command, filename in expected.items():
                with self.subTest(command=command):
                    executable = self.make_runtime(root, command, "win32")
                    self.assertEqual(executable.name, filename)
                    self.assertEqual(resolve_runtime_executable(command, root, "win32"), executable)

    def test_missing_runtime_directory_has_repair_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(boss_runtime.subprocess, "run") as run:
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    self.assertEqual(cmd_runtime("node", ["--version"], root, "linux"), 1)
            run.assert_not_called()
            self.assertIn("未找到 Boss 独立运行时目录", stderr.getvalue())
            self.assertIn("boss setup-runtime", stderr.getvalue())

    def test_missing_tool_does_not_fall_back_to_system_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".runtime" / "bin").mkdir(parents=True)
            with patch.object(boss_runtime.subprocess, "run") as run:
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    self.assertEqual(cmd_runtime("npm", ["--version"], root, "linux"), 1)
            run.assert_not_called()
            self.assertIn("缺少 npm 工具", stderr.getvalue())
            self.assertIn("boss setup-runtime", stderr.getvalue())

    def test_rejects_tool_without_execute_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = self.make_runtime(root, "python")
            with patch.object(boss_runtime.os, "access", return_value=False):
                with self.assertRaisesRegex(boss_runtime.RuntimeUnavailableError, "执行权限"):
                    resolve_runtime_executable("python", root, "linux")
            self.assertTrue(executable.exists())


class RuntimeExecutionTests(unittest.TestCase):
    def test_passes_arguments_unchanged_and_preserves_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / ".runtime" / "bin" / "node"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            args = ["script with spaces.mjs", "--flag", "value with spaces", "--", "-x"]
            completed = subprocess.CompletedProcess(args=[], returncode=23)
            with patch.object(boss_runtime.subprocess, "run", return_value=completed) as run:
                self.assertEqual(cmd_runtime("node", args, root, "linux"), 23)
            run.assert_called_once_with([str(executable), *args])

    def test_start_failure_is_clear_and_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / ".runtime" / "bin" / "bun"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            stderr = io.StringIO()
            with (
                patch.object(boss_runtime.subprocess, "run", side_effect=OSError("bad executable")),
                contextlib.redirect_stderr(stderr),
            ):
                self.assertEqual(cmd_runtime("bun", ["--version"], root, "linux"), 1)
            self.assertIn("无法启动 Boss 独立运行时工具 bun", stderr.getvalue())
            self.assertIn("boss setup-runtime", stderr.getvalue())


class BossDispatchTests(unittest.TestCase):
    def test_dispatches_every_runtime_command(self) -> None:
        for command in RUNTIME_COMMANDS:
            with self.subTest(command=command):
                with (
                    patch.object(boss_cli, "cmd_runtime", return_value=0) as run,
                    patch.object(sys, "argv", ["boss", command, "--version"]),
                ):
                    self.assertEqual(boss_cli.main(), 0)
                run.assert_called_once_with(command, ["--version"])

    def test_help_lists_all_runtime_commands(self) -> None:
        stdout = io.StringIO()
        with (
            patch.object(sys, "argv", ["boss", "--help"]),
            contextlib.redirect_stdout(stdout),
        ):
            self.assertEqual(boss_cli.main(), 0)
        for command in RUNTIME_COMMANDS:
            self.assertIn(f"  {command} [参数...]", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
