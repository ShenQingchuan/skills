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
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
BIN_DIR = REPO_ROOT / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

import sync_fskillhub
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
            write_skill(company.synced_dir / "skills" / "downloaded", "downloaded")

            tree = list_skills.collect_tree([default, company])
            output = "\n".join(list_skills.render_tree(tree))

            self.assertIn("🎯 manual", output)
            self.assertIn("🎯 remote", output)
            self.assertIn("🎯 private", output)
            self.assertIn("🎯 downloaded", output)
            self.assertIn("📂 company/", output)
            self.assertIn(
                f"入口: {default.synced_dir / 'dev/frontend/remote/SKILL.md'}", output
            )
            self.assertIn(
                f"入口: {company.registry_dir / 'skills/private/SKILL.md'}", output
            )
            self.assertIn(
                f"入口: {company.synced_dir / 'skills/downloaded/SKILL.md'}", output
            )
            self.assertNotIn("📂 .synced/", output)
            self.assertNotIn("📂 skills/", output)

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

            initial_output = io.StringIO()
            with contextlib.redirect_stdout(initial_output):
                needs_update = sync_profile(profile)
                self.assertTrue(needs_update)
                self.assertFalse(sync_profile(profile, check=True))
            self.assertIn("↓ local: 尚未下载", initial_output.getvalue())

            downloaded = profile.synced_dir / "dev" / "demo" / "SKILL.md"
            self.assertTrue(downloaded.is_file())
            self.assertTrue(profile.lock_file.is_file())
            self.assertTrue((profile.registry_dir / "workflow" / "manual" / "SKILL.md").is_file())
            self.assertEqual(gitignore.read_text(encoding="utf-8"), original_gitignore)

            downloaded.write_text("local change", encoding="utf-8")
            modified_output = io.StringIO()
            with contextlib.redirect_stdout(modified_output):
                self.assertTrue(sync_profile(profile, check=True))
            self.assertIn("本地内容被修改，同步会覆盖修改", modified_output.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                sync_profile(profile)
            downloaded.unlink()
            missing_output = io.StringIO()
            with contextlib.redirect_stdout(missing_output):
                self.assertTrue(sync_profile(profile, check=True))
            self.assertIn("本地文件缺失，需要重新下载", missing_output.getvalue())

            with contextlib.redirect_stdout(io.StringIO()):
                sync_profile(profile)
            (upstream / "skills" / "demo" / "SKILL.md").write_text("upstream update", encoding="utf-8")
            subprocess.run(["git", "-C", str(upstream), "add", "."], check=True)
            subprocess.run(["git", "-C", str(upstream), "commit", "--quiet", "-m", "update"], check=True)
            update_output = io.StringIO()
            with contextlib.redirect_stdout(update_output):
                self.assertTrue(sync_profile(profile, check=True))
            self.assertIn("需要更新（上游版本", update_output.getvalue())


class FskillhubSyncTests(unittest.TestCase):
    def make_profile(self, root: Path, version: str | None = None) -> Profile:
        profile = Profile("company", root / "profiles" / "company")
        profile.root_dir.mkdir(parents=True)
        entry = {"skill": "team-infra@fservice-cli", "from": "futu", "to": "skills/fservice-cli"}
        if version:
            entry["version"] = version
        profile.manifest_file.write_text(
            json.dumps(
                {
                    "sources": {
                        "futu": {
                            "method": "fskillhub",
                            "tool": "@futu/fskillhub@latest",
                            "npmRegistry": "http://registry.npm.oa.com/",
                            "registry": "https://api-mcp.futuoa.com",
                        }
                    },
                    "install": [entry],
                }
            ),
            encoding="utf-8",
        )
        return profile

    def fake_run(self, commands: list[list[str]], remote: dict):
        def fake(command: list[str]) -> str:
            commands.append(command)
            workdir = Path(command[command.index("--workdir") + 1])
            slug = command[command.index("install") + 1]
            skill_dir = workdir / "skills" / slug.rsplit("@", 1)[-1]
            write_skill(skill_dir, "fservice-cli")
            (skill_dir / "extra.txt").write_text(remote["content"], encoding="utf-8")
            origin = skill_dir / ".fskillhub" / "origin.json"
            origin.parent.mkdir(parents=True)
            origin.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "registry": "https://api-mcp.futuoa.com",
                        "slug": slug,
                        "installedVersion": remote["version"],
                        "installedAt": 1000 + len(commands),
                    }
                ),
                encoding="utf-8",
            )
            return ""

        return fake

    def run_with_fake_hub(self, profile: Profile, commands: list[list[str]], remote: dict, **kwargs):
        with (
            patch.object(sync_fskillhub, "runtime_npx", return_value=Path("/mock/npx")),
            patch.object(sync_fskillhub, "run", side_effect=self.fake_run(commands, remote)),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            return sync_profile(profile, **kwargs)

    def test_syncs_declared_hub_skill_into_unified_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.make_profile(Path(tmp), version="3.14.0")
            commands: list[list[str]] = []
            remote = {"version": "3.14.0", "content": "payload"}

            self.assertTrue(self.run_with_fake_hub(profile, commands, remote))
            target = profile.synced_dir / "skills" / "fservice-cli"
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertFalse((target / ".fskillhub").exists())
            self.assertFalse((profile.synced_dir / ".fskillhub").exists())
            self.assertIn("--no-input", commands[0])
            self.assertEqual(commands[0][-2:], ["--version", "3.14.0"])

            lock = json.loads(profile.lock_file.read_text(encoding="utf-8"))
            record = lock["installed"]["skills/fservice-cli"]
            self.assertEqual(record["method"], "fskillhub")
            self.assertEqual(record["version"], "3.14.0")
            self.assertEqual(lock["sources"]["futu"]["registry"], "https://api-mcp.futuoa.com")

            # 工具生成不同的安装时间，也不会让相同技能内容失去幂等性。
            self.assertFalse(self.run_with_fake_hub(profile, commands, remote, check=True))
            remote["version"] = "3.15.0"
            self.assertTrue(self.run_with_fake_hub(profile, commands, remote, check=True))

    def test_check_downloads_only_to_temporary_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.make_profile(Path(tmp))
            commands: list[list[str]] = []
            remote = {"version": "3.14.0", "content": "payload"}

            self.assertTrue(self.run_with_fake_hub(profile, commands, remote, check=True))
            self.assertFalse((profile.synced_dir / "skills" / "fservice-cli").exists())
            self.assertFalse(profile.lock_file.exists())

    def test_download_failure_preserves_installed_skill_and_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.make_profile(Path(tmp))
            commands: list[list[str]] = []
            remote = {"version": "3.14.0", "content": "payload"}
            self.run_with_fake_hub(profile, commands, remote)
            target = profile.synced_dir / "skills" / "fservice-cli" / "SKILL.md"
            original_lock = profile.lock_file.read_bytes()

            with (
                patch.object(sync_fskillhub, "runtime_npx", return_value=Path("/mock/npx")),
                patch.object(sync_fskillhub, "run", side_effect=RuntimeError("registry unavailable")),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertTrue(sync_profile(profile))

            self.assertTrue(target.is_file())
            self.assertEqual(json.loads(profile.lock_file.read_text(encoding="utf-8"))["installed"],
                             json.loads(original_lock)["installed"])

    def test_rejects_unknown_download_method(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.make_profile(Path(tmp))
            manifest = json.loads(profile.manifest_file.read_text(encoding="utf-8"))
            manifest["sources"]["futu"]["method"] = "shell"
            profile.manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
            with (
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaisesRegex(ValueError, "不支持的下载方法"),
            ):
                sync_profile(profile)


if __name__ == "__main__":
    unittest.main()
