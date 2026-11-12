#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Boss 网页看板与编辑器服务。"""

from __future__ import annotations

import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import webbrowser
from pathlib import Path

from boss_runtime import resolve_runtime_executable
from boss_service_state import ServiceRegistry

ROOT_DIR = Path(__file__).resolve().parent.parent
SERVICE_STATE_DIR = ROOT_DIR / ".local"
KANBAN_ASSETS_DIR = (
    ROOT_DIR / "registry" / "workflow" / "manage-project-kanban" / "assets" / "kanban-app"
)
DEFAULT_CODE_EXTENSIONS = [
    "ms-ceintl.vscode-language-pack-zh-hans",
    "catppuccin.catppuccin-vsc",
    "catppuccin.catppuccin-vsc-icons",
    "pkief.material-product-icons",
    "usernamehw.errorlens",
    "dbaeumer.vscode-eslint",
    "vue.volar",
    "golang.go",
    "unifiedjs.vscode-mdx",
    "ms-python.python",
]
HEALTH_PATHS = {"kanban": "/kanban.html", "code": "/healthz"}


def get_bun_executable() -> str:
    """返回沙盒 Bun；未安装时给出明确的修复提示。"""
    return str(resolve_runtime_executable("bun", ROOT_DIR))


def is_port_in_use(port: int) -> bool:
    """检测指定端口是否已被占用（同时检查 IPv4 与 IPv6）。"""
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                if sock.connect_ex((host, port)) == 0:
                    return True
        except OSError:
            pass
    return False


def find_available_port(start_port: int, max_attempts: int = 20) -> int:
    """从指定端口开始寻找空闲端口。"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"从 {start_port} 开始的 {max_attempts} 个端口均已被占用")


def is_http_ready(port: int, path: str) -> bool:
    """直接访问本机服务，不经过系统代理，兼容仅监听 IPv6 的服务。"""
    for host in ("127.0.0.1", "::1"):
        connection = http.client.HTTPConnection(host, port, timeout=0.5)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            response.read()
            if 200 <= response.status < 400:
                return True
        except (OSError, http.client.HTTPException):
            pass
        finally:
            connection.close()
    return False


def is_process_alive(pid: int) -> bool:
    """检查记录中的进程是否仍然存在。"""
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        return str(pid) in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def wait_for_service(port: int, path: str, proc: subprocess.Popen, timeout: int = 30) -> bool:
    """等待服务真正可访问，避免启动中的重复调用再次开新进程。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_http_ready(port, path):
            return True
        if proc.poll() is not None:
            return is_http_ready(port, path)
        time.sleep(0.1)
    return False


