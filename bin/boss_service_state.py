#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Boss 后台服务的本机运行记录。"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class ServiceRegistry:
    """按服务类型和项目路径保存运行记录，并串行化启动与停止操作。"""

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_file = state_dir / "services.json"
        self.lock_file = state_dir / "services.lock"

    @contextmanager
    def locked(self) -> Iterator[None]:
        """持有本机文件锁，避免同时执行命令时重复启动服务。"""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.lock_file.open("a+b") as lock:
            if os.name == "nt":
                import msvcrt

                lock.seek(0, os.SEEK_END)
                if lock.tell() == 0:
                    lock.write(b"\0")
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def get(self, service: str, project_root: Path) -> dict | None:
        """读取单个项目的记录；损坏或不完整的数据视为不存在。"""
        record = self._load().get(self._key(service, project_root))
        if not isinstance(record, dict):
            return None
        if not isinstance(record.get("port"), int):
            return None
        return dict(record)

    def put(self, service: str, project_root: Path, port: int, pid: int) -> dict:
        """写入或覆盖单个项目的运行记录。"""
        state = self._load()
        key = self._key(service, project_root)
        previous = state.get(key, {})
        now = time.time()
        record = {
            "service": service,
            "projectRoot": str(project_root.resolve()),
            "port": port,
            "pid": pid,
            "startedAt": previous.get("startedAt", now),
            "updatedAt": now,
        }
        state[key] = record
        self._write(state)
        return dict(record)

    def remove(self, service: str, project_root: Path) -> None:
        """移除单个项目的记录，不影响其他项目。"""
        state = self._load()
        if state.pop(self._key(service, project_root), None) is not None:
            self._write(state)

    def _key(self, service: str, project_root: Path) -> str:
        return f"{service}:{project_root.resolve()}"

    def _load(self) -> dict:
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}
        records = data.get("services")
        return dict(records) if isinstance(records, dict) else {}

    def _write(self, records: dict) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "services": records}
        temporary = self.state_file.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.state_file)
