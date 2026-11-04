#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Boss 网页看板与编辑器服务。"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from boss_runtime import resolve_runtime_executable

ROOT_DIR = Path(__file__).resolve().parent.parent
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


def get_bun_executable() -> str:
    """返回沙盒 Bun；未安装时给出明确的修复提示。"""
    return str(resolve_runtime_executable("bun", ROOT_DIR))


def is_port_in_use(port: int) -> bool:
    """检测指定端口是否已被占用（同时检查 IPv4 与 IPv6）"""
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((host, port)) == 0:
                    return True
        except Exception:
            pass
    return False


def find_available_port(start_port: int, max_attempts: int = 20) -> int:
    """自动寻找从 start_port 开始可用的端口"""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p):
            return p
    return start_port


def ensure_kanban_installed(kanban_dir: Path) -> None:
    """如果项目还没有 kanban.html，自动为其安装看板模板和 history.md"""
    kanban_dir.mkdir(parents=True, exist_ok=True)
    kanban_html = kanban_dir / "kanban.html"

    if kanban_html.exists():
        return

    print("ℹ️  检测到项目尚未安装看板，正在自动初始化到 .agents/kanban/ ...")
    if not KANBAN_ASSETS_DIR.exists():
        print(f"❌ 找不到看板模板目录: {KANBAN_ASSETS_DIR}", file=sys.stderr)
        return

    # 复制样式与前端驱动核心
    shutil.copy2(KANBAN_ASSETS_DIR / "kanban-style.css", kanban_dir / "kanban-style.css")
    shutil.copy2(KANBAN_ASSETS_DIR / "kanban-app.js", kanban_dir / "kanban-app.js")
    shutil.copy2(KANBAN_ASSETS_DIR / "kanban.html", kanban_html)
    print(f"✓ 已生成看板页面: {kanban_html}")

    history_md = kanban_dir / "history.md"
    if not history_md.exists():
        history_content = (
            "# 项目任务历史归档\n\n"
            "本项目所有通过人类验收（Accepted）的任务均会从实时看板中移出，按时间顺序沉淀于此。\n\n"
            "---\n"
        )
        history_md.write_text(history_content, encoding="utf-8")
        print(f"✓ 已初始化归档文件: {history_md}")


def find_running_code_server_port(project_root: Path) -> int | None:
    """检查是否已经有为当前目录启动的 coderaft 实例，若有则返回其端口"""
    try:
        out = subprocess.check_output("ps -eo pid,command", shell=True, text=True)
        norm_target = str(project_root.resolve())
        for line in out.splitlines():
            if "coderaft" in line and "--default-folder" in line:
                # 检查 default-folder 是否匹配当前目录
                parts = line.split()
                if "--default-folder" in parts:
                    df_idx = parts.index("--default-folder")
                    if df_idx + 1 < len(parts):
                        folder_arg = str(Path(parts[df_idx + 1]).resolve())
                        if folder_arg == norm_target:
                            # 提取其端口
                            if "-p" in parts:
                                p_idx = parts.index("-p")
                                if p_idx + 1 < len(parts):
                                    return int(parts[p_idx + 1])
                            if "--port" in parts:
                                p_idx = parts.index("--port")
                                if p_idx + 1 < len(parts):
                                    return int(parts[p_idx + 1])
    except Exception:
        pass
    return None


