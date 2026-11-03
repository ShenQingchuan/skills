#!/usr/bin/env bash
# ==============================================================================
# boss 一键无感安装脚本 (macOS / Linux)
#
# 特性：
# 1. 零手动 chmod：执行 sh install.sh 即可，脚本自动处理项目所有权限；
# 2. 免疫权限失效：在 ~/.local/bin 生成 python3 启动包装器，源码即使无执行权限也能跑；
# 3. 自动配置 PATH：智能检测 zsh/bash 配置文件并自动注入环境变量，无需手动编辑；
# 4. 自动同步技能：安装末尾执行 sync-skills，首次安装即可得到完整技能库。
# ==============================================================================
set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/.local/bin"
TARGET_CMD="$TARGET_DIR/boss"
COMPLETION_DIR="$HOME/.local/share/boss/completions"
ZSH_COMPLETION="$COMPLETION_DIR/boss.zsh"
BASH_COMPLETION="$COMPLETION_DIR/boss.bash"

echo "=================================================="
echo "🚀 [boss] 正在安装个人 Skill 治理框架..."
echo "=================================================="

# 初始化本机配置与目录；重装时绝不覆盖已有配置
mkdir -p "$REPO_ROOT/registry/.synced" "$REPO_ROOT/profiles"
if [ ! -f "$REPO_ROOT/config.json" ]; then
    cp "$REPO_ROOT/config.example.json" "$REPO_ROOT/config.json"
    echo "✓ 已创建本机配置: $REPO_ROOT/config.json"
fi

# 1. 自动为项目内部所有脚本赋予执行权限（静默自动完成，无需用户介入）
chmod +x "$REPO_ROOT/bin/boss" 2>/dev/null || true
chmod +x "$REPO_ROOT/install.sh" 2>/dev/null || true
chmod +x "$REPO_ROOT/bin/setup-runtime.sh" 2>/dev/null || true
chmod +x "$REPO_ROOT/bin/sync_skills.py" 2>/dev/null || true
chmod +x "$REPO_ROOT/skills-router/scripts/list_skills.py" 2>/dev/null || true

# 2. 确保用户可执行目录 ~/.local/bin 存在
mkdir -p "$TARGET_DIR"

# 3. 创建防权限失效的 Wrapper 启动器
# 无论未来源码目录权限如何变动，显式调用 python3 均能 100% 成功执行
cat << 'EOF' > "$TARGET_CMD"
#!/usr/bin/env bash
REPO_BOSS="__REPO_ROOT__/bin/boss"
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$REPO_BOSS" "$@"
else
    exec python "$REPO_BOSS" "$@"
fi
EOF

# 将当前仓库真实路径注入包装器中，并赋予包装器执行权限
sed -i.bak "s|__REPO_ROOT__|$REPO_ROOT|g" "$TARGET_CMD" && rm -f "$TARGET_CMD.bak"
chmod 755 "$TARGET_CMD"

# 安装 zsh / Bash 补全脚本，Shell 配置只负责加载这里的副本
mkdir -p "$COMPLETION_DIR"
cp "$REPO_ROOT/completions/boss.zsh" "$ZSH_COMPLETION"
cp "$REPO_ROOT/completions/boss.bash" "$BASH_COMPLETION"

# 清理旧版 skill-boss 命令（如果存在）
rm -f "$TARGET_DIR/skill-boss"

echo "✓ 已成功部署可执行命令: $TARGET_CMD"

# 4. 自动检测并配置 Shell 环境变量（免除手动编辑 ~/.zshrc / ~/.bashrc）
DETECTED_RC=""
SHELL_NAME="${SHELL##*/}"
if [ -n "$ZSH_VERSION" ] || [ "$SHELL_NAME" = "zsh" ]; then
    DETECTED_RC="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    if [ -f "$HOME/.bashrc" ] || [ ! -f "$HOME/.bash_profile" ]; then
        DETECTED_RC="$HOME/.bashrc"
    else
        DETECTED_RC="$HOME/.bash_profile"
    fi
elif [ -f "$HOME/.zshrc" ]; then
    DETECTED_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    DETECTED_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    DETECTED_RC="$HOME/.bash_profile"
fi

PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
AUTO_CONFIGURED=0

if [ -n "$DETECTED_RC" ]; then
    if ! grep -qs '\.local/bin' "$DETECTED_RC" 2>/dev/null; then
        echo "" >> "$DETECTED_RC"
        echo "# boss CLI 路径配置" >> "$DETECTED_RC"
        echo "$PATH_LINE" >> "$DETECTED_RC"
        AUTO_CONFIGURED=1
        echo "✓ 已自动将 PATH 配置写入: $DETECTED_RC"
    fi
fi

# 只为安装时检测到的 Shell 写入配置，重复执行不会重复添加
configure_completion() {
    local rc_file="$1"
    local completion_file="$2"
    local shell_label="$3"
    local source_line="[ -r \"$completion_file\" ] && source \"$completion_file\""

    if ! grep -qsF "$source_line" "$rc_file" 2>/dev/null; then
        printf '\n# boss CLI %s Tab 自动补全\n%s\n' "$shell_label" "$source_line" >> "$rc_file"
    fi
    echo "✓ 已配置 $shell_label Tab 自动补全: $rc_file"
}

case "$DETECTED_RC" in
    */.zshrc)
        configure_completion "$DETECTED_RC" "$ZSH_COMPLETION" "zsh"
        ;;
    */.bashrc|*/.bash_profile)
        configure_completion "$DETECTED_RC" "$BASH_COMPLETION" "Bash"
        ;;
esac

# 首次安装直接拉齐技能库；重复安装时同步脚本会按指纹幂等处理
echo ""
echo "🔄 正在同步技能库..."
if ! "$TARGET_CMD" sync-skills; then
    echo "❌ 技能同步失败。请检查网络后重新运行 install.sh，或手动执行 boss sync-skills。" >&2
    exit 1
fi

echo "=================================================="
echo "🎉 安装完成！"
echo ""
if [[ ":$PATH:" == *":$TARGET_DIR:"* ]]; then
    echo "你可以直接在当前终端执行: boss --help"
elif [ $AUTO_CONFIGURED -eq 1 ]; then
    echo "💡 环境变量已自动配置完成！"
    echo "   新打开的终端可直接输入: boss"
    echo "   若在当前终端立即使用，请执行: export PATH=\"\$HOME/.local/bin:\$PATH\""
else
    echo "💡 提示: 请将 $TARGET_DIR 加入你的 PATH 变量以在任意处直接使用 boss"
fi
echo "=================================================="

