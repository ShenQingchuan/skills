# ==============================================================================
# boss 一键无感安装脚本 (Windows PowerShell)
#
# 特性：
# 1. 零手动赋权：自动生成 .cmd 批处理包装器，开箱即用；
# 2. 自动配置 PATH：自动将 %USERPROFILE%\.local\bin 写入当前用户环境变量，无需手动设置；
# 3. 免管理员权限：仅配置当前用户环境，不弹 UAC，不污染全局系统；
# 4. 自动准备 Python：优先使用系统 Python 3，没有时通过 uv 安装独立 Python 3.12；
# 5. 自动同步技能：安装末尾执行 sync-skills，首次安装即可得到完整技能库。
# ==============================================================================
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$UserBinDir = Join-Path $env:USERPROFILE ".local\bin"
$CmdWrapper = Join-Path $UserBinDir "boss.cmd"
$PythonScript = Join-Path $RepoRoot "bin\boss"
$CompletionDir = Join-Path $env:USERPROFILE ".local\share\boss\completions"
$PowerShellCompletion = Join-Path $CompletionDir "boss.ps1"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 [boss] 正在安装个人 Skill 治理框架..." -ForegroundColor Cyan
Write-Host "=================================================="

# 初始化本机配置与目录；重装时绝不覆盖已有配置
$ConfigFile = Join-Path $RepoRoot "config.json"
$ConfigExample = Join-Path $RepoRoot "config.example.json"
$SyncedDir = Join-Path $RepoRoot "registry\.synced"
$ProfilesDir = Join-Path $RepoRoot "profiles"
New-Item -ItemType Directory -Path $SyncedDir -Force | Out-Null
New-Item -ItemType Directory -Path $ProfilesDir -Force | Out-Null
if (-not (Test-Path $ConfigFile)) {
    Copy-Item -Path $ConfigExample -Destination $ConfigFile
    Write-Host "✓ 已创建本机配置: $ConfigFile" -ForegroundColor Green
}

# 1. 创建用户级 bin 目录
if (-not (Test-Path $UserBinDir)) {
    New-Item -ItemType Directory -Path $UserBinDir | Out-Null
}

# 2. 准备 Python 并生成批处理包装器，重装时复用已有运行时
$PythonInstaller = Join-Path $RepoRoot "bin\install-python.ps1"
$PythonExecutable = & $PythonInstaller -RootDir $RepoRoot
if ([string]::IsNullOrWhiteSpace($PythonExecutable) -or -not (Test-Path "$PythonExecutable")) {
    throw "未能准备 Python 运行环境。"
}

$WrapperContent = @"
@echo off
"$PythonExecutable" "$PythonScript" %*
exit /b %ERRORLEVEL%
"@

Set-Content -Path $CmdWrapper -Value $WrapperContent -Encoding ASCII

# 每次覆盖补全脚本本体，重装即可升级到最新版本
if (-not (Test-Path $CompletionDir)) {
    New-Item -ItemType Directory -Path $CompletionDir -Force | Out-Null
}
Copy-Item -Path (Join-Path $RepoRoot "completions\boss.ps1") -Destination $PowerShellCompletion -Force

# 清理旧版 skill-boss 命令（如果存在）
$LegacyCmdWrapper = Join-Path $UserBinDir "skill-boss.cmd"
if (Test-Path $LegacyCmdWrapper) {
    Remove-Item -Force $LegacyCmdWrapper
}

Write-Host "✓ 已生成 Windows 执行代理: $CmdWrapper" -ForegroundColor Green

# 3. 自动检测并写入用户环境变量 PATH，兼容已有条目的大小写和末尾斜杠差异
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$NormalizedUserBinDir = $UserBinDir.TrimEnd('\')
$ExistingBinPath = @($UserPath -split ';' | Where-Object {
    -not [string]::IsNullOrWhiteSpace($_) -and $_.Trim().TrimEnd('\') -ieq $NormalizedUserBinDir
})

if ($ExistingBinPath.Count -eq 0) {
    $NewPath = if ([string]::IsNullOrWhiteSpace($UserPath)) { $UserBinDir } else { "$UserPath;$UserBinDir" }
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "✓ 已自动将 $UserBinDir 添加至当前用户的 PATH 环境变量中。" -ForegroundColor Green
    Write-Host "💡 提示: 环境变量已自动配置！新打开的终端窗口可直接输入 boss 使用。" -ForegroundColor Yellow
} else {
    Write-Host "✓ 环境变量已就绪: $UserBinDir 已在当前用户的 PATH 中。" -ForegroundColor Green
}

# 4. 向 PowerShell Profile 添加唯一的一行加载配置
$ProfilePath = $PROFILE.CurrentUserCurrentHost
$ProfileDir = Split-Path -Parent $ProfilePath
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}
if (-not (Test-Path $ProfilePath)) {
    New-Item -ItemType File -Path $ProfilePath -Force | Out-Null
}

$EscapedCompletionPath = $PowerShellCompletion.Replace("'", "''")
$CompletionSourceLine = "if (Test-Path -LiteralPath '$EscapedCompletionPath') { . '$EscapedCompletionPath' }"
$ProfileContent = Get-Content -Path $ProfilePath -Raw
if ([string]::IsNullOrEmpty($ProfileContent) -or -not $ProfileContent.Contains($CompletionSourceLine)) {
    Add-Content -Path $ProfilePath -Value "`n# boss CLI PowerShell Tab completion`n$CompletionSourceLine" -Encoding UTF8
}
Write-Host "✓ 已配置 PowerShell Tab 自动补全: $ProfilePath" -ForegroundColor Green

# 首次安装直接拉齐技能库；重复安装时同步脚本会按指纹幂等处理
Write-Host ""
Write-Host "🔄 正在同步技能库..." -ForegroundColor Cyan
& $CmdWrapper sync-skills
if ($LASTEXITCODE -ne 0) {
    throw "技能同步失败。请检查网络后重新运行 install.ps1，或手动执行 boss sync-skills。"
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎉 安装完成！你可以在新终端窗口直接输入: boss --help" -ForegroundColor Cyan
Write-Host "=================================================="

