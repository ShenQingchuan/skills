# ==============================================================================
# Skills Suite Runtime Injector (Windows PowerShell)
#
# 为本 skills 套件提供独立、纯净、开箱即用的运行引擎：
# 1. 0 外部依赖：仅使用系统底层 Invoke-WebRequest 与 Expand-Archive，自动下载部署官方绿色版：
#    - Node.js (最新 LTS, 内置 npm, 原生直接支持执行 TS)
#    - Bun (单文件极速 JS/TS 引擎)
#    - uv (现代 Python 包与工具管理器) & Python 3.12 独立运行时
#    - ripgrep (极速文本检索工具 rg)
# 2. 私有沙盒：所有引擎与产物均严格收拢在 .runtime\ 目录下，绝不污染全局系统；
# 3. 依赖隔离：本套件所需的 npm 依赖全部安装于 .runtime\node_modules，不脏宿主环境。
# ==============================================================================

param (
    [switch]$Status,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$ToolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ToolsDir
$RuntimeDir = Join-Path $RootDir ".runtime"
$RuntimeBin = Join-Path $RuntimeDir "bin"

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeBin | Out-Null

if ($Help) {
    Write-Host "用法: powershell -ExecutionPolicy Bypass -File .\tools\setup-runtime.ps1 [选项]"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  (无参数)      为本 skills 套件下载并配置全套绿色运行时引擎"
    Write-Host "  -Status       查看当前沙盒运行时的就绪状态及版本"
    Write-Host "  -Help         显示帮助信息"
    exit 0
}

if ($Status) {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "🔍 [Skills Runtime 状态检测]" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "沙盒根目录: $RuntimeDir"
    Write-Host "引擎路径:   $RuntimeBin"
    Write-Host "----------------------------------------------------------"
    $NodeCmd = Join-Path $RuntimeBin "node.cmd"
    if (Test-Path $NodeCmd) { Write-Host "✓ Node.js:  $(& $NodeCmd -v)" } else { Write-Host "✗ Node.js:  未就绪" }
    $BunExe = Join-Path $RuntimeBin "bun.exe"
    if (Test-Path $BunExe) { Write-Host "✓ Bun:      $(& $BunExe -v)" } else { Write-Host "✗ Bun:      未就绪" }
    $UvExe = Join-Path $RuntimeBin "uv.exe"
    if (Test-Path $UvExe) { Write-Host "✓ uv:       $((& $UvExe --version) -split ' ')[0..1] -join ' '" } else { Write-Host "✗ uv:       未就绪" }
    $PyCmd = Join-Path $RuntimeBin "python3.cmd"
    if (Test-Path $PyCmd) { Write-Host "✓ Python:   $(& $PyCmd --version)" } else { Write-Host "✗ Python:   未就绪" }
    $RgExe = Join-Path $RuntimeBin "rg.exe"
    if (Test-Path $RgExe) { Write-Host "✓ ripgrep:  $((& $RgExe --version)[0])" } else { Write-Host "✗ ripgrep:  未就绪" }
    Write-Host "==========================================================" -ForegroundColor Cyan
    exit 0
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🚀 [Skills Runtime] 正在为本套件配置独立运行时引擎 (Windows)..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. 识别架构
$Arch = if ([System.Environment]::Is64BitOperatingSystem) { "x64" } else { "x86" }
if ($env:PROCESSOR_ARCHITECTURE -match "ARM64") { $Arch = "arm64" }

Write-Host "💻 识别到系统架构: Windows ($Arch)"

# 2. 准备私有 npm 沙盒配置
$PkgJson = Join-Path $RuntimeDir "package.json"
if (-not (Test-Path $PkgJson)) {
    '{"name": "skills-runtime-sandbox", "version": "1.0.0", "private": true, "type": "module"}' | Out-File -Encoding utf8 $PkgJson
}
$RuntimeNodeModules = Join-Path $RuntimeDir "node_modules"
New-Item -ItemType Directory -Force -Path $RuntimeNodeModules | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $RuntimeDir ".npm-cache") | Out-Null

# ==============================================================================
# 3. 注入 Node.js LTS
# ==============================================================================
$NodeDir = Join-Path $RuntimeDir "node"
$NodeExe = Join-Path $NodeDir "node.exe"

if (-not (Test-Path $NodeExe)) {
    Write-Host "📦 [1/5] 正在下载 Node.js 官方最新 LTS 绿色运行时..." -ForegroundColor Yellow
    $NodeVer = "v22.14.0"
    try {
        $Tab = (Invoke-WebRequest -Uri "https://nodejs.org/dist/index.tab" -UseBasicParsing).Content
        $Lines = $Tab -split "`n"
        foreach ($Line in $Lines) {
            $Cols = $Line -split "`t"
            if ($Cols.Count -ge 10 -and $Cols[9] -ne "-" -and $Cols[9] -ne "" -and $Cols[9] -ne "lts") {
                $NodeVer = $Cols[0]
                break
            }
        }
    } catch {
        Write-Host "    -> 查询官方索引失败，使用稳定默认版本: $NodeVer"
    }

    $ArchiveName = "node-$NodeVer-win-$Arch.zip"
    $DownloadUrl = "https://nodejs.org/dist/$NodeVer/$ArchiveName"
    $TempArchive = Join-Path $env:TEMP $ArchiveName

    Write-Host "    -> 正在下载: $DownloadUrl"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempArchive -UseBasicParsing

    if (Test-Path $NodeDir) { Remove-Item -Recurse -Force $NodeDir }
    Expand-Archive -Path $TempArchive -DestinationPath $RuntimeDir -Force
    Rename-Item -Path (Join-Path $RuntimeDir "node-$NodeVer-win-$Arch") -NewName "node"
    Remove-Item -Force $TempArchive
    Write-Host "    ✓ Node.js ($NodeVer) 部署完成" -ForegroundColor Green
} else {
    Write-Host "    ✓ Node.js 已就绪" -ForegroundColor Green
}

# ==============================================================================
# 4. 注入 uv
# ==============================================================================
$UvDir = Join-Path $RuntimeDir "uv"
$UvExe = Join-Path $UvDir "uv.exe"

if (-not (Test-Path $UvExe)) {
    Write-Host "📦 [2/5] 正在下载 uv (现代 Python 管理器)..." -ForegroundColor Yellow
    $UvZip = "uv-x86_64-pc-windows-msvc.zip"
    $UvUrl = "https://github.com/astral-sh/uv/releases/latest/download/$UvZip"
    $TempUv = Join-Path $env:TEMP $UvZip

    Invoke-WebRequest -Uri $UvUrl -OutFile $TempUv -UseBasicParsing
    New-Item -ItemType Directory -Force -Path $UvDir | Out-Null
    Expand-Archive -Path $TempUv -DestinationPath $UvDir -Force
    Remove-Item -Force $TempUv
    Write-Host "    ✓ uv 部署完成" -ForegroundColor Green
} else {
    Write-Host "    ✓ uv 已就绪" -ForegroundColor Green
}

# ==============================================================================
# 5. 注入 Python 3.12 独立运行时
# ==============================================================================
Write-Host "📦 [3/5] 正在确认独立 Python 3 运行时..." -ForegroundColor Yellow
$PythonExec = ""
try {
    $PythonExec = & $UvExe python find 3.12 2>$null
} catch {}

if ([string]::IsNullOrWhiteSpace($PythonExec) -or -not (Test-Path $PythonExec)) {
    Write-Host "    -> 正在自动下载独立 Python 3.12 解释器..."
    & $UvExe python install 3.12
    $PythonExec = & $UvExe python find 3.12
}
Write-Host "    ✓ Python 环境就绪: $PythonExec" -ForegroundColor Green

# ==============================================================================
# 6. 注入 Bun
# ==============================================================================
$BunDir = Join-Path $RuntimeDir "bun"
$BunExe = Join-Path $BunDir "bun.exe"

if (-not (Test-Path $BunExe)) {
    Write-Host "📦 [4/5] 正在下载 Bun (单文件 JS/TS 引擎)..." -ForegroundColor Yellow
    $BunZip = "bun-windows-x64.zip"
    $BunUrl = "https://github.com/oven-sh/bun/releases/latest/download/$BunZip"
    $TempBun = Join-Path $env:TEMP $BunZip

    Invoke-WebRequest -Uri $BunUrl -OutFile $TempBun -UseBasicParsing
    $TempExtract = Join-Path $env:TEMP "bun_temp"
    if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
    Expand-Archive -Path $TempBun -DestinationPath $TempExtract -Force
    New-Item -ItemType Directory -Force -Path $BunDir | Out-Null
    Move-Item -Path (Join-Path $TempExtract "bun-windows-x64\bun.exe") -Destination $BunExe -Force
    Remove-Item -Recurse -Force $TempExtract
    Remove-Item -Force $TempBun
    Write-Host "    ✓ Bun 部署完成" -ForegroundColor Green
} else {
    Write-Host "    ✓ Bun 已就绪" -ForegroundColor Green
}

# ==============================================================================
# 7. 注入 ripgrep
# ==============================================================================
$RgDir = Join-Path $RuntimeDir "ripgrep"
$RgExe = Join-Path $RgDir "rg.exe"

if (-not (Test-Path $RgExe)) {
    Write-Host "📦 [5/5] 正在下载 ripgrep (代码检索工具)..." -ForegroundColor Yellow
    $RgZip = "ripgrep-14.1.1-x86_64-pc-windows-msvc.zip"
    $RgUrl = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/$RgZip"
    $TempRg = Join-Path $env:TEMP $RgZip

    Invoke-WebRequest -Uri $RgUrl -OutFile $TempRg -UseBasicParsing
    $TempRgExtract = Join-Path $env:TEMP "rg_temp"
    if (Test-Path $TempRgExtract) { Remove-Item -Recurse -Force $TempRgExtract }
    Expand-Archive -Path $TempRg -DestinationPath $TempRgExtract -Force
    New-Item -ItemType Directory -Force -Path $RgDir | Out-Null
    $FoundRg = Get-ChildItem -Path $TempRgExtract -Filter "rg.exe" -Recurse | Select-Object -First 1
    Move-Item -Path $FoundRg.FullName -Destination $RgExe -Force
    Remove-Item -Recurse -Force $TempRgExtract
    Remove-Item -Force $TempRg
    Write-Host "    ✓ ripgrep (rg) 部署完成" -ForegroundColor Green
} else {
    Write-Host "    ✓ ripgrep 已就绪" -ForegroundColor Green
}

# ==============================================================================
# 8. 组装套件内部垫片 (置于 .runtime\bin)
# ==============================================================================
Write-Host "🔗 正在组装套件内部垫片与符号链接..." -ForegroundColor Cyan

# 部署 node.cmd
$NodeCmdContent = @"
@echo off
set "RUNTIME_ROOT=$RuntimeDir"
set "NODE_PATH=%RUNTIME_ROOT%\node_modules;%NODE_PATH%"
set "NODE_OPTIONS=--experimental-strip-types --no-warnings %NODE_OPTIONS%"
"%RUNTIME_ROOT%\node\node.exe" %*
"@
$NodeCmdContent | Out-File -Encoding ascii (Join-Path $RuntimeBin "node.cmd")

# 部署 npm.cmd
$NpmCmdContent = @"
@echo off
set "RUNTIME_ROOT=$RuntimeDir"
set "npm_config_prefix=%RUNTIME_ROOT%"
set "npm_config_cache=%RUNTIME_ROOT%\.npm-cache"
if "%1"=="install" goto do_install
if "%1"=="i" goto do_install
if "%1"=="add" goto do_install
"%RUNTIME_ROOT%\node\npm.cmd" %*
goto end
:do_install
"%RUNTIME_ROOT%\node\npm.cmd" --prefix "%RUNTIME_ROOT%" %*
:end
"@
$NpmCmdContent | Out-File -Encoding ascii (Join-Path $RuntimeBin "npm.cmd")

# 部署 npx.cmd
$NpxCmdContent = @"
@echo off
set "RUNTIME_ROOT=$RuntimeDir"
set "NODE_PATH=%RUNTIME_ROOT%\node_modules;%NODE_PATH%"
set "npm_config_prefix=%RUNTIME_ROOT%"
set "npm_config_cache=%RUNTIME_ROOT%\.npm-cache"
"%RUNTIME_ROOT%\node\npx.cmd" %*
"@
$NpxCmdContent | Out-File -Encoding ascii (Join-Path $RuntimeBin "npx.cmd")

# 复制其它独立可执行程序至 .runtime\bin
Copy-Item -Path $UvExe -Destination (Join-Path $RuntimeBin "uv.exe") -Force
Copy-Item -Path (Join-Path $UvDir "uvx.exe") -Destination (Join-Path $RuntimeBin "uvx.exe") -Force
Copy-Item -Path $BunExe -Destination (Join-Path $RuntimeBin "bun.exe") -Force
Copy-Item -Path $RgExe -Destination (Join-Path $RuntimeBin "rg.exe") -Force

# 部署 python 软垫片
$PyCmdContent = @"
@echo off
"$PythonExec" %*
"@
$PyCmdContent | Out-File -Encoding ascii (Join-Path $RuntimeBin "python.cmd")
$PyCmdContent | Out-File -Encoding ascii (Join-Path $RuntimeBin "python3.cmd")

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "🎉 [Skills Runtime] 独立运行时已就绪！" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "沙盒可执行文件存放目录: $RuntimeBin"
Write-Host "支持的引擎:"
Write-Host "  • Node.js  (TS 运行时 + 私有 npm 依赖隔离)"
Write-Host "  • Bun      (单文件 JS/TS 引擎)"
Write-Host "  • uv       (Python 包管理与环境隔离)"
Write-Host "  • Python 3 (独立运行时)"
Write-Host "  • ripgrep  (代码检索工具 rg)"
Write-Host "==========================================================" -ForegroundColor Green
