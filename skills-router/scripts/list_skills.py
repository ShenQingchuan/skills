#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描默认与已启用 Profile 的 registry，并合并成一棵逻辑技能树。"""

from __future__ import annotations

import json
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


def category_key(raw_path: str, source: str) -> str:
    """分类说明使用与 install.to 相同的逻辑目录，不含 Profile 名。"""
    if not isinstance(raw_path, str):
        raise ValueError(f"{source} 的 categories 必须是「目录路径 → 一句话」")
    text = raw_path.strip().replace("\\", "/")
    normalized = text.strip("/")
    parts = normalized.split("/") if normalized else []
    if text.startswith("/") or not normalized or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{source} 中的分类路径无效：{raw_path}")
    return normalized


def load_category_descriptions(profiles: list[Profile]) -> dict[str, str]:
    """读取各 Profile 清单里的分类说明。键是技能树上的逻辑路径。"""
    descriptions: dict[str, str] = {}
    for profile in profiles:
        manifest_file = profile.manifest_file
        if not manifest_file.is_file():
            continue
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"技能清单不是有效 JSON：{manifest_file}\n{exc}") from exc
        if not isinstance(manifest, dict):
            raise ValueError(f"技能清单必须是对象：{manifest_file}")

        raw = manifest.get("categories", {})
        if not isinstance(raw, dict):
            raise ValueError(f"{manifest_file} 的 categories 必须是对象")

        prefix = "" if profile.name == "default" else f"{profile.name}/"
        for path, desc in raw.items():
            if not isinstance(desc, str) or not desc.strip():
                raise ValueError(f"{manifest_file} 的 categories 必须是「目录路径 → 一句话」")
            key = prefix + category_key(path, str(manifest_file))
            descriptions[key] = " ".join(desc.split())
    return descriptions


def stamp_category_descriptions(node_dict: dict, descriptions: dict[str, str]) -> None:
    for node in node_dict.values():
        if node["is_skill"]:
            continue
        desc = descriptions.get(node["rel_path"].as_posix())
        if desc:
            node["desc"] = desc
        stamp_category_descriptions(node["children"], descriptions)


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


def scan_storage(storage_dir: Path, logical_prefix: Path) -> dict:
    """扫描一种存储来源，并将 skills/ 中的未分类技能提升到逻辑根目录。"""
    tree = scan_registry(storage_dir, logical_prefix)
    uncategorized = tree.get("skills")
    if uncategorized and not uncategorized["is_skill"]:
        del tree["skills"]
        merge_trees(tree, scan_registry(storage_dir / "skills", logical_prefix))
    return tree


def collect_tree(profiles: list[Profile]) -> dict:
    """手写与下载存储分离，逻辑分类合并；私有 Profile 使用顶层命名空间。"""
    tree: dict = {}
    for profile in profiles:
        prefix = Path() if profile.name == "default" else Path(profile.name)
        profile_tree: dict = {}
        merge_trees(profile_tree, scan_storage(profile.registry_dir, prefix))
        merge_trees(profile_tree, scan_storage(profile.synced_dir, prefix))

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
    stamp_category_descriptions(tree, load_category_descriptions(profiles))
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


def count_skills(node_dict: dict) -> int:
    """统计整棵子树的技能数，供概览展示分类体量。"""
    return sum(
        1 if node["is_skill"] else count_skills(node["children"])
        for node in node_dict.values()
    )


def render_skill(node: dict, prefix: str, connector: str) -> str:
    meta = node["meta"]
    skill_file = node["path"] / "SKILL.md"
    line = f"{prefix}{connector}🎯 {meta['name']} - {shorten(meta['desc'])}"
    return f"{line} (入口: {skill_file})"


def render_overview(node_dict: dict, prefix: str = "") -> list[str]:
    """根视图只披露第一层；分类显示递归技能数，不泄露后代细节。"""
    lines = []
    keys = sorted(node_dict)
    for index, key in enumerate(keys):
        connector = "└── " if index == len(keys) - 1 else "├── "
        node = node_dict[key]
        if node["is_skill"]:
            lines.append(render_skill(node, prefix, connector))
            continue

        children = node["children"]
        count = count_skills(children)
        label = f"{prefix}{connector}📂 {key}/"
        label += "（空）" if not children else f"（{count} 个技能）"
        desc = node.get("desc")
        if desc:
            label += f" - {shorten(desc)}"
        lines.append(label)
    return lines


def render_tree(node_dict: dict, prefix: str = "") -> list[str]:
    """完整展开指定分类下的所有技能，不按数量折叠。"""
    lines = []
    keys = sorted(node_dict)
    for index, key in enumerate(keys):
        is_last = index == len(keys) - 1
        connector = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")
        node = node_dict[key]

        if node["is_skill"]:
            lines.append(render_skill(node, prefix, connector))
            continue

        children = node["children"]
        label = f"{prefix}{connector}📂 {key}/"
        desc = node.get("desc")
        if desc:
            label += f" - {shorten(desc)}"
        if not children:
            label += "（空）"
        lines.append(label)
        lines.extend(render_tree(children, child_prefix))
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

    if selected_path.parts:
        print(f"📦 skills-router [子目录视图: {selected_path}]")
    else:
        active_names = [profile.name for profile in profiles if profile.name != "default"]
        active_text = f"；已启用 Profile: {', '.join(active_names)}" if active_names else ""
        print(f"📦 skills-router（共 {count_skills(tree)} 个技能{active_text}）")

    if not tree:
        print("  └── （当前未安装任何技能）")
        return 0

    lines = (
        render_tree(tree, prefix="  ")
        if selected_path.parts
        else render_overview(tree, prefix="  ")
    )
    for line in lines:
        print(line)
    if not selected_path.parts:
        print('搜索：boss search-skills "<关键词>"；展开分类：boss list-skills <路径>')
    return 0


if __name__ == "__main__":
    sys.exit(main())
