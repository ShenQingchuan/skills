# 为 boss Windows 安装器寻找 Python 3；系统没有时，通过独立 uv 自动安装。
param (
    [Parameter(Mandatory = $true)]
    [string]$RootDir
)

$ErrorActionPreference = "Stop"

function Resolve-SystemPython {
    $PythonCommand = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        try {
            $Resolved = & $PythonCommand.Source -c "import sys; print(sys.executable if sys.version_info >= (3, 10) else '')" 2>$null
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($Resolved) -and (Test-Path "$Resolved")) {
                return "$Resolved".Trim()
            }
        } catch {}
    }

    $PyLauncher = Get-Command py -CommandType Application -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        try {
            $Resolved = & $PyLauncher.Source -3 -c "import sys; print(sys.executable if sys.version_info >= (3, 10) else '')" 2>$null
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($Resolved) -and (Test-Path "$Resolved")) {
                return "$Resolved".Trim()
            }
        } catch {}
    }

    return $null
}

$SystemPython = Resolve-SystemPython
if (-not [string]::IsNullOrWhiteSpace($SystemPython)) {
    Write-Host "✓ 已检测到系统 Python: $SystemPython" -ForegroundColor Green
    return $SystemPython
}

Write-Host "ℹ️ 未检测到 Python 3，将使用 uv 自动安装独立运行时..." -ForegroundColor Yellow

$RuntimeDir = Join-Path $RootDir ".runtime"
$UvDir = Join-Path $RuntimeDir "uv"
$UvExe = Join-Path $UvDir "uv.exe"
$PythonInstallDir = Join-Path $RuntimeDir "python"
$UvCacheDir = Join-Path $RuntimeDir ".uv-cache"

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $PythonInstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $UvCacheDir | Out-Null
$env:UV_PYTHON_INSTALL_DIR = $PythonInstallDir
$env:UV_CACHE_DIR = $UvCacheDir

if (-not (Test-Path $UvExe)) {
    if (-not [System.Environment]::Is64BitOperatingSystem) {
        throw "32 位 Windows 不受支持，请手动安装 64 位 Python 3 后重新运行安装器。"
    }

    $UvArch = if ($env:PROCESSOR_ARCHITECTURE -match "ARM64") { "aarch64" } else { "x86_64" }
    $UvZip = "uv-$UvArch-pc-windows-msvc.zip"
    $UvUrl = "https://github.com/astral-sh/uv/releases/latest/download/$UvZip"
    $TempUv = Join-Path $env:TEMP $UvZip

    Write-Host "📦 正在下载独立 uv..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $UvUrl -OutFile $TempUv -UseBasicParsing
    New-Item -ItemType Directory -Force -Path $UvDir | Out-Null
    Expand-Archive -Path $TempUv -DestinationPath $UvDir -Force
    Remove-Item -Force $TempUv
}

if (-not (Test-Path $UvExe)) {
    throw "uv 安装失败，无法自动准备 Python。"
}

$PythonExecutable = ""
try {
    $PythonExecutable = & $UvExe python find 3.12 2>$null
} catch {}

if ([string]::IsNullOrWhiteSpace($PythonExecutable) -or -not (Test-Path "$PythonExecutable")) {
    Write-Host "📦 正在下载独立 Python 3.12..." -ForegroundColor Yellow
    & $UvExe python install 3.12 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.12 自动安装失败，请检查网络后重新运行安装器。"
    }
    $PythonExecutable = & $UvExe python find 3.12
}

if ([string]::IsNullOrWhiteSpace($PythonExecutable) -or -not (Test-Path "$PythonExecutable")) {
    throw "找不到可用的 Python 3.12，请手动安装 Python 3 后重新运行安装器。"
}

$PythonExecutable = "$PythonExecutable".Trim()
Write-Host "✓ Python 已就绪: $PythonExecutable" -ForegroundColor Green
return $PythonExecutable
