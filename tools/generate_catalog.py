#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成全量技能目录 CATALOG.md。
对齐 antfu/skills-pack 风格，按类别组织表格，自动为外部引入技能标注源链接（Credit），本地技能不带外部链接。
"""

import json
import re
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
REGISTRY_DIR = REPO_ROOT / "skills-router" / "registry"
SOURCES_FILE = TOOLS_DIR / "sources.json"
LOCK_FILE = TOOLS_DIR / "sources.lock.json"
CATALOG_FILE = REPO_ROOT / "CATALOG.md"


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


def main():
    sources_data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    lock_data = json.loads(LOCK_FILE.read_text(encoding="utf-8")) if LOCK_FILE.is_file() else {}

    installed = lock_data.get("installed", {})
    sources = sources_data.get("sources", {})

    categories = {
        "Core & Routing (核心路由)": [],
        "Browser & Automation (浏览器自动化)": [],
        "Frontend Development (前端开发 / Vue 生态)": [],
        "Office & Collaboration (办公协同 / 飞书套件)": [],
        "Workflow & Engineering (工作流与工程)": [],
        "Other (其他)": [],
    }

    # 1. 核心路由（本地自建）
    router_file = REPO_ROOT / "skills-router" / "SKILL.md"
    r_name, r_desc = parse_skill_meta(router_file)
    categories["Core & Routing (核心路由)"].append({
        "name": r_name,
        "desc": r_desc,
        "skill_link": None,
        "source_link": None,
        "source_name": "Local（自建）",
    })

    # 2. 遍历 registry
    for p in sorted(REGISTRY_DIR.rglob("SKILL.md")):
        rel_path = p.parent.relative_to(REGISTRY_DIR).as_posix()
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
            "desc": desc,
            "skill_link": skill_url,
            "source_link": source_link,
            "source_name": source_name,
        }

        if rel_path.startswith("dev/agent-browser"):
            categories["Browser & Automation (浏览器自动化)"].append(entry)
        elif rel_path.startswith("dev/frontend"):
            categories["Frontend Development (前端开发 / Vue 生态)"].append(entry)
        elif rel_path.startswith("office/lark"):
            categories["Office & Collaboration (办公协同 / 飞书套件)"].append(entry)
        elif rel_path.startswith("workflow/"):
            categories["Workflow & Engineering (工作流与工程)"].append(entry)
        else:
            categories["Other (其他)"].append(entry)

    out = [
        "# Skills Catalog\n",
        "本仓库已收纳的完整技能索引目录。通过单一入口 `skills-router` 渐进式披露，避免平铺污染 Agent 上下文。\n",
        "- **外部引入技能**：均提供指向原仓库和原始 `SKILL.md` 的链接以标明版权与来源（Credit）。",
        "- **本地自建技能**：标记为 `Local（自建）`，无外部链接。\n",
    ]

    total_count = 0
    for cat, items in categories.items():
        if not items:
            continue
        total_count += len(items)
        out.append(f"## {cat}\n")
        out.append("| 技能 (Skill) | 简介 (Description) | 来源 (Source) |")
        out.append("| --- | --- | --- |")
        for item in items:
            # 技能名与链接
            if item["skill_link"]:
                skill_col = f"[{item['name']}]({item['skill_link']})"
            else:
                skill_col = f"**{item['name']}**"

            # 描述清洗
            desc_clean = item["desc"].replace("|", "\\|").replace("\n", " ").strip()
            if len(desc_clean) > 160:
                desc_clean = desc_clean[:157] + "..."

            # 来源链接
            if item["source_link"]:
                source_col = f"[{item['source_name']}]({item['source_link']})"
            else:
                source_col = item["source_name"]

            out.append(f"| {skill_col} | {desc_clean} | {source_col} |")
        out.append("")

    CATALOG_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"✓ 已生成 {CATALOG_FILE.name}，收录 {total_count} 个技能。")


if __name__ == "__main__":
    main()