def create_detached_process(cmd: list[str], cwd: Path | None = None) -> subprocess.Popen:
    """启动与终端输入、输出完全分离的后台进程。"""
    options = {
        "cwd": str(cwd) if cwd else None,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform.startswith("win"):
        creation_flags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creation_flags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creation_flags |= subprocess.DETACHED_PROCESS
        options["creationflags"] = creation_flags
    else:
        options["start_new_session"] = True
    return subprocess.Popen(cmd, **options)


def ensure_kanban_installed(kanban_dir: Path) -> None:
    """如果项目还没有 kanban.html，自动安装看板模板和归档文件。"""
    kanban_dir.mkdir(parents=True, exist_ok=True)
    kanban_html = kanban_dir / "kanban.html"
    if kanban_html.exists():
        return

    print("ℹ️  检测到项目尚未安装看板，正在自动初始化到 .agents/kanban/ ...")
    if not KANBAN_ASSETS_DIR.exists():
        raise RuntimeError(f"找不到看板模板目录: {KANBAN_ASSETS_DIR}")
    shutil.copy2(KANBAN_ASSETS_DIR / "kanban-style.css", kanban_dir / "kanban-style.css")
    shutil.copy2(KANBAN_ASSETS_DIR / "kanban-app.js", kanban_dir / "kanban-app.js")
    shutil.copy2(KANBAN_ASSETS_DIR / "kanban.html", kanban_html)
    print(f"✓ 已生成看板页面: {kanban_html}")

    history_md = kanban_dir / "history.md"
    if not history_md.exists():
        history_md.write_text(
            "# 项目任务历史归档\n\n"
            "本项目所有通过人类验收（Accepted）的任务均会从实时看板中移出，按时间顺序沉淀于此。\n\n"
            "---\n",
            encoding="utf-8",
        )
        print(f"✓ 已初始化归档文件: {history_md}")


def find_running_code_server(project_root: Path) -> tuple[int, int] | None:
    """兼容发现尚未写入运行记录的 coderaft，返回 PID 和端口。"""
    try:
        out = subprocess.check_output("ps -eo pid,command", shell=True, text=True)
        target = str(project_root.resolve())
        for line in out.splitlines():
            if "coderaft" not in line or "--default-folder" not in line:
                continue
            parts = line.split()
            folder_index = parts.index("--default-folder")
            if folder_index + 1 >= len(parts) or str(Path(parts[folder_index + 1]).resolve()) != target:
                continue
            for flag in ("-p", "--port"):
                if flag in parts and parts.index(flag) + 1 < len(parts):
                    return int(parts[0]), int(parts[parts.index(flag) + 1])
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return None


def find_running_service(
    registry: ServiceRegistry, service: str, project_root: Path
) -> dict | None:
    """返回当前项目仍可访问的服务，并清理已经失效的记录。"""
    record = registry.get(service, project_root)
    if record:
        pid = record.get("pid")
        if (
            isinstance(pid, int)
            and is_process_alive(pid)
            and is_http_ready(record["port"], HEALTH_PATHS[service])
        ):
            return record
        registry.remove(service, project_root)

    if service == "code":
        detected = find_running_code_server(project_root)
        if detected and is_http_ready(detected[1], HEALTH_PATHS[service]):
            return registry.put(service, project_root, detected[1], detected[0])
    return None


def stop_server_by_port(port: int) -> bool:
    """停止监听指定端口的进程。"""
    stopped = False
    try:
        if sys.platform.startswith("win"):
            out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
            for line in out.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    subprocess.run(
                        f"taskkill /F /PID {parts[-1]}",
                        shell=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    stopped = True
        else:
            out = subprocess.check_output(f"lsof -ti :{port}", shell=True, text=True)
            for pid in out.strip().split():
                os.kill(int(pid), 15)
                stopped = True
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return stopped


def parse_service_args(args: list[str], default_port: int) -> tuple[Path, int, bool, bool]:
    """解析服务命令共用的项目路径、停止标记和端口参数。"""
    project_root = Path.cwd()
    port = default_port
    is_stop = False
    port_explicit = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "stop":
            is_stop = True
            index += 1
        elif arg in ("--port", "-p"):
            if index + 1 >= len(args):
                raise ValueError("--port 需要提供端口号参数")
            try:
                port = int(args[index + 1])
            except ValueError as error:
                raise ValueError(f"端口必须是纯数字: {args[index + 1]}") from error
            port_explicit = True
            index += 2
        elif arg.startswith("--port="):
            try:
                port = int(arg.split("=", 1)[1])
            except ValueError as error:
                raise ValueError(f"端口必须是纯数字: {arg}") from error
            port_explicit = True
            index += 1
        elif not arg.startswith("-"):
            project_root = Path(arg).resolve()
            index += 1
        else:
            index += 1
    if not 1 <= port <= 65535:
        raise ValueError(f"端口必须在 1-65535 之间: {port}")
    return project_root.resolve(), port, is_stop, port_explicit


def stop_project_service(
    registry: ServiceRegistry,
    service: str,
    project_root: Path,
    requested_port: int,
    port_explicit: bool,
) -> int:
    """优先停止当前项目记录的服务，仅显式指定端口时按端口停止。"""
    with registry.locked():
        record = find_running_service(registry, service, project_root)
        if record:
            port = record["port"]
        elif port_explicit:
            port = requested_port
        else:
            print(f"ℹ️  当前项目没有运行中的{service_name(service)}。")
            return 0

        print(f"⏹️  正在停止端口 {port} 的{service_name(service)}...")
        stopped = stop_server_by_port(port)
        if record and (stopped or not is_port_in_use(port)):
            registry.remove(service, project_root)
        if stopped:
            print(f"✓ 端口 {port} 对应的{service_name(service)}已停止。")
        else:
            print(f"ℹ️  端口 {port} 当前没有可停止的服务。")
        return 0


def service_name(service: str) -> str:
    return "看板服务" if service == "kanban" else "网页编辑器"


def cmd_kanban(args: list[str]) -> int:
    """启动、复用或停止指定项目的网页看板服务。"""
    try:
        project_root, port, is_stop, port_explicit = parse_service_args(args, 5173)
    except ValueError as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1

    registry = ServiceRegistry(SERVICE_STATE_DIR)
    if is_stop:
        return stop_project_service(registry, "kanban", project_root, port, port_explicit)

    try:
        with registry.locked():
            record = find_running_service(registry, "kanban", project_root)
            if record:
                print_kanban_report(record, reused=True)
                return 0

            project_root.mkdir(parents=True, exist_ok=True)
            kanban_dir = project_root / ".agents" / "kanban"
            ensure_kanban_installed(kanban_dir)
            if is_port_in_use(port):
                next_port = find_available_port(port + 1)
                print(f"ℹ️  端口 {port} 已被占用，已自动换用新端口: {next_port}")
                port = next_port

            bun_bin = get_bun_executable()
            tmp_config = Path(tempfile.gettempdir()) / "vite-kanban.config.mjs"
            tmp_cache = Path(tempfile.gettempdir()) / "vite-kanban-cache"
            tmp_config.write_text(
                f"export default {{\n  cacheDir: {json.dumps(str(tmp_cache))}\n}};\n",
                encoding="utf-8",
            )
            proc = create_detached_process(
                [bun_bin, "x", "vite", "--config", str(tmp_config), "--port", str(port)],
                cwd=kanban_dir,
            )
            if not wait_for_service(port, HEALTH_PATHS["kanban"], proc):
                stop_server_by_port(port)
                print("❌ 看板服务启动失败，请检查端口和运行环境。", file=sys.stderr)
                return 1
            record = registry.put("kanban", project_root, port, proc.pid)
    except (OSError, RuntimeError) as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1

    print_kanban_report(record, reused=False)
    return 0


def print_kanban_report(record: dict, reused: bool) -> None:
    """打印看板的唯一访问地址和停止方式。"""
    title = "当前项目看板已在运行，直接复用！" if reused else "项目任务看板服务已在后台启动！"
    port = record["port"]
    print(
        f"""
==================================================
🚀 {title}
--------------------------------------------------
📌 访问地址: http://localhost:{port}/kanban.html
📁 项目工作区: {record['projectRoot']}
🔢 进程 PID:   {record['pid']}
💡 停止服务:   boss kanban stop {record['projectRoot']}
==================================================
""".strip()
    )


def cmd_code(args: list[str]) -> int:
    """启动、复用或停止带闲置自动关闭的网页编辑器。"""
    try:
        project_root, port, is_stop, port_explicit = parse_service_args(args, 6063)
    except ValueError as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1

    registry = ServiceRegistry(SERVICE_STATE_DIR)
    if is_stop:
        return stop_project_service(registry, "code", project_root, port, port_explicit)

    try:
        with registry.locked():
            record = find_running_service(registry, "code", project_root)
            if record:
                url = f"http://localhost:{record['port']}"
                print(f"ℹ️  当前工作区已在运行网页编辑器 (端口: {record['port']})，正在打开...")
                webbrowser.open(url)
                return 0

            project_root.mkdir(parents=True, exist_ok=True)
            if is_port_in_use(port):
                next_port = find_available_port(port + 1)
                print(f"ℹ️  默认端口 {port} 已被占用，已自动换用新端口: {next_port}")
                port = next_port
            bun_bin = get_bun_executable()
            extension_args = []
            for extension in DEFAULT_CODE_EXTENSIONS:
                extension_args.extend(["--preinstall-extension", extension])

            daemon_script = f"""
import subprocess, time, urllib.request, json, webbrowser

port = {port}
folder = {json.dumps(str(project_root))}
bun_bin = {json.dumps(bun_bin)}
ext_args = {json.dumps(extension_args)}
cmd = [bun_bin, "x", "coderaft", "-p", str(port), "--default-folder", folder, "--no-tui"] + ext_args
proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(30):
    time.sleep(0.3)
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{{port}}/healthz", timeout=1)
        webbrowser.open(f"http://localhost:{{port}}")
        break
    except Exception:
        pass
last_active = time.time()
last_heartbeat = None
while True:
    time.sleep(60)
    if proc.poll() is not None:
        break
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{{port}}/healthz", timeout=2) as resp:
            data = json.loads(resp.read().decode())
            heartbeat = data.get("lastHeartbeat")
            if heartbeat != last_heartbeat:
                last_heartbeat = heartbeat
                last_active = time.time()
    except Exception:
        pass
    if time.time() - last_active > 7200:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        break
"""
            proc = create_detached_process([sys.executable, "-c", daemon_script])
            if not wait_for_service(port, HEALTH_PATHS["code"], proc):
                proc.terminate()
                stop_server_by_port(port)
                print("❌ 网页编辑器启动失败，请检查端口和运行环境。", file=sys.stderr)
                return 1
            record = registry.put("code", project_root, port, proc.pid)
    except (OSError, RuntimeError) as error:
        print(f"❌ {error}", file=sys.stderr)
        return 1

    print(
        f"""
==================================================
🛶 网页代码编辑器 (coderaft) 已在后台启动！
--------------------------------------------------
📌 访问地址: http://localhost:{record['port']}
📁 工作区路径: {project_root}
⚡ 守护机制:   已自动打开浏览器，连续 2 小时闲置后自动关闭
💡 停止服务:   boss code stop {project_root}
==================================================
""".strip()
    )
    return 0
