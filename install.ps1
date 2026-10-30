# ==============================================================================
# skill-boss 一键无感安装脚本 (Windows PowerShell)
#
# 特性：
# 1. 零手动赋权：自动生成 .cmd 批处理包装器，开箱即用；
# 2. 自动配置 PATH：自动将 %USERPROFILE%\.local\bin 写入当前用户环境变量，无需手动设置；
# 3. 免管理员权限：仅配置当前用户环境，不弹 UAC，不污染全局系统。
# ==============================================================================
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$UserBinDir = Join-Path $env:USERPROFILE ".local\bin"
$CmdWrapper = Join-Path $UserBinDir "skill-boss.cmd"
$PythonScript = Join-Path $RepoRoot "bin\skill-boss"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 [skill-boss] 正在安装个人 Skill 治理框架..." -ForegroundColor Cyan
Write-Host "=================================================="

# 1. 创建用户级 bin 目录
if (-not (Test-Path $UserBinDir)) {
    New-Item -ItemType Directory -Path $UserBinDir | Out-Null
}

# 2. 生成批处理包装器（显式调用 python 执行，免疫文件属性问题）
$WrapperContent = @"
@echo off
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "$PythonScript" %*
) else (
    py "$PythonScript" %*
)
"@

Set-Content -Path $CmdWrapper -Value $WrapperContent -Encoding ASCII
Write-Host "✓ 已生成 Windows 执行代理: $CmdWrapper" -ForegroundColor Green

# 3. 自动检测并写入用户环境变量 PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$Paths = $UserPath -split ';'

if ($Paths -notcontains $UserBinDir) {
    $NewPath = if ([string]::IsNullOrWhiteSpace($UserPath)) { $UserBinDir } else { "$UserPath;$UserBinDir" }
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "✓ 已自动将 $UserBinDir 添加至当前用户的 PATH 环境变量中。" -ForegroundColor Green
    Write-Host "💡 提示: 环境变量已自动配置！新打开的终端窗口可直接输入 skill-boss 使用。" -ForegroundColor Yellow
} else {
    Write-Host "✓ 环境变量已就绪: $UserBinDir 已在当前用户的 PATH 中。" -ForegroundColor Green
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎉 安装完成！你可以在新终端窗口直接输入: skill-boss --help" -ForegroundColor Cyan
Write-Host "=================================================="
