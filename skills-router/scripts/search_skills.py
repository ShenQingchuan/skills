#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按一个查询字符串中的多个关键词搜索全部已加载技能。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
BIN_DIR = REPO_ROOT / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from list_skills import collect_tree, shorten
from skill_boss_profiles import load_profiles


def parse_keywords(query: str) -> list[str]:
    """按空白拆分查询并去重，忽略大小写但保留原始关键词用于匹配。"""
    keywords = []
    seen = set()
    for keyword in query.split():
        normalized = keyword.casefold()
        if normalized not in seen:
            seen.add(normalized)
            keywords.append(normalized)
    if not keywords:
        raise ValueError("请提供搜索关键词，例如：boss search-skills \"vue testing\"")
    return keywords


def iter_skill_nodes(node_dict: dict, category_text: str = ""):
    """展开技能节点，并携带祖先分类说明作为搜索文本。"""
    for key in sorted(node_dict):
        node = node_dict[key]
        if node["is_skill"]:
            yield node, category_text
        else:
            child_category_text = " ".join(
                part for part in (category_text, node.get("desc", "")) if part
            )
            yield from iter_skill_nodes(node["children"], child_category_text)


def keyword_weight(keyword: str, node: dict, category_text: str) -> int:
    """取关键词在各字段中的最高权重；精确技能名最容易被选中。"""
    name = node["meta"]["name"].casefold()
    logical_path = node["rel_path"].as_posix().casefold()
    description = node["meta"]["desc"].casefold()
    if keyword == name:
        return 5
    if keyword in name:
        return 4
    if keyword in logical_path:
        return 3
    if keyword in description:
        return 2
    if keyword in category_text.casefold():
        return 1
    return 0


def rank_skills(tree: dict, query: str) -> list[dict]:
    """至少命中一个关键词即可入选；命中数优先，其次比较字段权重。"""
    keywords = parse_keywords(query)
    ranked = []
    for node, category_text in iter_skill_nodes(tree):
        weights = [keyword_weight(keyword, node, category_text) for keyword in keywords]
        matched_count = sum(weight > 0 for weight in weights)
        if matched_count:
            ranked.append((matched_count, sum(weights), node))

    ranked.sort(
        key=lambda item: (-item[0], -item[1], item[2]["rel_path"].as_posix())
    )
    return [node for _, _, node in ranked]


def render_results(matches: list[dict], limit: int) -> list[str]:
    """每个候选用绝对入口作为标识，只补充一段短描述。"""
    selected = matches[:limit]
    summary = f"🔎 {len(matches)} 个匹配技能"
    if len(selected) < len(matches):
        summary += f"，显示前 {len(selected)} 个"
    lines = [summary]
    for index, node in enumerate(selected, start=1):
        lines.append(f"{index}. 🎯 {node['path'] / 'SKILL.md'}")
        lines.append(f"   {shorten(node['meta']['desc'], 80)}")
    return lines


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("必须大于 0")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="搜索全部技能；查询字符串可包含多个以空白分隔的关键词。"
    )
    parser.add_argument("query", help='带引号的关键词字符串，例如 "vue testing"')
    parser.add_argument("--limit", type=positive_int, default=5, help="最多显示几条结果（默认 5）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        matches = rank_skills(collect_tree(load_profiles(REPO_ROOT)), args.query)
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    if not matches:
        print(f'未找到匹配技能："{args.query}"')
        print("可尝试减少关键词，或运行 boss list-skills 查看分类。")
        return 0

    for line in render_results(matches, args.limit):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
