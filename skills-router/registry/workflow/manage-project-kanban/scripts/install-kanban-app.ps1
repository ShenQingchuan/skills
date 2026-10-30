# ==============================================================================
# install-kanban-app.ps1
# 项目任务看板一键安装脚本 (Windows PowerShell)
# 用法:
#   powershell -ExecutionPolicy Bypass -File "$HOME\.agents\skills\skills-router\registry\workflow\manage-project-kanban\scripts\install-kanban-app.ps1" [target_dir]
# ==============================================================================
param(
  [string]$TargetDir = "."
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VendorAppDir = Join-Path (Split-Path -Parent $ScriptDir) "assets\kanban-app"

if (-not (Test-Path $VendorAppDir)) {
  Write-Error "❌ 错误: 未找到看板应用模版源目录: $VendorAppDir"
  exit 1
}

$ResolvedTarget = Resolve-Path -Path $TargetDir -ErrorAction SilentlyContinue
if (-not $ResolvedTarget) {
  New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
  $ResolvedTarget = (Resolve-Path -Path $TargetDir).Path
} else {
  $ResolvedTarget = $ResolvedTarget.Path
}

Write-Host "📦 正在向目标目录安装看板应用: $ResolvedTarget"

Copy-Item -Path "$VendorAppDir\kanban-style.css" -Destination "$ResolvedTarget\" -Force
Copy-Item -Path "$VendorAppDir\kanban-app.js" -Destination "$ResolvedTarget\" -Force

$KanbanHtml = Join-Path $ResolvedTarget "kanban.html"
if (Test-Path $KanbanHtml) {
  Write-Host "ℹ️  $KanbanHtml 已存在，已保留现有任务数据并更新配套引擎文件。"
} else {
  Copy-Item -Path "$VendorAppDir\kanban.html" -Destination "$ResolvedTarget\" -Force
  Write-Host "✓ 已生成看板页面: $KanbanHtml"
}

$HistoryMd = Join-Path $ResolvedTarget "history.md"
if (-not (Test-Path $HistoryMd)) {
  $Template = @"
# 项目任务历史归档

本项目所有通过人类验收（Accepted）的任务均会从实时看板中移出，按时间顺序沉淀于此。

---
"@
  Set-Content -Path $HistoryMd -Value $Template -Encoding UTF8
  Write-Host "✓ 已初始化归档文件: $HistoryMd"
} else {
  Write-Host "ℹ️  $HistoryMd 已存在，无需重复创建。"
}

Write-Host ""
Write-Host "🎉 看板安装就绪！"
Write-Host ""
Write-Host "启动本地实时画板服务推荐命令:"
Write-Host "  & `"`$HOME\.agents\skills\.runtime\bin\bun.exe`" x vite --port 5173"
Write-Host "浏览器访问入口:"
Write-Host "  http://localhost:5173/kanban.html"
Write-Host ""
