#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 Boss 调用仓库内的独立运行时。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
RUNTIME_COMMANDS = ("bun", "uv", "python", "node", "npm")
WINDOWS_EXECUTABLES = {
    "bun": "bun.exe",
    "uv": "uv.exe",
    "python": "python.cmd",
    "node": "node.cmd",
    "npm": "npm.cmd",
}


class RuntimeUnavailableError(RuntimeError):
    """独立运行时目录或目标工具不可用。"""


def executable_name(command: str, platform: str) -> str:
    """返回目标工具在当前系统中的垫片文件名。"""
    if command not in RUNTIME_COMMANDS:
        raise ValueError(f"不支持的运行时命令: {command}")
    if platform.startswith("win"):
        return WINDOWS_EXECUTABLES[command]
    return command


def resolve_runtime_executable(
    command: str,
    root_dir: Path = ROOT_DIR,
    platform: str | None = None,
) -> Path:
    """定位并检查沙盒工具，绝不回退到 PATH 中的系统版本。"""
    platform = sys.platform if platform is None else platform
    filename = executable_name(command, platform)
    runtime_bin = root_dir / ".runtime" / "bin"
    repair_hint = "请先运行 `boss setup-runtime` 安装或修复独立运行时。"

    if not runtime_bin.is_dir():
        raise RuntimeUnavailableError(
            f"未找到 Boss 独立运行时目录: {runtime_bin}\n{repair_hint}"
        )

    executable = runtime_bin / filename
    if not executable.is_file():
        raise RuntimeUnavailableError(
            f"Boss 独立运行时缺少 {command} 工具: {executable}\n{repair_hint}"
        )
    if not platform.startswith("win") and not os.access(executable, os.X_OK):
        raise RuntimeUnavailableError(
            f"Boss 独立运行时工具没有执行权限: {executable}\n{repair_hint}"
        )
    return executable


def cmd_runtime(
    command: str,
    args: list[str],
    root_dir: Path = ROOT_DIR,
    platform: str | None = None,
) -> int:
    """将参数原样交给沙盒工具，并保留它的退出码。"""
    try:
        executable = resolve_runtime_executable(command, root_dir, platform)
    except RuntimeUnavailableError as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1

    try:
        result = subprocess.run([str(executable), *args])
    except OSError as error:
        print(
            f"❌ 无法启动 Boss 独立运行时工具 {command}: {error}\n"
            "请运行 `boss setup-runtime` 修复独立运行时。",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        return 130
    return result.returncode
