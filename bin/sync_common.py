#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""不同下载方法共用的文件、指纹与同步状态工具。"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".DS_Store", "node_modules")


def log(message: str) -> None:
    print(message, flush=True)


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        details = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"命令失败：{' '.join(cmd)}\n{details}")
    return proc.stdout


def digest_dir(path: Path) -> str:
    """目录内容指纹只取决于相对路径和文件字节。"""
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def target_dir(registry_dir: Path, relative_path: str) -> Path:
    """确保清单或旧锁文件不能把同步内容写到 registry/.synced/ 之外。"""
    target = (registry_dir / relative_path).resolve()
    try:
        target.relative_to(registry_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"技能安装路径越界：{relative_path}") from exc
    return target


def suite_paths(lock_installed: dict, source_id: str, suite: str) -> list[str]:
    return [
        path
        for path, value in lock_installed.items()
        if value.get("from") == source_id
        and (value.get("suite") == suite or path.startswith(f"{suite}/"))
    ]


def local_sync_status(
    entries: list[dict], source_id: str, lock_installed: dict, registry_dir: Path
) -> str | None:
    """返回最直观的本地状态；None 表示本地内容与锁定记录一致。"""
    installed_paths = []
    for entry in entries:
        if entry.get("skill") == "*":
            paths = suite_paths(lock_installed, source_id, entry["to"])
            if not paths:
                return "尚未下载"
            installed_paths.extend(paths)
        else:
            path = entry["to"]
            if path not in lock_installed:
                return "尚未下载"
            installed_paths.append(path)

    for path in installed_paths:
        if not (target_dir(registry_dir, path) / "SKILL.md").is_file():
            return "本地文件缺失，需要重新下载"

    for path in installed_paths:
        target = target_dir(registry_dir, path)
        if digest_dir(target) != lock_installed[path].get("digest"):
            return "本地内容被修改，同步会覆盖修改"

    return None


def preserve_entries(entries: list[dict], source_id: str, lock_installed: dict, new_installed: dict) -> None:
    """无需重新下载时，完整保留单项技能或套件的旧锁定记录。"""
    for entry in entries:
        if entry.get("skill") == "*":
            for path in suite_paths(lock_installed, source_id, entry["to"]):
                new_installed[path] = lock_installed[path]
        elif entry["to"] in lock_installed:
            new_installed[entry["to"]] = lock_installed[entry["to"]]


def copy_skill(source_dir: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source_dir, target, ignore=IGNORE)
