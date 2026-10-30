#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成全量技能目录 CATALOG.md。
严格按照真实目录结构（dev/agent-friendly, dev/frontend, office/lark 等）分层组织，
自动为外部引入技能标注源链接（Credit），本地自建技能清晰归类，并在表格中呈现精准相对路径。
"""

import json
import re
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
REGISTRY_DIR = REPO_ROOT / "skills-router" / "registry"
SOURCES_FILE = REPO_ROOT / "sources.json"
LOCK_FILE = REPO_ROOT / "sources.lock.json"
CATALOG_FILE = REPO_ROOT / "CATALOG.md"

# 目录友好中文标注（若未登记则默认使用目录名自身）
CATEGORY_META = {
    "dev": "开发与智能体生态",
    "dev/agent-friendly": "本地自建 · 智能体规约",
    "dev/frontend": "前端开发",
    "dev/agent-browser": "浏览器自动化",
    "office": "办公与协同生态",
    "office/lark": "飞书全能力套件",
    "workflow": "工作流与决策",
    "writing": "写作与文档",
}


def parse_skill_meta(skill_file: Path) -> tuple[str, str]:
    """从 skill 文件中提取名称与描述（支持单行、多行以及 YAML > / | 折叠块）"""
    name = skill_file.parent.name
    desc = "（无描述）"
    if not skill_file.is_file():
        return name, desc

    content = skill_file.read_text(encoding="utf-8", errors="ignore")
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip("\"'")

        # 提取 description（支持多行缩进块与标量）
        desc_block_match = re.search(
            r"^description:\s*([>|]?)\s*\n((?:(?:[ \t]+[^\n]*|\s*)\n)+)",
            fm_text,
            re.MULTILINE,
        )
        if desc_block_match and desc_block_match.group(2).strip():
            block_lines = [
                line.strip()
                for line in desc_block_match.group(2).splitlines()
                if line.strip()
            ]
            desc = " ".join(block_lines)
        else:
            desc_match = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
            if desc_match:
                desc = desc_match.group(1).strip().strip("\"'")
                desc = desc.split("\n")[0].strip()
    return name, desc


def format_table_row(item: dict) -> str:
    """生成单行 Markdown 表格内容"""
    if item["skill_link"]:
        skill_col = f"[{item['name']}]({item['skill_link']})"
    else:
        skill_col = f"**{item['name']}**"

    path_col = f"`{item['path']}`"

    desc_clean = item["desc"].replace("|", "\\|").replace("\n", " ").strip()
    if len(desc_clean) > 160:
        desc_clean = desc_clean[:157] + "..."

    if item["source_link"]:
        source_col = f"[{item['source_name']}]({item['source_link']})"
    else:
        source_col = item["source_name"]

    return f"| {skill_col} | {path_col} | {desc_clean} | {source_col} |"


def main():
    sources_data = json.loads(SOURCES_FILE.read_text(encoding="utf-8")) if SOURCES_FILE.is_file() else {}
    lock_data = json.loads(LOCK_FILE.read_text(encoding="utf-8")) if LOCK_FILE.is_file() else {}

    installed = lock_data.get("installed", {})
    sources = sources_data.get("sources", {})

    # 1. 扫描 registry 下所有技能，按目录结构分类
    # 结构: { top_dir: { sub_dir: [skills...] } }
    catalog_tree: dict[str, dict[str, list[dict]]] = {}

    for p in sorted(REGISTRY_DIR.rglob("SKILL.md")):
        skill_dir = p.parent
        rel_path = skill_dir.relative_to(REGISTRY_DIR).as_posix()
        parts = rel_path.split("/")

        top_dir = parts[0]
        # 判断子分类目录
        if len(parts) == 1:
            sub_dir = top_dir
        elif len(parts) == 2:
            # 例如 dev/agent-browser 或 workflow/grilling
            # 如果父目录是独立技能目录（如 agent-browser），保留为 dev/agent-browser 细分
            if top_dir == "workflow":
                sub_dir = "workflow"
            else:
                sub_dir = f"{top_dir}/{parts[1]}"
        else:
            # 例如 dev/agent-friendly/create-rule -> sub_dir 是 dev/agent-friendly
            # office/lark/lark-approval -> sub_dir 是 office/lark
            sub_dir = f"{top_dir}/{parts[1]}"

        name, desc = parse_skill_meta(p)
        lock_info = installed.get(rel_path)

        if lock_info:
            source_id = lock_info["from"]
            upstream_skill = lock_info["skill"]
            source_cfg = sources.get(source_id, {})
            repo_url = source_cfg.get("repo", "")
            skills_dir = source_cfg.get("skillsDir", "skills")
            skill_url = f"{repo_url}/blob/HEAD/{skills_dir}/{upstream_skill}/SKILL.md"
            source_name = repo_url.replace("https://github.com/", "")
            source_link = repo_url
        else:
            skill_url = None
            source_link = None
            source_name = "Local（自建）"

        entry = {
            "name": name,
            "path": f"{rel_path}/",
            "desc": desc,
            "skill_link": skill_url,
            "source_link": source_link,
            "source_name": source_name,
        }

        if top_dir not in catalog_tree:
            catalog_tree[top_dir] = {}
        if sub_dir not in catalog_tree[top_dir]:
            catalog_tree[top_dir][sub_dir] = []
        catalog_tree[top_dir][sub_dir].append(entry)

    # 2. 组装 Markdown
    out = [
        "# Skills Catalog\n",
        "本仓库已收纳的完整技能索引目录。通过单一入口 `skills-router` 渐进式披露，避免平铺污染 Agent 上下文。\n",
        "- **外部引入技能**：均提供指向原仓库和原始 `SKILL.md` 的链接以标明版权与来源（Credit）。",
        "- **本地自建技能**：标记为 `Local（自建）`，受 Git 跟踪与保护。\n",
        "---",
    ]

    total_count = 0

    # 核心路由 (置顶)
    router_file = REPO_ROOT / "skills-router" / "SKILL.md"
    r_name, r_desc = parse_skill_meta(router_file)
    total_count += 1
    out.append("## 📦 核心路由 (skills-router/)\n")
    out.append("| 技能 (Skill) | 相对路径 (Path) | 简介 (Description) | 来源 (Source) |")
    out.append("| --- | --- | --- | --- |")
    out.append(format_table_row({
        "name": r_name,
        "path": "skills-router/",
        "desc": r_desc,
        "skill_link": None,
        "source_link": None,
        "source_name": "Local（自建）",
    }))
    out.append("")

    # 目录排序：按照预设推荐顺序（dev, office, workflow...），未预设的按字母排序
    order_pref = ["dev", "office", "workflow"]
    sorted_top = sorted(catalog_tree.keys(), key=lambda x: (order_pref.index(x) if x in order_pref else 99, x))

    for top in sorted_top:
        sub_groups = catalog_tree[top]
        top_label = CATEGORY_META.get(top, top)
        out.append(f"## 📂 {top}/ ({top_label})\n")

        # 排序子目录，把包含 agent-friendly（自建）的排在最前
        def sub_sort_key(sub_key: str):
            if "agent-friendly" in sub_key:
                return (0, sub_key)
            return (1, sub_key)

        sorted_subs = sorted(sub_groups.keys(), key=sub_sort_key)

        # 如果只有一个子分类且名字和顶层一样（如 workflow），直接平铺展示
        if len(sorted_subs) == 1 and sorted_subs[0] == top:
            items = sub_groups[top]
            total_count += len(items)
            out.append("| 技能 (Skill) | 相对路径 (Path) | 简介 (Description) | 来源 (Source) |")
            out.append("| --- | --- | --- | --- |")
            for item in items:
                out.append(format_table_row(item))
            out.append("")
        else:
            for sub in sorted_subs:
                items = sub_groups[sub]
                total_count += len(items)
                sub_label = CATEGORY_META.get(sub, sub)
                out.append(f"### 🎯 {sub}/ ({sub_label})\n")
                out.append("| 技能 (Skill) | 相对路径 (Path) | 简介 (Description) | 来源 (Source) |")
                out.append("| --- | --- | --- | --- |")
                for item in items:
                    out.append(format_table_row(item))
                out.append("")

    CATALOG_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"✓ 已生成 {CATALOG_FILE.name}，收录 {total_count} 个技能。")


if __name__ == "__main__":
    main()
