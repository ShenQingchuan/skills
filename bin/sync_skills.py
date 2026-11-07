#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把清单中的第三方技能同步到各 Profile 的 registry/.synced/。

默认 Profile 使用仓库根目录的 sources.json、sources.lock.json 和 registry/。
config.json 中启用的 Profile 使用 profiles/<name>/ 下的同一组路径。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath

from skill_boss_profiles import Profile, load_profiles
from sync_common import (
    copy_skill,
    digest_dir,
    local_sync_status,
    log,
    preserve_entries,
    run,
    target_dir,
)
from sync_fskillhub import sync_source as sync_fskillhub_source

BIN_DIR = Path(__file__).resolve().parent
REPO_ROOT = BIN_DIR.parent


def resolve_ref(repo: str, ref: str) -> tuple[str, str]:
    """精确解析上游分支、标签或清单中直接固定的 commit。"""
    output = run(["git", "ls-remote", "--refs", repo])
    refs = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2:
            refs[parts[1]] = parts[0]

    for candidate in (f"refs/heads/{ref}", f"refs/tags/{ref}"):
        if candidate in refs:
            return candidate, refs[candidate]
    if re.fullmatch(r"[0-9a-f]{7,40}", ref):
        return ref, ref
    raise RuntimeError(f"{repo} 上找不到 ref：{ref}")


def sparse_targets(subdirs: list[str]) -> list[str] | None:
    """把清单里的仓库内路径换算成 sparse-checkout 参数。

    返回 None 表示技能就是整个仓库：sparse-checkout 只能勾选子目录，
    勾选根目录会丢掉全部子目录，所以这种情况必须整仓克隆。
    """
    cleaned = set()
    for subdir in subdirs:
        parts = [part for part in PurePosixPath(subdir).parts if part not in ("", ".")]
        if not parts:
            return None
        cleaned.add("/".join(parts))
    return sorted(cleaned)


def clone_sparse(repo: str, ref: str, subdirs: list[str], dest: Path) -> None:
    """只下载需要的子目录；服务端不支持 blob 过滤时退回普通浅克隆。"""
    targets = sparse_targets(subdirs)
    base = ["git", "clone", "--quiet", "--depth", "1", "--branch", ref]
    if targets is not None:
        base.append("--sparse")

    filters = ["--filter=blob:none", ""] if targets is not None else [""]
    for blob_filter in filters:
        if dest.exists():
            shutil.rmtree(dest)
        extra = [blob_filter] if blob_filter else []
        try:
            run(base + extra + [repo, str(dest)])
            break
        except RuntimeError:
            continue
    else:
        raise RuntimeError(f"无法克隆 {repo}")

    if targets is not None:
        run(["git", "-C", str(dest), "sparse-checkout", "set", *targets])


