#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Profile 路径与本机启用配置的统一定义。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    """一个同构技能空间：清单、锁文件和 registry 都位于同一目录。"""

    name: str
    root_dir: Path

    @property
    def manifest_file(self) -> Path:
        return self.root_dir / "sources.json"

    @property
    def lock_file(self) -> Path:
        return self.root_dir / "sources.lock.json"

    @property
    def registry_dir(self) -> Path:
        return self.root_dir / "registry"

    @property
    def synced_dir(self) -> Path:
        return self.registry_dir / ".synced"


def validate_profile_name(name: str) -> None:
    """Profile 名必须是单层、非隐藏的目录名，避免路径穿越。"""
    if (
        not name
        or name.strip() != name
        or name.startswith(".")
        or name in {".", ".."}
        or "/" in name
        or "\\" in name
    ):
        raise ValueError(f"无效的 Profile 名称：{name!r}")


def load_active_profile_names(config_file: Path) -> list[str]:
    """读取本机启用的 Profile；没有 config.json 时只使用默认 Profile。"""
    if not config_file.is_file():
        return []

    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"本机配置不是有效 JSON：{config_file}\n{exc}") from exc

    if not isinstance(config, dict) or not isinstance(config.get("activeProfiles", []), list):
        raise ValueError(f"本机配置的 activeProfiles 必须是字符串数组：{config_file}")

    names: list[str] = []
    for name in config.get("activeProfiles", []):
        if not isinstance(name, str):
            raise ValueError(f"本机配置的 activeProfiles 必须是字符串数组：{config_file}")
        validate_profile_name(name)
        if name == "default":
            raise ValueError("default 是内置 Profile，不需要写入 activeProfiles")
        if name not in names:
            names.append(name)
    return names


def load_profiles(repo_root: Path) -> list[Profile]:
    """默认 Profile 始终加载，其后按 config.json 中的顺序叠加私有 Profile。"""
    repo_root = repo_root.resolve()
    profiles = [Profile(name="default", root_dir=repo_root)]
    config_file = repo_root / "config.json"
    profiles_dir = repo_root / "profiles"
    for name in load_active_profile_names(config_file):
        profiles.append(Profile(name=name, root_dir=profiles_dir / name))
    return profiles