def stop_server_by_port(port: int) -> bool:
    """按端口号直接释放后台进程，零临时文件产生"""
    is_windows = sys.platform.startswith("win")
    stopped = False
    try:
        if is_windows:
            out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
            for line in out.strip().splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and f":{port}" in parts[1]:
                    p = parts[-1]
                    subprocess.run(f"taskkill /F /PID {p}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    stopped = True
        else:
            out = subprocess.check_output(f"lsof -ti :{port}", shell=True, text=True)
            for pid_str in out.strip().split():
                os.kill(int(pid_str), 15)
                stopped = True
    except Exception:
        pass

    return stopped


def stop_kanban_server(port: int = 5173) -> bool:
    """按端口号释放看板进程"""
    return stop_server_by_port(port)


def stop_code_server(port: int = 6063) -> bool:
    """按端口号释放网页编辑器进程"""
    return stop_server_by_port(port)


def cmd_kanban(args: list[str]) -> int:
    """启动或停止指定项目的网页看板服务"""
    project_root = Path.cwd()
    port = 5173
    is_stop_cmd = False

    # 解析子命令与参数：boss kanban [stop] [项目路径] [--port 端口]
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "stop":
            is_stop_cmd = True
            idx += 1
        elif arg in ("--port", "-p"):
            if idx + 1 < len(args):
                try:
                    port = int(args[idx + 1])
                    idx += 2
                    continue
                except ValueError:
                    print(f"❌ 端口必须是纯数字: {args[idx + 1]}", file=sys.stderr)
                    return 1
            else:
                print("❌ --port 需要提供端口号参数", file=sys.stderr)
                return 1
        elif arg.startswith("--port="):
            try:
                port = int(arg.split("=", 1)[1])
                idx += 1
                continue
            except ValueError:
                print(f"❌ 端口必须是纯数字: {arg}", file=sys.stderr)
                return 1
        elif not arg.startswith("-"):
            project_root = Path(arg).resolve()
            idx += 1
        else:
            idx += 1

    # 确定看板目录：用户当前 cwd（或指定的项目路径）就是项目根目录
    kanban_dir = project_root / ".agents" / "kanban"

    # 处理 stop 停止命令
    if is_stop_cmd:
        print(f"⏹️  正在停止端口 {port} 的看板服务...")
        success = stop_kanban_server(port=port)
        if success:
            print(f"✓ 端口 {port} 对应的看板服务已停止。")
        else:
            print(f"ℹ️  未发现运行中的看板进程（端口 {port} 未被占用）。")
        return 0

    if not project_root.exists():
        project_root.mkdir(parents=True, exist_ok=True)

    # 1. 确保看板必要资产已就绪
    ensure_kanban_installed(kanban_dir)

    # 2. 检查端口是否被占用，若被占用则顺延选择可用端口
    if is_port_in_use(port):
        next_port = find_available_port(port + 1)
        print(f"ℹ️  端口 {port} 已被占用，已自动换用新端口: {next_port}")
        port = next_port

    # 3. 启动后台服务：使用 Bun x Vite 驱动 HMR，把缓存严格限制在系统 /tmp，确保项目目录 100% 干净
    try:
        bun_bin = get_bun_executable()
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    tmp_config = Path(tempfile.gettempdir()) / "vite-kanban.config.mjs"
    tmp_cache = Path(tempfile.gettempdir()) / "vite-kanban-cache"
    tmp_config.write_text(f"export default {{\n  cacheDir: {json.dumps(str(tmp_cache))}\n}};\n", encoding="utf-8")

    cmd = [bun_bin, "x", "vite", "--config", str(tmp_config), "--port", str(port)]

    is_windows = sys.platform.startswith("win")
    if is_windows:
        creation_flags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creation_flags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creation_flags |= subprocess.DETACHED_PROCESS
        proc = subprocess.Popen(
            cmd,
            cwd=str(kanban_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(kanban_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    # 等待确认进程启动成功
    time.sleep(0.6)
    if proc.poll() is not None:
        print("❌ 看板服务启动失败，请检查端口是否冲突或运行环境是否正常。", file=sys.stderr)
        return 1

    # 4. 打印启动成功报告
    url = f"http://localhost:{port}/kanban.html"
    report = f"""
==================================================
🚀 项目任务看板服务已在后台启动！
--------------------------------------------------
📌 访问地址: {url}
📁 项目工作区: {project_root}
📂 看板目录:   {kanban_dir}
⚡ 驱动引擎:   Vite (HMR 实时热更新)
🔢 进程 PID:   {proc.pid}
💡 停止服务:   boss kanban stop [--port {port}]
==================================================
"""
    print(report.strip())
    return 0


def cmd_code(args: list[str]) -> int:
    """启动或停止基于 coderaft 的轻量网页编辑器，带浏览器自动打开与闲置自动关闭守护"""
    project_root = Path.cwd()
    port = 6063
    is_stop_cmd = False

    # 解析参数：boss code [stop] [项目路径] [--port 端口]
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "stop":
            is_stop_cmd = True
            idx += 1
        elif arg in ("--port", "-p"):
            if idx + 1 < len(args):
                try:
                    port = int(args[idx + 1])
                    idx += 2
                    continue
                except ValueError:
                    print(f"❌ 端口必须是纯数字: {args[idx + 1]}", file=sys.stderr)
                    return 1
            else:
                print("❌ --port 需要提供端口号参数", file=sys.stderr)
                return 1
        elif arg.startswith("--port="):
            try:
                port = int(arg.split("=", 1)[1])
                idx += 1
                continue
            except ValueError:
                print(f"❌ 端口必须是纯数字: {arg}", file=sys.stderr)
                return 1
        elif not arg.startswith("-"):
            project_root = Path(arg).resolve()
            idx += 1
        else:
            idx += 1

    if is_stop_cmd:
        print(f"⏹️  正在停止端口 {port} 的网页编辑器服务...")
        success = stop_code_server(port=port)
        if success:
            print(f"✓ 端口 {port} 对应的网页编辑器已停止。")
        else:
            print(f"ℹ️  未发现运行中的编辑器进程（端口 {port} 未被占用）。")
        return 0

    if not project_root.exists():
        project_root.mkdir(parents=True, exist_ok=True)

    # 1. 检查是否已经为当前项目启动过 coderaft 服务，若已启动直接在浏览器重新激活，绝不换新端口重复启动
    existing_port = find_running_code_server_port(project_root)
    if existing_port:
        url = f"http://localhost:{existing_port}"
        print(f"ℹ️  检测到当前工作区已在运行网页编辑器 (端口: {existing_port})，正在浏览器中打开...")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
        return 0

    if is_port_in_use(port):
        next_port = find_available_port(port + 1)
        print(f"ℹ️  默认端口 {port} 已被占用，已自动换用新端口: {next_port}")
        port = next_port

    try:
        bun_bin = get_bun_executable()
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    # 守护脚本：后台启动 coderaft，自动在浏览器打开，并每分钟检查 /healthz 心跳。若连续 2 小时无网络活跃或无连接则自动关停
    ext_args = []
    for ext in DEFAULT_CODE_EXTENSIONS:
        ext_args.extend(["--preinstall-extension", ext])

    daemon_script = f"""
import subprocess, time, sys, os, urllib.request, json, webbrowser

port = {port}
folder = {json.dumps(str(project_root))}
bun_bin = {json.dumps(bun_bin)}
ext_args = {json.dumps(ext_args)}

# 启动 coderaft 服务，预装核心扩展（已装的跳过，未装的自动安装）
cmd = [bun_bin, "x", "coderaft", "-p", str(port), "--default-folder", folder, "--no-tui"] + ext_args
proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 等待服务就绪并自动用浏览器打开
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
max_idle_seconds = 7200  # 2 小时

while True:
    time.sleep(60)
    if proc.poll() is not None:
        break
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{{port}}/healthz", timeout=2) as resp:
            data = json.loads(resp.read().decode())
            hb = data.get("lastHeartbeat")
            if hb != last_heartbeat:
                last_heartbeat = hb
                last_active = time.time()
    except Exception:
        pass

    # 超过 2 小时没有活跃活动，自动优雅关闭
    if time.time() - last_active > max_idle_seconds:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        break
"""

    is_windows = sys.platform.startswith("win")
    if is_windows:
        creation_flags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creation_flags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creation_flags |= subprocess.DETACHED_PROCESS
        proc = subprocess.Popen(
            [sys.executable, "-c", daemon_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
    else:
        proc = subprocess.Popen(
            [sys.executable, "-c", daemon_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    # 4. 打印启动成功报告
    url = f"http://localhost:{port}"
    report = f"""
==================================================
🛶 网页代码编辑器 (coderaft) 已在后台启动！
--------------------------------------------------
📌 访问地址: {url}
📁 工作区路径: {project_root}
⚡ 守护机制:   已自动打开浏览器，若连续 2 小时闲置无动静将自动关闭
💡 停止服务:   boss code stop [--port {port}]
==================================================
"""
    print(report.strip())
    return 0