def load_lock(lock_file: Path) -> dict:
    if lock_file.is_file():
        try:
            return json.loads(lock_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log(f"⚠ {lock_file} 内容损坏，将重建。")
    return {}


def sync_profile(profile: Profile, check: bool = False) -> bool:
    """同步一个 Profile，返回是否存在上游更新或本地差异。"""
    if not profile.manifest_file.is_file():
        raise FileNotFoundError(f"Profile {profile.name!r} 缺少清单：{profile.manifest_file}")

    log(f"\n📦 Profile: {profile.name}")
    manifest = json.loads(profile.manifest_file.read_text(encoding="utf-8"))
    sources: dict = manifest["sources"]
    install: list[dict] = manifest["install"]

    lock = load_lock(profile.lock_file)
    lock_sources: dict = lock.get("sources", {})
    lock_installed: dict = lock.get("installed", {})
    registry_dir = profile.synced_dir

    grouped: dict[str, list[dict]] = {}
    for entry in install:
        grouped.setdefault(entry["from"], []).append(entry)

    new_sources: dict = {}
    new_installed: dict = {}
    needs_update = False
    touched: list[str] = []

    workdir = Path(tempfile.mkdtemp(prefix=f"skills-sync-{profile.name}-"))
    try:
        for source_id, entries in grouped.items():
            spec = sources[source_id]
            method = spec.get("method", "git")
            if method == "fskillhub":
                result = sync_fskillhub_source(
                    REPO_ROOT,
                    source_id,
                    spec,
                    entries,
                    lock_installed,
                    registry_dir,
                    workdir / f"fskillhub-{len(new_sources)}",
                    check,
                )
                new_sources[source_id] = result.source
                new_installed.update(result.installed)
                needs_update = result.needs_update or needs_update
                touched.extend(result.touched)
                continue
            if method != "git":
                raise ValueError(f"{source_id} 使用了不支持的下载方法：{method}")

            repo, ref, skills_dir = spec["repo"], spec["ref"], spec["skillsDir"]

            try:
                resolved_ref, commit = resolve_ref(repo, ref)
            except RuntimeError as exc:
                log(f"⚠ {source_id}: 无法查询上游（{exc}）。保留上次记录。")
                if source_id in lock_sources:
                    new_sources[source_id] = lock_sources[source_id]
                preserve_entries(entries, source_id, lock_installed, new_installed)
                needs_update = True
                continue

            new_sources[source_id] = {
                "repo": repo,
                "ref": ref,
                "resolvedRef": resolved_ref,
                "commit": commit,
            }
            previous_commit = lock_sources.get(source_id, {}).get("commit")
            commit_changed = previous_commit != commit

            local_status = local_sync_status(entries, source_id, lock_installed, registry_dir)

            if not commit_changed and local_status is None:
                log(f"✓ {source_id}: 已是最新 ({commit[:8]})")
                preserve_entries(entries, source_id, lock_installed, new_installed)
                continue

            reasons = []
            if previous_commit and commit_changed:
                reasons.append(f"需要更新（上游版本 {previous_commit[:8]} → {commit[:8]}）")
            elif not previous_commit and local_status is None:
                reasons.append(f"需要重新同步（尚无上游版本记录，当前版本 {commit[:8]}）")
            if local_status is not None:
                reasons.append(local_status)
            needs_update = True

            if check:
                log(f"⚠ {source_id}: {'；'.join(reasons)}")
                preserve_entries(entries, source_id, lock_installed, new_installed)
                continue

            log(f"↓ {source_id}: {'；'.join(reasons)}")
            checkout = workdir / source_id
            has_suite = any(entry.get("skill") == "*" for entry in entries)
            if has_suite:
                subdirs = [skills_dir]
            else:
                subdirs = sorted({f"{skills_dir}/{entry['skill']}" for entry in entries})
            clone_sparse(repo, ref, subdirs, checkout)

            for entry in entries:
                if entry.get("skill") == "*":
                    suite_root = checkout / skills_dir
                    found_skills = sorted(
                        p for p in suite_root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
                    ) if suite_root.is_dir() else []
                    if not found_skills:
                        log(f"  ✗ {source_id}: 套件目录 ({skills_dir}) 下未找到任何有效技能")
                        continue
                    for skill_dir in found_skills:
                        target_rel = f"{entry['to']}/{skill_dir.name}"
                        target = target_dir(registry_dir, target_rel)
                        copy_skill(skill_dir, target)
                        new_installed[target_rel] = {
                            "from": source_id,
                            "skill": skill_dir.name,
                            "suite": entry["to"],
                            "digest": digest_dir(target),
                        }
                        touched.append(target_rel)
                        log(f"  + {target_rel}")
                else:
                    source_dir = checkout / skills_dir / entry["skill"]
                    if not (source_dir / "SKILL.md").is_file():
                        log(f"  ✗ {entry['skill']}: 上游没有 SKILL.md，已跳过")
                        continue
                    copy_skill(source_dir, target_dir(registry_dir, entry["to"]))
                    target = target_dir(registry_dir, entry["to"])
                    new_installed[entry["to"]] = {
                        "from": source_id,
                        "skill": entry["skill"],
                        "digest": digest_dir(target),
                    }
                    touched.append(entry["to"])
                    log(f"  + {entry['to']}")

        wanted = set(new_installed.keys())
        for stale_path in [path for path in lock_installed if path not in wanted]:
            stale_dir = target_dir(registry_dir, stale_path)
            if check:
                log(f"⚠ 已从清单移除：{stale_path}")
                needs_update = True
                continue
            if stale_dir.exists():
                shutil.rmtree(stale_dir)
                log(f"  - {stale_path}（已从清单移除）")
            touched.append(stale_path)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if check:
        return needs_update

    profile.lock_file.parent.mkdir(parents=True, exist_ok=True)
    profile.lock_file.write_text(
        json.dumps(
            {
                "generatedBy": "boss (bin/sync_skills.py)",
                "sources": new_sources,
                "installed": new_installed,
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    if touched:
        log(f"\n本次变更 {len(touched)} 项：")
        for path in touched:
            log(f"  · {path}")
    else:
        log("\n没有变化。")
    return needs_update


def main() -> int:
    parser = argparse.ArgumentParser(description="同步默认 Profile 及 config.json 中启用的私有 Profile")
    parser.add_argument("--check", action="store_true", help="只检查更新，不写任何文件")
    args = parser.parse_args()

    try:
        profiles = load_profiles(REPO_ROOT)
        needs_update = False
        for profile in profiles:
            needs_update = sync_profile(profile, check=args.check) or needs_update
    except (FileNotFoundError, KeyError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        log(f"❌ 同步失败：{exc}")
        return 1

    if args.check:
        if needs_update:
            log("\n有技能需要下载、更新或重新同步。运行 boss sync-skills 进行同步。")
            return 1
        log("\n全部已是最新。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
