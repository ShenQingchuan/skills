#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = REPO_ROOT / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from skill_boss_profiles import Profile, load_profiles
from sync_skills import sync_profile

LIST_SCRIPT = REPO_ROOT / "skills-router" / "scripts" / "list_skills.py"
SPEC = importlib.util.spec_from_file_location("list_skills", LIST_SCRIPT)
list_skills = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(list_skills)


def write_skill(skill_dir: Path, name: str) -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {name} test skill\n---\n\n# {name}\n",
        encoding="utf-8",
    )


class ProfileConfigTests(unittest.TestCase):
    def test_loads_default_and_active_profiles_with_same_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "config.json").write_text(
                json.dumps({"activeProfiles": ["company", "company"]}), encoding="utf-8"
            )
            profiles = load_profiles(root)

            self.assertEqual([profile.name for profile in profiles], ["default", "company"])
            company = profiles[1]
            self.assertEqual(company.manifest_file, root / "profiles" / "company" / "sources.json")
            self.assertEqual(company.lock_file, root / "profiles" / "company" / "sources.lock.json")
            self.assertEqual(company.registry_dir, root / "profiles" / "company" / "registry")
            self.assertEqual(company.synced_dir, company.registry_dir / ".synced")

    def test_missing_config_means_default_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([p.name for p in load_profiles(Path(tmp))], ["default"])

    def test_rejects_profile_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.json").write_text(
                json.dumps({"activeProfiles": ["../outside"]}), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                load_profiles(root)


class RegistryTreeTests(unittest.TestCase):
    def test_parses_folded_yaml_description_with_chomp_indicator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "demo"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: >-\n  第一行描述\n  第二行描述\n---\n",
                encoding="utf-8",
            )
            meta = list_skills.parse_skill_meta(skill_dir)
            self.assertEqual(meta["desc"], "第一行描述 第二行描述")

    def test_merges_default_sources_and_namespaces_private_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            default = Profile("default", root)
            company = Profile("company", root / "profiles" / "company")
            write_skill(default.registry_dir / "dev" / "frontend" / "manual", "manual")
            write_skill(default.synced_dir / "dev" / "frontend" / "remote", "remote")
            write_skill(company.registry_dir / "skills" / "private", "private")

            tree = list_skills.collect_tree([default, company])
            output = "\n".join(list_skills.render_tree(tree))

            self.assertIn("🎯 manual", output)
            self.assertIn("🎯 remote", output)
            self.assertIn("🎯 private", output)
            self.assertIn("📂 company/", output)
            self.assertIn("入口: dev/frontend/remote/SKILL.md", output)
            self.assertIn("入口: company/private/SKILL.md", output)
            self.assertNotIn(".synced", output)

    def test_rejects_duplicate_logical_skill_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Profile("default", Path(tmp))
            write_skill(profile.registry_dir / "dev" / "demo", "manual")
            write_skill(profile.synced_dir / "dev" / "demo", "remote")
            with self.assertRaisesRegex(ValueError, "dev/demo"):
                list_skills.collect_tree([profile])


class SyncProfileTests(unittest.TestCase):
    def test_sync_writes_only_synced_registry_and_profile_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            upstream = root / "upstream"
            write_skill(upstream / "skills" / "demo", "demo")
            subprocess.run(["git", "init", "--quiet", "--initial-branch=main", str(upstream)], check=True)
            subprocess.run(["git", "-C", str(upstream), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(upstream), "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", str(upstream), "add", "."], check=True)
            subprocess.run(["git", "-C", str(upstream), "commit", "--quiet", "-m", "test"], check=True)

            profile = Profile("company", root / "profiles" / "company")
            profile.root_dir.mkdir(parents=True)
            profile.manifest_file.write_text(
                json.dumps(
                    {
                        "sources": {
                            "local": {"repo": str(upstream), "ref": "main", "skillsDir": "skills"}
                        },
                        "install": [{"skill": "demo", "from": "local", "to": "dev/demo"}],
                    }
                ),
                encoding="utf-8",
            )
            write_skill(profile.registry_dir / "workflow" / "manual", "manual")
            gitignore = root / ".gitignore"
            original_gitignore = "/profiles/\n/registry/.synced/\n"
            gitignore.write_text(original_gitignore, encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                needs_update = sync_profile(profile)
                self.assertTrue(needs_update)
                self.assertFalse(sync_profile(profile, check=True))

            downloaded = profile.synced_dir / "dev" / "demo" / "SKILL.md"
            self.assertTrue(downloaded.is_file())
            self.assertTrue(profile.lock_file.is_file())
            self.assertTrue((profile.registry_dir / "workflow" / "manual" / "SKILL.md").is_file())
            self.assertEqual(gitignore.read_text(encoding="utf-8"), original_gitignore)

            downloaded.write_text("local change", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(sync_profile(profile, check=True))


if __name__ == "__main__":
    unittest.main()
