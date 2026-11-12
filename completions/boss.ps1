# boss CLI 的 PowerShell 原生命令补全。
$BossArgumentCompleter = {
    param($wordToComplete, $commandAst, $cursorPosition)

    $elements = @($commandAst.CommandElements | ForEach-Object { $_.Extent.Text })
    $command = if ($elements.Count -ge 2) { $elements[1] } else { "" }
    $isTopLevel = $elements.Count -eq 1 -or ($elements.Count -eq 2 -and $wordToComplete -ne "")
    $candidates = @()

    if ($isTopLevel) {
        if ($wordToComplete.StartsWith("-")) {
            $candidates = @("-h", "--help")
        } else {
            $candidates = @("kanban", "code", "list-skills", "search-skills", "sync-skills", "setup-runtime", "bun", "uv", "python", "node", "npm")
        }
    } else {
        switch ($command) {
            { $_ -in @("kanban", "code") } {
                $candidates = @("stop", "-p", "--port", "-h", "--help")
            }
            "list-skills" {
                $candidates = @(& boss _complete skill-dirs $wordToComplete 2>$null)
            }
            "search-skills" {
                $candidates = @("--limit", "-h", "--help")
            }
            "sync-skills" {
                $candidates = @("--check", "-h", "--help")
            }
            "setup-runtime" {
                $candidates = @("-s", "--status", "-h", "--help")
            }
        }
    }

    $candidates |
        Where-Object { $_ -and $_.StartsWith($wordToComplete, [System.StringComparison]::OrdinalIgnoreCase) } |
        Sort-Object -Unique |
        ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)
        }
}

# 同一终端重复加载时不重复注册补全器。
if (-not $global:BossCompletionIsRegistered) {
    Register-ArgumentCompleter -Native -CommandName boss -ScriptBlock $BossArgumentCompleter
    $global:BossCompletionIsRegistered = $true
}
