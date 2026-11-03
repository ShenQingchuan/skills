#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描默认与已启用 Profile 的 registry，并合并成一棵逻辑技能树。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
BIN_DIR = REPO_ROOT / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from skill_boss_profiles import Profile, load_profiles

MAX_DESC = 110
FOLD_THRESHOLD = 10


def shorten(text: str, limit: int = MAX_DESC) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def parse_skill_meta(skill_dir: Path) -> dict:
    """从 SKILL.md 解析名称与描述；分类完全由目录位置决定。"""
    skill_file = skill_dir / "SKILL.md"
    name = skill_dir.name
    desc = "（无描述）"

    try:
        content = skill_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"name": name, "desc": desc}

    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip("\"'")
        desc_block_match = re.search(
            r"^description:[ \t]*([>|][+-]?)?[ \t]*\n((?:[ \t]+[^\n]*(?:\n|$)|[ \t]*\n)+)",
            fm_text,
            re.MULTILINE,
        )
        if desc_block_match and desc_block_match.group(2).strip():
            desc = " ".join(
                line.strip() for line in desc_block_match.group(2).splitlines() if line.strip()
            )
        else:
            desc_match = re.search(r"^description:[ \t]*(.+)$", fm_text, re.MULTILINE)
            if desc_match:
                desc = desc_match.group(1).strip().strip("\"'").split("\n")[0].strip()
    else:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if line.startswith("#"):
                name = line.lstrip("#").strip()
            elif desc == "（无描述）":
                desc = line
                break

    return {"name": name, "desc": desc}


def scan_registry(base_dir: Path, logical_prefix: Path = Path()) -> dict:
    """遇到一个 SKILL.md 就停止深入；rel_path 始终是不含存储前缀的逻辑路径。"""
    if not base_dir.is_dir():
        return {}

    items = {}
    for entry in sorted(base_dir.iterdir(), key=lambda path: (path.is_file(), path.name)):
        if entry.name.startswith(".") or entry.name in {"__pycache__", "node_modules", "venv", ".venv"}:
            continue
        if not entry.is_dir():
            continue

        rel_path = logical_prefix / entry.name
        if (entry / "SKILL.md").is_file():
            items[entry.name] = {
                "is_skill": True,
                "path": entry,
                "rel_path": rel_path,
                "meta": parse_skill_meta(entry),
            }
        else:
            items[entry.name] = {
                "is_skill": False,
                "path": entry,
                "rel_path": rel_path,
                "children": scan_registry(entry, rel_path),
            }
    return items


def merge_trees(target: dict, incoming: dict) -> None:
    """合并分类；同一逻辑技能只能有一个实际来源。"""
    for key, node in incoming.items():
        if key not in target:
            target[key] = node
            continue

        current = target[key]
        if current["is_skill"] or node["is_skill"]:
            raise ValueError(f"技能逻辑路径冲突：{node['rel_path']}")
        merge_trees(current["children"], node["children"])


def collect_tree(profiles: list[Profile]) -> dict:
    """默认 Profile 位于根目录；私有 Profile 以名称作为顶层命名空间。"""
    tree: dict = {}
    for profile in profiles:
        prefix = Path() if profile.name == "default" else Path(profile.name)
        profile_tree: dict = {}

        unmanaged_tree = scan_registry(profile.registry_dir, prefix)
        native_skills = unmanaged_tree.get("skills")
        if native_skills and not native_skills["is_skill"]:
            # skills/ 用于存放未分类技能，不参与逻辑分类。
            del unmanaged_tree["skills"]
            merge_trees(profile_tree, scan_registry(profile.registry_dir / "skills", prefix))
        merge_trees(profile_tree, unmanaged_tree)
        merge_trees(profile_tree, scan_registry(profile.synced_dir, prefix))

        if profile.name == "default":
            merge_trees(tree, profile_tree)
        elif profile_tree:
            merge_trees(
                tree,
                {
                    profile.name: {
                        "is_skill": False,
                        "path": profile.registry_dir,
                        "rel_path": Path(profile.name),
                        "children": profile_tree,
                    }
                },
            )
    return tree


def select_category(tree: dict, raw_path: str) -> tuple[dict, Path]:
    normalized_input = raw_path.strip().replace("\\", "/")
    normalized = normalized_input.strip("/")
    if not normalized:
        if normalized_input.startswith("/"):
            raise ValueError(f"无效的技能分类路径：{raw_path}")
        return tree, Path()

    parts = normalized.split("/")
    if normalized_input.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"无效的技能分类路径：{raw_path}")

    current = tree
    for part in parts:
        node = current.get(part)
        if not node or node["is_skill"]:
            raise ValueError(f"指定分类不存在：{normalized}")
        current = node["children"]
    return current, Path(*parts)


def render_tree(node_dict: dict, prefix: str = "", strip_prefix: Path = Path()) -> list[str]:
    lines = []
    keys = sorted(node_dict)
    for index, key in enumerate(keys):
        is_last = index == len(keys) - 1
        connector = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")
        node = node_dict[key]

        if node["is_skill"]:
            rel_path = node["rel_path"]
            if strip_prefix.parts:
                rel_path = rel_path.relative_to(strip_prefix)
            meta = node["meta"]
            line = f"{prefix}{connector}🎯 {meta['name']} - {shorten(meta['desc'])}"
            lines.append(f"{line} (入口: {rel_path}/SKILL.md)")
            continue

        children = node["children"]
        if not children:
            lines.append(f"{prefix}{connector}📂 {key}/ （空）")
        elif len(children) > FOLD_THRESHOLD:
            lines.append(
                f"{prefix}{connector}📂 {key}/ （{len(children)} 项已折叠 → "
                f"请单独展开查阅 {node['rel_path']}）"
            )
        else:
            lines.append(f"{prefix}{connector}📂 {key}/")
            lines.extend(render_tree(children, child_prefix, strip_prefix))
    return lines


def skill_directory_completions(profiles: list[Profile], prefix: str) -> list[str]:
    """为 Shell 补全提供与技能树一致的合并分类目录。"""
    parent, name_prefix = prefix.rsplit("/", 1) if "/" in prefix else ("", prefix)
    tree, _ = select_category(collect_tree(profiles), parent)
    parent_prefix = f"{parent}/" if parent else ""
    return [
        f"{parent_prefix}{key}/"
        for key in sorted(tree)
        if not tree[key]["is_skill"] and key.startswith(name_prefix)
    ]


def main() -> int:
    try:
        profiles = load_profiles(REPO_ROOT)
        tree = collect_tree(profiles)
        arg_path = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() else ""
        tree, selected_path = select_category(tree, arg_path)
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    active_names = [profile.name for profile in profiles if profile.name != "default"]
    active_text = f"；已启用 Profile: {', '.join(active_names)}" if active_names else ""
    sub_title = f" [子目录视图: {selected_path}]" if selected_path.parts else ""
    registry_dir = REPO_ROOT / "registry"
    print(f"📦 skills-router（技能路由中心根目录: {registry_dir}{active_text}）{sub_title}")

    if not tree:
        print("  └── （当前未安装任何技能）")
        return 0

    for line in render_tree(tree, prefix="  ", strip_prefix=selected_path):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
