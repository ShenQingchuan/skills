#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = REPO_ROOT / "bin"
ROUTER_SCRIPTS_DIR = REPO_ROOT / "skills-router" / "scripts"
for directory in (BIN_DIR, ROUTER_SCRIPTS_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import list_skills
import search_skills
from skill_boss_profiles import Profile


def write_skill(skill_dir: Path, name: str, description: str | None = None) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description or name + ' test skill'}\n---\n",
        encoding="utf-8",
    )


class SkillSearchTests(unittest.TestCase):
    def test_multiple_keywords_prioritize_match_count_then_field_weight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Profile("default", Path(tmp))
            write_skill(
                profile.registry_dir / "dev/frontend/vue-testing",
                "vue-testing",
                "Vue component testing guide",
            )
            write_skill(profile.registry_dir / "dev/frontend/vue", "vue", "Vue framework")
            write_skill(profile.registry_dir / "dev/testing/vitest", "vitest", "Testing runner")
            write_skill(profile.registry_dir / "writing/docs", "docs", "Writing documents")

            matches = search_skills.rank_skills(
                list_skills.collect_tree([profile]), "vue testing"
            )

            self.assertEqual(
                [node["meta"]["name"] for node in matches],
                ["vue-testing", "vue", "vitest"],
            )

    def test_search_includes_full_description_and_category_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Profile("default", Path(tmp))
            profile.manifest_file.write_text(
                json.dumps({"categories": {"office/lark": "飞书 审批"}}), encoding="utf-8"
            )
            write_skill(profile.registry_dir / "office/lark/workflow", "workflow", "流程操作")
            hidden_keyword = "罕见关键词"
            write_skill(
                profile.registry_dir / "writing/long",
                "long",
                "很长" * 80 + hidden_keyword,
            )

            tree = list_skills.collect_tree([profile])

            self.assertEqual(
                search_skills.rank_skills(tree, "飞书 审批")[0]["meta"]["name"],
                "workflow",
            )
            self.assertEqual(
                search_skills.rank_skills(tree, hidden_keyword)[0]["meta"]["name"],
                "long",
            )

    def test_keywords_are_case_insensitive_and_deduplicated(self) -> None:
        self.assertEqual(search_skills.parse_keywords(" Vue  vue TESTING "), ["vue", "testing"])
        with self.assertRaisesRegex(ValueError, "请提供搜索关键词"):
            search_skills.parse_keywords("  \n ")

    def test_unmatched_keywords_do_not_produce_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Profile("default", Path(tmp))
            write_skill(profile.registry_dir / "dev/vue", "vue")
            tree = list_skills.collect_tree([profile])
            self.assertEqual(search_skills.rank_skills(tree, "不存在的能力"), [])

    def test_result_output_uses_entry_path_as_identity(self) -> None:
        node = {
            "meta": {"name": "vue-testing", "desc": "Vue testing guide " + "details " * 20},
            "rel_path": Path("dev/frontend/vue-testing"),
            "path": Path("/registry/.synced/dev/frontend/vue-testing"),
        }

        output = "\n".join(search_skills.render_results([node], limit=5))

        self.assertTrue(output.startswith("🔎 1 个匹配技能"))
        self.assertIn(
            "1. 🎯 /registry/.synced/dev/frontend/vue-testing/SKILL.md\n   Vue testing guide",
            output,
        )
        self.assertNotIn("1. vue-testing -", output)
        self.assertNotIn("[dev/frontend/vue-testing]", output)
        self.assertNotIn("入口:", output)
        self.assertTrue(output.endswith("…"))


if __name__ == "__main__":
    unittest.main()
