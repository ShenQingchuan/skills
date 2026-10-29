#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把第三方技能同步进 registry/。

用法
----
    python3 tools/sync_skills.py            # 拉取上游并更新 registry/
    python3 tools/sync_skills.py --check    # 只检查有没有更新；有则退出码 1，不写任何文件

原理
----
registry/ 里的第三方技能是**产物**，不是源头。源头永远是上游仓库。
所以这里只维护两份状态：

    tools/sources.json       人写的：从哪个仓库、拿哪些技能、放到哪里（声明）
    tools/sources.lock.json  机器写的：上游 commit + 每个技能目录的内容指纹（事实）

脚本负责把「声明」变成「事实」，并且要做到：幂等（跑一百遍结果一样）、
可重复（内容只取决于上游 commit，不取决于运行时间或机器）、可无人值守（CI 里也能跑）。

注意
----
registry/ 里由本脚本管理的目录不要手改：下次同步会原样覆盖。
要改就改上游，或者把 sources.json 里的 repo 换成你自己的 fork。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
REGISTRY_DIR = REPO_ROOT / "skills-router" / "registry"
MANIFEST_FILE = TOOLS_DIR / "sources.json"
LOCK_FILE = TOOLS_DIR / "sources.lock.json"

# 复制技能包时跳过的东西：版本控制、缓存、系统垃圾
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".DS_Store", "node_modules")


def log(message: str) -> None:
    print(message, flush=True)


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"命令失败：{' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout


def resolve_commit(repo: str, ref: str) -> str:
    """不下拉仓库，直接问远端：这个 ref 现在指向哪个 commit。"""
    output = run(["git", "ls-remote", repo, ref])
    for line in output.splitlines():
        parts = line.split()
        if len(parts) == 2:
            return parts[0]
    raise RuntimeError(f"{repo} 上找不到 ref：{ref}")


def digest_dir(path: Path) -> str:
    """目录内容指纹：只取决于「相对路径 + 文件字节」，跟时间无关。"""
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def clone_sparse(repo: str, ref: str, subdirs: list[str], dest: Path) -> None:
    """只下载需要的子目录，不把整个仓库拉下来。"""
    base = ["git", "clone", "--quiet", "--depth", "1", "--branch", ref, "--sparse"]
    # 先试 blob 过滤（更省流量），不支持就退回普通浅克隆
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


def load_lock() -> dict:
    if LOCK_FILE.is_file():
        try:
            return json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log(f"⚠ {LOCK_FILE.name} 内容损坏，将重建。")
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="同步第三方技能到 registry/")
    parser.add_argument("--check", action="store_true", help="只检查是否有上游更新，不写任何文件")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    sources: dict = manifest["sources"]
    install: list[dict] = manifest["install"]

    lock = load_lock()
    lock_sources: dict = lock.get("sources", {})
    lock_installed: dict = lock.get("installed", {})

    grouped: dict[str, list[dict]] = {}
    for entry in install:
        grouped.setdefault(entry["from"], []).append(entry)

    new_sources: dict = {}
    new_installed: dict = {}
    needs_update = False
    touched: list[str] = []

    workdir = Path(tempfile.mkdtemp(prefix="skills-sync-"))
    try:
        for source_id, entries in grouped.items():
            spec = sources[source_id]
            repo, ref, skills_dir = spec["repo"], spec["ref"], spec["skillsDir"]

            try:
                commit = resolve_commit(repo, ref)
            except RuntimeError as exc:
                log(f"⚠ {source_id}: 无法查询上游（{exc}）。保留上次记录。")
                if source_id in lock_sources:
                    new_sources[source_id] = lock_sources[source_id]
                for entry in entries:
                    if entry["to"] in lock_installed:
                        new_installed[entry["to"]] = lock_installed[entry["to"]]
                needs_update = True
                continue

            new_sources[source_id] = {"repo": repo, "ref": ref, "commit": commit}
            previous_commit = lock_sources.get(source_id, {}).get("commit")
            commit_changed = previous_commit != commit

            # 本地现状：目录在不在、内容有没有被手改
            current: dict[str, str | None] = {}
            for entry in entries:
                target = REGISTRY_DIR / entry["to"]
                current[entry["to"]] = digest_dir(target) if (target / "SKILL.md").is_file() else None
            local_ok = all(
                current[entry["to"]] is not None
                and current[entry["to"]] == lock_installed.get(entry["to"], {}).get("digest")
                for entry in entries
            )

            if not commit_changed and local_ok:
                log(f"✓ {source_id}: 已是最新 ({commit[:8]})")
                for entry in entries:
                    new_installed[entry["to"]] = lock_installed[entry["to"]]
                continue

            reasons = []
            if commit_changed:
                reasons.append(f"上游更新 {str(previous_commit)[:8]} → {commit[:8]}")
            if not local_ok:
                reasons.append("本地目录缺失或被改动")
            needs_update = True

            if args.check:
                log(f"⚠ {source_id}: {'；'.join(reasons)}")
                for entry in entries:
                    new_installed[entry["to"]] = lock_installed.get(entry["to"], {})
                continue

            log(f"↓ {source_id}: {'；'.join(reasons)}")
            checkout = workdir / source_id
            subdirs = sorted({f"{skills_dir}/{entry['skill']}" for entry in entries})
            clone_sparse(repo, ref, subdirs, checkout)

            for entry in entries:
                source_dir = checkout / skills_dir / entry["skill"]
                if not (source_dir / "SKILL.md").is_file():
                    log(f"  ✗ {entry['skill']}: 上游没有 SKILL.md，已跳过")
                    continue
                target = REGISTRY_DIR / entry["to"]
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(source_dir, target, ignore=IGNORE)
                new_installed[entry["to"]] = {
                    "from": source_id,
                    "skill": entry["skill"],
                    "digest": digest_dir(target),
                }
                touched.append(entry["to"])
                log(f"  + {entry['to']}")

        # 清单里已经删掉的技能，目录也一并清掉，让 registry 始终等于清单
        wanted = {entry["to"] for entry in install}
        for stale_path in [path for path in lock_installed if path not in wanted]:
            stale_dir = REGISTRY_DIR / stale_path
            if args.check:
                log(f"⚠ 已从清单移除：{stale_path}")
                needs_update = True
                continue
            if stale_dir.exists():
                shutil.rmtree(stale_dir)
                log(f"  - {stale_path}（已从清单移除）")
            touched.append(stale_path)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if args.check:
        if needs_update:
            log("\n发现上游更新或本地改动。运行 python3 tools/sync_skills.py 进行同步。")
            return 1
        log("\n全部已是最新。")
        return 0

    LOCK_FILE.write_text(
        json.dumps(
            {
                "generatedBy": "tools/sync_skills.py",
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
