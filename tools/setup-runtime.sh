#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# ==============================================================================
# Skills Suite Runtime Injector (macOS / Linux)
#
# 为本 skills 套件提供独立、纯净、开箱即用的运行引擎：
# 1. 0 外部依赖：仅使用系统底层 curl 与 tar/unzip，自动下载部署官方绿色版：
#    - Node.js (最新 LTS, 内置 npm, 原生直接支持执行 TS)
#    - Bun (单文件极速 JS/TS 引擎)
#    - uv (现代 Python 包与工具管理器) & Python 3.12 独立运行时
#    - ripgrep (极速文本检索工具 rg)
# 2. 私有沙盒：所有引擎与产物均严格收拢在 .runtime/ 目录下，绝不污染全局系统；
# 3. 依赖隔离：本套件所需的 npm 依赖全部安装于 .runtime/node_modules，不脏宿主环境。
# ==============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"
RUNTIME_BIN="$RUNTIME_DIR/bin"

mkdir -p "$RUNTIME_DIR"
mkdir -p "$RUNTIME_BIN"

# 查看就绪状态子命令
if [ "$1" = "--status" ] || [ "$1" = "-s" ]; then
    echo "=========================================================="
    echo "🔍 [Skills Runtime 状态检测]"
    echo "=========================================================="
    echo "沙盒根目录: $RUNTIME_DIR"
    echo "引擎路径:   $RUNTIME_BIN"
    echo "----------------------------------------------------------"
    [ -x "$RUNTIME_BIN/node" ]    && echo "✓ Node.js:  $("$RUNTIME_BIN/node" -v)" || echo "✗ Node.js:  未就绪"
    [ -x "$RUNTIME_BIN/bun" ]     && echo "✓ Bun:      $("$RUNTIME_BIN/bun" -v)"  || echo "✗ Bun:      未就绪"
    [ -x "$RUNTIME_BIN/uv" ]      && echo "✓ uv:       $("$RUNTIME_BIN/uv" --version | awk '{print $1,$2}')"  || echo "✗ uv:       未就绪"
    [ -x "$RUNTIME_BIN/python3" ] && echo "✓ Python:   $("$RUNTIME_BIN/python3" --version)" || echo "✗ Python:   未就绪"
    [ -x "$RUNTIME_BIN/rg" ]      && echo "✓ ripgrep:  $("$RUNTIME_BIN/rg" --version | head -n 1)" || echo "✗ ripgrep:  未就绪"
    echo "=========================================================="
    exit 0
fi

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: ./tools/setup-runtime [选项]"
    echo ""
    echo "选项:"
    echo "  (无参数)      为本 skills 套件下载并配置全套绿色运行时引擎"
    echo "  -s, --status  查看当前沙盒运行时的就绪状态及版本"
    echo "  -h, --help    显示帮助信息"
    exit 0
fi

echo "=========================================================="
echo "🚀 [Skills Runtime] 正在为本套件配置独立运行时引擎..."
echo "=========================================================="

# 1. 识别平台与架构
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Darwin)
        PLATFORM="darwin"
        UV_OS="apple-darwin"
        RG_OS="apple-darwin"
        ;;
    Linux)
        PLATFORM="linux"
        UV_OS="unknown-linux-gnu"
        RG_OS="unknown-linux-musl"
        ;;
    *)
        echo "❌ 暂不支持的操作系统: $OS"
        exit 1
        ;;
esac

case "$ARCH" in
    x86_64|amd64)
        NODE_ARCH="x64"
        BUN_ARCH="x64"
        UV_ARCH="x86_64"
        RG_ARCH="x86_64"
        ;;
    arm64|aarch64)
        NODE_ARCH="arm64"
        BUN_ARCH="aarch64"
        UV_ARCH="aarch64"
        RG_ARCH="aarch64"
        ;;
    *)
        echo "❌ 暂不支持的架构: $ARCH"
        exit 1
        ;;
esac

echo "💻 识别到系统平台: $PLATFORM ($ARCH)"

# 2. 初始化本套件专属 npm 依赖沙盒
if [ ! -f "$RUNTIME_DIR/package.json" ]; then
    echo '{"name": "skills-runtime-sandbox", "version": "1.0.0", "private": true, "type": "module"}' > "$RUNTIME_DIR/package.json"
