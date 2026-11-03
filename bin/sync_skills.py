#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把清单中的第三方技能同步到各 Profile 的 registry/.synced/。

默认 Profile 使用仓库根目录的 sources.json、sources.lock.json 和 registry/。
config.json 中启用的 Profile 使用 profiles/<name>/ 下的同一组路径。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from skill_boss_profiles import Profile, load_profiles

BIN_DIR = Path(__file__).resolve().parent
REPO_ROOT = BIN_DIR.parent

# 复制技能包时跳过版本控制、缓存和系统垃圾。
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".DS_Store", "node_modules")


def log(message: str) -> None:
    print(message, flush=True)


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败：{' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout


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


def digest_dir(path: Path) -> str:
    """目录内容指纹只取决于相对路径和文件字节。"""
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def clone_sparse(repo: str, ref: str, subdirs: list[str], dest: Path) -> None:
    """只下载需要的子目录；服务端不支持 blob 过滤时退回普通浅克隆。"""
    base = ["git", "clone", "--quiet", "--depth", "1", "--branch", ref, "--sparse"]
    for extra in (["--filter=blob:none"], []):
        if dest.exists():
            shutil.rmtree(dest)
        try:
            run(base + extra + [repo, str(dest)])
            break
        except RuntimeError:
            continue
    else:
        raise RuntimeError(f"无法克隆 {repo}")
    run(["git", "-C", str(dest), "sparse-checkout", "set", *subdirs])


def load_lock(lock_file: Path) -> dict:
    if lock_file.is_file():
        try:
            return json.loads(lock_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log(f"⚠ {lock_file} 内容损坏，将重建。")
    return {}


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

            current_ok = True
            for entry in entries:
                if entry.get("skill") == "*":
                    installed_suite = suite_paths(lock_installed, source_id, entry["to"])
                    if not installed_suite:
                        current_ok = False
                        break
                    for path in installed_suite:
                        target = target_dir(registry_dir, path)
                        if not (target / "SKILL.md").is_file() or digest_dir(target) != lock_installed[path].get("digest"):
                            current_ok = False
                            break
                    if not current_ok:
                        break
                else:
                    target = target_dir(registry_dir, entry["to"])
                    if not (target / "SKILL.md").is_file() or digest_dir(target) != lock_installed.get(entry["to"], {}).get("digest"):
                        current_ok = False
                        break

            if not commit_changed and current_ok:
                log(f"✓ {source_id}: 已是最新 ({commit[:8]})")
                preserve_entries(entries, source_id, lock_installed, new_installed)
                continue

            reasons = []
            if commit_changed:
                reasons.append(f"上游更新 {str(previous_commit)[:8]} → {commit[:8]}")
            if not current_ok:
                reasons.append("本地目录缺失或被改动")
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
            log("\n发现上游更新或本地改动。运行 boss sync-skills 进行同步。")
            return 1
        log("\n全部已是最新。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
