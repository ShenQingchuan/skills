#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import contextlib
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

import boss_services
from boss_service_state import ServiceRegistry


class FakeProcess:
    def __init__(self, pid: int = 4321):
        self.pid = pid
        self.terminated = False

    def poll(self):
        return None

    def terminate(self):
        self.terminated = True


class ServiceRegistryTests(unittest.TestCase):
    def test_records_are_persistent_and_isolated_by_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir = root / ".local"
            first_project = root / "first"
            second_project = root / "second"
            registry = ServiceRegistry(state_dir)
            registry.put("kanban", first_project, 5173, 101)
            registry.put("kanban", second_project, 5174, 102)

            reloaded = ServiceRegistry(state_dir)
            self.assertEqual(reloaded.get("kanban", first_project)["port"], 5173)
            self.assertEqual(reloaded.get("kanban", second_project)["port"], 5174)
            self.assertIsNone(reloaded.get("code", first_project))

            reloaded.remove("kanban", first_project)
            self.assertIsNone(reloaded.get("kanban", first_project))
            self.assertEqual(reloaded.get("kanban", second_project)["port"], 5174)

    def test_invalid_json_is_treated_as_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / ".local"
            state_dir.mkdir()
            (state_dir / "services.json").write_text("not json", encoding="utf-8")
            registry = ServiceRegistry(state_dir)
            self.assertIsNone(registry.get("kanban", Path(tmp)))


class ServiceCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = self.root / "project"
        self.kanban_dir = self.project / ".agents" / "kanban"
        self.kanban_dir.mkdir(parents=True)
        (self.kanban_dir / "kanban.html").write_text("kanban", encoding="utf-8")
        self.state_dir = self.root / ".local"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_kanban_reuses_the_record_for_the_same_project(self) -> None:
        process = FakeProcess()
        with (
            patch.object(boss_services, "SERVICE_STATE_DIR", self.state_dir),
            patch.object(boss_services, "get_bun_executable", return_value="bun"),
            patch.object(boss_services, "create_detached_process", return_value=process) as launch,
            patch.object(boss_services, "wait_for_service", return_value=True),
            patch.object(boss_services, "is_port_in_use", return_value=False),
            patch.object(boss_services, "is_process_alive", return_value=True),
            patch.object(boss_services, "is_http_ready", return_value=True),
        ):
            first_output = io.StringIO()
            second_output = io.StringIO()
            with contextlib.redirect_stdout(first_output):
                self.assertEqual(boss_services.cmd_kanban([str(self.project)]), 0)
            with contextlib.redirect_stdout(second_output):
                self.assertEqual(boss_services.cmd_kanban([str(self.project)]), 0)

        launch.assert_called_once()
        self.assertIn("后台启动", first_output.getvalue())
        self.assertIn("直接复用", second_output.getvalue())
        record = ServiceRegistry(self.state_dir).get("kanban", self.project)
        self.assertEqual(record["port"], 5173)
        self.assertEqual(record["pid"], process.pid)

    def test_different_projects_have_independent_records(self) -> None:
        other_project = self.root / "other"
        other_kanban = other_project / ".agents" / "kanban"
        other_kanban.mkdir(parents=True)
        (other_kanban / "kanban.html").write_text("kanban", encoding="utf-8")
        with (
            patch.object(boss_services, "SERVICE_STATE_DIR", self.state_dir),
            patch.object(boss_services, "get_bun_executable", return_value="bun"),
            patch.object(boss_services, "create_detached_process", side_effect=[FakeProcess(1), FakeProcess(2)]) as launch,
            patch.object(boss_services, "wait_for_service", return_value=True),
            patch.object(boss_services, "is_port_in_use", return_value=False),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            boss_services.cmd_kanban([str(self.project)])
            boss_services.cmd_kanban([str(other_project)])
        self.assertEqual(launch.call_count, 2)

    def test_dead_record_is_replaced_instead_of_reused(self) -> None:
        ServiceRegistry(self.state_dir).put("kanban", self.project, 5173, 999)
        with (
            patch.object(boss_services, "SERVICE_STATE_DIR", self.state_dir),
            patch.object(boss_services, "get_bun_executable", return_value="bun"),
            patch.object(boss_services, "create_detached_process", return_value=FakeProcess(1000)) as launch,
            patch.object(boss_services, "wait_for_service", return_value=True),
            patch.object(boss_services, "is_port_in_use", return_value=False),
            patch.object(boss_services, "is_process_alive", return_value=False),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(boss_services.cmd_kanban([str(self.project)]), 0)
        launch.assert_called_once()
        self.assertEqual(ServiceRegistry(self.state_dir).get("kanban", self.project)["pid"], 1000)

    def test_stop_uses_the_projects_actual_recorded_port(self) -> None:
        ServiceRegistry(self.state_dir).put("kanban", self.project, 5199, 123)
        with (
            patch.object(boss_services, "SERVICE_STATE_DIR", self.state_dir),
            patch.object(boss_services, "is_process_alive", return_value=True),
            patch.object(boss_services, "is_http_ready", return_value=True),
            patch.object(boss_services, "stop_server_by_port", return_value=True) as stop,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(boss_services.cmd_kanban(["stop", str(self.project)]), 0)
        stop.assert_called_once_with(5199)
        self.assertIsNone(ServiceRegistry(self.state_dir).get("kanban", self.project))

    def test_stop_without_record_does_not_kill_the_default_port(self) -> None:
        with (
            patch.object(boss_services, "SERVICE_STATE_DIR", self.state_dir),
            patch.object(boss_services, "stop_server_by_port") as stop,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(boss_services.cmd_kanban(["stop", str(self.project)]), 0)
        stop.assert_not_called()

    def test_detached_process_never_inherits_terminal_input(self) -> None:
        with patch.object(boss_services.subprocess, "Popen", return_value=FakeProcess()) as popen:
            boss_services.create_detached_process(["bun", "x", "vite"])
        self.assertIs(popen.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertIs(popen.call_args.kwargs["stdout"], subprocess.DEVNULL)
        self.assertIs(popen.call_args.kwargs["stderr"], subprocess.DEVNULL)

    def test_code_daemon_also_disconnects_child_terminal_input(self) -> None:
        with (
            patch.object(boss_services, "SERVICE_STATE_DIR", self.state_dir),
            patch.object(boss_services, "get_bun_executable", return_value="bun"),
            patch.object(boss_services, "create_detached_process", return_value=FakeProcess()) as launch,
            patch.object(boss_services, "find_running_code_server", return_value=None),
            patch.object(boss_services, "wait_for_service", return_value=True),
            patch.object(boss_services, "is_port_in_use", return_value=False),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(boss_services.cmd_code([str(self.project)]), 0)
        daemon_script = launch.call_args.args[0][2]
        self.assertIn("stdin=subprocess.DEVNULL", daemon_script)

    def test_state_file_is_human_readable_json(self) -> None:
        registry = ServiceRegistry(self.state_dir)
        registry.put("kanban", self.project, 5173, 123)
        data = json.loads((self.state_dir / "services.json").read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 1)
        self.assertEqual(len(data["services"]), 1)


if __name__ == "__main__":
    unittest.main()
