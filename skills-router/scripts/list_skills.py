#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skills-router 技能树探测脚本
扫描 registry/ 目录，将已安装的技能及其描述以 Agent 友好的树状形式展示。
不依赖任何第三方库（仅使用 Python 原生标准库）。
"""

import re
import sys
from pathlib import Path

# 描述过长会把技能树撑爆，截断到一句话的规模
MAX_DESC = 110
# 目录内技能超过该数量时默认折叠（可通过参数单独查看子路径）
FOLD_THRESHOLD = 10


def shorten(text: str, limit: int = MAX_DESC) -> str:
    """压成一行的短语，超长就截断。"""
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def parse_skill_meta(skill_dir: Path) -> dict:
    """从 skill 目录下的 SKILL.md 解析名称与描述"""
    skill_file = skill_dir / "SKILL.md"
    name = skill_dir.name
    desc = "（无描述）"

    if not skill_file.is_file():
        return {"name": name, "desc": desc}

    try:
        content = skill_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"name": name, "desc": desc}

    # 尝试解析 YAML frontmatter（--- ... ---）
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        # 提取 name
        name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip("\"'")
        # 提取 description（支持多行、单行、以及 YAML 折叠标量 > 或 |）
        desc_block_match = re.search(r"^description:\s*([>|]?)\s*\n((?:(?:[ \t]+[^\n]*|\s*)\n)+)", fm_text, re.MULTILINE)
        if desc_block_match and desc_block_match.group(2).strip():
            block_lines = [line.strip() for line in desc_block_match.group(2).splitlines() if line.strip()]
            desc = " ".join(block_lines)
        else:
            desc_match = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
            if desc_match:
                desc = desc_match.group(1).strip().strip("\"'")
                desc = desc.split("\n")[0].strip()
    else:
        # 没有 frontmatter，尝试找第一个标题与第一段正文
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            if line.startswith("#"):
                name = line.lstrip("#").strip()
            elif desc == "（无描述）":
                desc = line
                break

    return {"name": name, "desc": desc}


def scan_registry(base_dir: Path):
    """
    扫描目录树：
    - 若目录内包含 SKILL.md，则视为叶子节点（一个完整的 Skill 单元），停止向其内部深入（如 scripts/, references/ 等内部资产）。
    - 若目录内不含 SKILL.md，则视为分类文件夹，继续向下递归。
    """
    if not base_dir.exists() or not base_dir.is_dir():
        return {}

    items = {}
    for entry in sorted(base_dir.iterdir(), key=lambda x: (x.is_file(), x.name)):
        # 忽略隐藏目录与临时环境
        if entry.name.startswith(".") or entry.name in {"__pycache__", "node_modules", "venv", ".venv"}:
            continue

        if entry.is_dir():
            # 判断是否是 skill 单元
            if (entry / "SKILL.md").is_file():
                meta = parse_skill_meta(entry)
                items[entry.name] = {
                    "is_skill": True,
                    "path": entry,
                    "meta": meta,
                }
            else:
                # 分类目录，继续递归
                sub_items = scan_registry(entry)
                items[entry.name] = {
                    "is_skill": False,
                    "path": entry,
                    "children": sub_items,
                }
    return items


def count_skills(node_dict: dict) -> int:
    """递归统计某个节点树下包含的所有 Skill 数量"""
    total = 0
    for node in node_dict.values():
        if node["is_skill"]:
            total += 1
        else:
            total += count_skills(node["children"])
    return total


def render_tree(
    node_dict: dict,
    prefix: str = "",
    base_dir: Path = None,
    registry_dir: Path = None,
    script_display: str = "list_skills.py",
    is_root_level: bool = True,
) -> list[str]:
    """渲染为缩进树形文本，并在子目录技能过多时自动折叠"""
    lines = []
    keys = list(node_dict.keys())
    total = len(keys)

    for i, key in enumerate(keys):
        is_last = (i == total - 1)
        connector = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")
        node = node_dict[key]

        if node["is_skill"]:
            meta = node["meta"]
            rel_path = node["path"].relative_to(base_dir) if base_dir else node["path"]
            line = f"{prefix}{connector}🎯 {meta['name']} - {shorten(meta['desc'])}"
            line += f" (入口: {rel_path}/SKILL.md)"
            lines.append(line)
        else:
            # 这是一个分类目录
            children = node["children"]
            if not children:
                # 空目录
                lines.append(f"{prefix}{connector}📂 {key}/ （空）")
            else:
                direct_child_count = len(children)
                # 只有当前层级的“直接子节点”数量超过阈值时才折叠
                if direct_child_count > FOLD_THRESHOLD:
                    rel_to_reg = node["path"].relative_to(registry_dir) if registry_dir else key
                    lines.append(
                        f"{prefix}{connector}📂 {key}/ （{direct_child_count} 项已折叠 → 请单独展开查阅 {rel_to_reg}）"
                    )
                else:
                    lines.append(f"{prefix}{connector}📂 {key}/")
                    lines.extend(
                        render_tree(
                            children,
                            prefix=child_prefix,
                            base_dir=base_dir,
                            registry_dir=registry_dir,
                            script_display=script_display,
                            is_root_level=False,
                        )
                    )

    return lines


def main():
    script_path = Path(__file__).resolve()
    # 结构：skills-router/scripts/list_skills.py -> router 目录为父级的父级
    router_dir = script_path.parent.parent
    registry_dir = (router_dir / "registry").resolve()

    # 尝试生成相对直观的脚本调用命令名
    try:
        script_display = str(script_path.relative_to(Path.cwd()))
    except Exception:
        script_display = script_path.name

    # 处理用户指定的子路径参数
    target_dir = registry_dir
    sub_title = ""
    if len(sys.argv) > 1 and sys.argv[1].strip():
        arg_path = sys.argv[1].strip()
        candidate = (registry_dir / arg_path).resolve()
        if not candidate.exists():
            # 也允许用户传入绝对路径或相对于当前工作区的路径
            candidate = Path(arg_path).resolve()

        if candidate.exists() and candidate.is_dir():
            target_dir = candidate
            try:
                rel = target_dir.relative_to(registry_dir)
                sub_title = f" [子目录视图: {rel}]"
            except ValueError:
                sub_title = f" [视图: {target_dir}]"
        else:
            print(f"❌ 指定路径不存在或非目录: {arg_path}")
            sys.exit(1)

    print(f"📦 skills-router（技能路由中心根目录: {registry_dir}{sub_title}）")

    if not target_dir.exists():
        print(f"  └── 📂 {target_dir.name}/ （目录尚不存在）")
        return

    tree = scan_registry(target_dir)
    if not tree:
        print(f"  └── 📂 {target_dir.name}/ （当前未安装任何技能）")
        return

    output_lines = render_tree(
        tree,
        prefix="  ",
        base_dir=target_dir,
        registry_dir=registry_dir,
        script_display=script_display,
        is_root_level=True,
    )
    for line in output_lines:
        print(line)


if __name__ == "__main__":
    main()