fi
mkdir -p "$RUNTIME_DIR/node_modules"
mkdir -p "$RUNTIME_DIR/.npm-cache"

# ==============================================================================
# 3. 注入 Node.js LTS 绿色运行时
# ==============================================================================
NODE_DIR="$RUNTIME_DIR/node"
if [ ! -x "$NODE_DIR/bin/node" ]; then
    echo "📦 [1/5] 正在下载 Node.js 最新官方 LTS 绿色运行时..."
    NODE_VER=$( (curl -fsSL https://nodejs.org/dist/index.tab 2>/dev/null || true) | awk -F'\t' 'NR>1 && $10 != "-" && $10 != "" {print $1; exit}' )
    if [ -z "$NODE_VER" ]; then NODE_VER="v22.14.0"; fi
    echo "    -> 选定 LTS 版本: $NODE_VER"

    NODE_TAR="node-${NODE_VER}-${PLATFORM}-${NODE_ARCH}.tar.gz"
    NODE_URL="https://nodejs.org/dist/${NODE_VER}/${NODE_TAR}"
    TMP_NODE="/tmp/${NODE_TAR}"

    curl -fsSL "$NODE_URL" -o "$TMP_NODE"
    rm -rf "$NODE_DIR"
    mkdir -p "$NODE_DIR"
    tar -xzf "$TMP_NODE" -C "$NODE_DIR" --strip-components=1
    rm -f "$TMP_NODE"
    echo "    ✓ Node.js ($NODE_VER) 部署完成"
else
    echo "    ✓ Node.js 已就绪"
fi

# ==============================================================================
# 4. 注入 uv (Python 生态管理引擎)
# ==============================================================================
UV_DIR="$RUNTIME_DIR/uv"
if [ ! -x "$UV_DIR/uv" ]; then
    echo "📦 [2/5] 正在下载 uv (现代 Python 包与运行时管理器)..."
    UV_TAR="uv-${UV_ARCH}-${UV_OS}.tar.gz"
    UV_URL="https://github.com/astral-sh/uv/releases/latest/download/${UV_TAR}"
    TMP_UV="/tmp/${UV_TAR}"

    curl -fsSL "$UV_URL" -o "$TMP_UV"
    rm -rf "$UV_DIR"
    mkdir -p "$UV_DIR"
    tar -xzf "$TMP_UV" -C "$UV_DIR" --strip-components=1
    chmod +x "$UV_DIR/uv" "$UV_DIR/uvx"
    rm -f "$TMP_UV"
    echo "    ✓ uv 部署完成"
else
    echo "    ✓ uv 已就绪"
fi

# ==============================================================================
# 5. 注入 Python 3.12 独立绿色运行时
# ==============================================================================
echo "📦 [3/5] 正在确认独立 Python 3 运行时..."
PYTHON_EXEC=$("$UV_DIR/uv" python find 3.12 2>/dev/null || true)
if [ -z "$PYTHON_EXEC" ] || [ ! -x "$PYTHON_EXEC" ]; then
    echo "    -> 正在自动下载独立 Python 3.12 解释器..."
    "$UV_DIR/uv" python install 3.12
    PYTHON_EXEC=$("$UV_DIR/uv" python find 3.12)
fi
echo "    ✓ Python 环境就绪: $PYTHON_EXEC"

# ==============================================================================
# 6. 注入 Bun (极速单文件 JS/TS 引擎)
# ==============================================================================
BUN_DIR="$RUNTIME_DIR/bun"
if [ ! -x "$BUN_DIR/bun" ]; then
    echo "📦 [4/5] 正在下载 Bun (单文件 JS/TS 引擎)..."
    BUN_ZIP="bun-${PLATFORM}-${BUN_ARCH}.zip"
    BUN_URL="https://github.com/oven-sh/bun/releases/latest/download/${BUN_ZIP}"
    TMP_BUN="/tmp/${BUN_ZIP}"

    curl -fsSL "$BUN_URL" -o "$TMP_BUN"
    rm -rf "$BUN_DIR"
    mkdir -p "$BUN_DIR"
    unzip -q -o "$TMP_BUN" -d /tmp/bun_extracted
    mv /tmp/bun_extracted/bun-${PLATFORM}-${BUN_ARCH}/bun "$BUN_DIR/bun"
    chmod +x "$BUN_DIR/bun"
    rm -rf "$TMP_BUN" /tmp/bun_extracted
    echo "    ✓ Bun 部署完成"
else
    echo "    ✓ Bun 已就绪"
fi

# ==============================================================================
# 7. 注入 ripgrep (单文件文本检索工具 rg)
# ==============================================================================
RG_DIR="$RUNTIME_DIR/ripgrep"
if [ ! -x "$RG_DIR/rg" ]; then
    echo "📦 [5/5] 正在下载 ripgrep (高速代码搜索工具)..."
    RG_VER="14.1.1"
    RG_TAR="ripgrep-${RG_VER}-${RG_ARCH}-${RG_OS}.tar.gz"
    RG_URL="https://github.com/BurntSushi/ripgrep/releases/download/${RG_VER}/${RG_TAR}"
    TMP_RG="/tmp/${RG_TAR}"

    curl -fsSL "$RG_URL" -o "$TMP_RG"
    rm -rf "$RG_DIR"
    mkdir -p "$RG_DIR"
    tar -xzf "$TMP_RG" -C "$RG_DIR" --strip-components=1
    chmod +x "$RG_DIR/rg"
    rm -f "$TMP_RG"
    echo "    ✓ ripgrep (rg) 部署完成"
else
    echo "    ✓ ripgrep 已就绪"
fi

# ==============================================================================
# 8. 组装本套件沙盒内部垫片 (置于 .runtime/bin)
# ==============================================================================
echo "🔗 正在组装套件内部垫片与符号链接..."

# (1) node 垫片：锁定本地私有 node_modules，原生支持运行 TS
cat << EOF > "$RUNTIME_BIN/node"
#!/usr/bin/env bash
export NODE_PATH="$RUNTIME_DIR/node_modules:\$NODE_PATH"
export NODE_OPTIONS="--experimental-strip-types --no-warnings \$NODE_OPTIONS"
exec "$NODE_DIR/bin/node" "\$@"
EOF
chmod +x "$RUNTIME_BIN/node"

# (2) npm 垫片：强制将依赖与缓存安装在本套件 .runtime 目录内
cat << EOF > "$RUNTIME_BIN/npm"
#!/usr/bin/env bash
export npm_config_prefix="$RUNTIME_DIR"
export npm_config_cache="$RUNTIME_DIR/.npm-cache"
if [ "\$1" = "install" ] || [ "\$1" = "i" ] || [ "\$1" = "add" ]; then
    exec "$NODE_DIR/bin/npm" --prefix "$RUNTIME_DIR" "\$@"
else
    exec "$NODE_DIR/bin/npm" "\$@"
fi
EOF
chmod +x "$RUNTIME_BIN/npm"

# (3) npx 垫片
cat << EOF > "$RUNTIME_BIN/npx"
#!/usr/bin/env bash
export NODE_PATH="$RUNTIME_DIR/node_modules:\$NODE_PATH"
export npm_config_prefix="$RUNTIME_DIR"
export npm_config_cache="$RUNTIME_DIR/.npm-cache"
exec "$NODE_DIR/bin/npx" "\$@"
EOF
chmod +x "$RUNTIME_BIN/npx"

# (4) 链接其它单文件工具
ln -sf "$UV_DIR/uv" "$RUNTIME_BIN/uv"
ln -sf "$UV_DIR/uvx" "$RUNTIME_BIN/uvx"
ln -sf "$BUN_DIR/bun" "$RUNTIME_BIN/bun"
ln -sf "$RG_DIR/rg" "$RUNTIME_BIN/rg"
ln -sf "$PYTHON_EXEC" "$RUNTIME_BIN/python3"
ln -sf "$PYTHON_EXEC" "$RUNTIME_BIN/python"

echo ""
echo "=========================================================="
echo "🎉 [Skills Runtime] 独立运行时已就绪！"
echo "=========================================================="
echo "沙盒可执行文件存放目录: $RUNTIME_BIN"
echo "支持的引擎:"
echo "  • Node.js  (TS 运行时 + 私有 npm 依赖隔离)"
echo "  • Bun      (单文件 JS/TS 引擎)"
echo "  • uv       (Python 包管理与环境隔离)"
echo "  • Python 3 (独立运行时)"
echo "  • ripgrep  (代码检索工具 rg)"
echo "=========================================================="
