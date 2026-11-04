#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用公司 Fskillhub CLI 下载技能，并接入统一同步锁。"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from sync_common import (
    copy_skill,
    digest_dir,
    local_sync_status,
    log,
    preserve_entries,
    run,
    target_dir,
)


@dataclass(frozen=True)
class DownloadedSkill:
    directory: Path
    version: str


@dataclass
class SourceSyncResult:
    source: dict
    installed: dict
    needs_update: bool
    touched: list[str]


def runtime_npx(repo_root: Path) -> Path:
    executable = "npx.cmd" if sys.platform.startswith("win") else "npx"
    npx = repo_root / ".runtime" / "bin" / executable
    if not npx.is_file():
        raise RuntimeError("未找到仓库独立 Node 运行时，请先执行 `boss setup-runtime`")
    return npx


def read_origin(skill_dir: Path, requested_slug: str) -> str:
    origin_file = skill_dir / ".fskillhub" / "origin.json"
    try:
        origin = json.loads(origin_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Fskillhub 没有生成有效的来源记录：{origin_file}") from exc

    actual_slug = origin.get("slug")
    slug_matches = actual_slug == requested_slug
    if "@" not in requested_slug:
        slug_matches = actual_slug == requested_slug or str(actual_slug).endswith(f"@{requested_slug}")
    if not slug_matches:
        raise RuntimeError(f"Fskillhub 安装了错误技能：期望 {requested_slug}，实际 {actual_slug}")

    version = origin.get("installedVersion")
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"Fskillhub 来源记录缺少安装版本：{origin_file}")
    return version


def download_skill(
    repo_root: Path, source: dict, entry: dict, workdir: Path
) -> DownloadedSkill:
    """在独立目录安装一个技能，不向正式 registry 写入任何文件。"""
    slug = entry["skill"]
    if slug == "*" or "/" in slug or "\\" in slug:
        raise ValueError(f"无效的 Fskillhub 技能标识：{slug!r}")

    command = [
        str(runtime_npx(repo_root)),
        "-y",
        "--registry",
        source["npmRegistry"],
        source.get("tool", "@futu/fskillhub@latest"),
        "--workdir",
        str(workdir),
        "--dir",
        "skills",
        "--no-input",
        "--registry",
        source["registry"],
        "install",
        slug,
    ]
    if entry.get("version"):
        command.extend(["--version", str(entry["version"])])
    run(command)

    skill_name = slug.rsplit("@", 1)[-1]
    skill_dir = workdir / "skills" / skill_name
    if not (skill_dir / "SKILL.md").is_file():
        raise RuntimeError(f"Fskillhub 下载结果缺少 SKILL.md：{skill_dir}")
    version = read_origin(skill_dir, slug)

    # 安装时间等工具私有状态不参与同步指纹；来源和版本由统一锁文件保存。
    shutil.rmtree(skill_dir / ".fskillhub", ignore_errors=True)
    return DownloadedSkill(directory=skill_dir, version=version)


def sync_source(
    repo_root: Path,
    source_id: str,
    source: dict,
    entries: list[dict],
    lock_installed: dict,
    registry_dir: Path,
    workdir: Path,
    check: bool,
) -> SourceSyncResult:
    """下载并比较一组公司技能；失败时保留对应旧记录。"""
    source_lock = {
        "method": "fskillhub",
        "tool": source.get("tool", "@futu/fskillhub@latest"),
        "npmRegistry": source["npmRegistry"],
        "registry": source["registry"],
    }
    installed: dict = {}
    touched: list[str] = []
    needs_update = False

    for index, entry in enumerate(entries):
        path = entry["to"]
        previous = lock_installed.get(path)
        local_status = local_sync_status([entry], source_id, lock_installed, registry_dir)
        try:
            downloaded = download_skill(repo_root, source, entry, workdir / str(index))
        except RuntimeError as exc:
            log(f"⚠ {source_id}/{entry['skill']}: 无法查询或下载（{exc}）。保留上次记录。")
            preserve_entries([entry], source_id, lock_installed, installed)
            needs_update = True
            continue

        remote_digest = digest_dir(downloaded.directory)
        version_changed = bool(previous and previous.get("version") != downloaded.version)
        content_changed = bool(previous and previous.get("digest") != remote_digest)
        if local_status is None and not version_changed and not content_changed:
            log(f"✓ {path}: 已是最新 ({downloaded.version})")
            preserve_entries([entry], source_id, lock_installed, installed)
            continue

        reasons = []
        if version_changed:
            reasons.append(f"需要更新（上游版本 {previous.get('version', '未知')} → {downloaded.version}）")
        elif content_changed:
            reasons.append("上游同版本内容发生变化，需要重新同步")
        if local_status is not None:
            reasons.append(local_status)
        needs_update = True

        if check:
            log(f"⚠ {path}: {'；'.join(reasons)}")
            preserve_entries([entry], source_id, lock_installed, installed)
            continue

        log(f"↓ {path}: {'；'.join(reasons)}")
        target = target_dir(registry_dir, path)
        copy_skill(downloaded.directory, target)
        installed[path] = {
            "from": source_id,
            "method": "fskillhub",
            "skill": entry["skill"],
            "version": downloaded.version,
            "digest": digest_dir(target),
        }
        touched.append(path)
        log(f"  + {path} ({downloaded.version})")

    return SourceSyncResult(source_lock, installed, needs_update, touched)
