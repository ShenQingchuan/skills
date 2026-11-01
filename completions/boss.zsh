#compdef boss

# boss CLI 的 zsh 补全：子命令、选项和技能分类目录。
_boss_completion() {
  local cur prev command
  local -a commands options skill_dirs actions
  cur="${words[CURRENT]}"
  prev="${words[CURRENT - 1]}"
  command="${words[2]}"

  if (( CURRENT == 2 )); then
    if [[ "$cur" == -* ]]; then
      options=('-h:查看帮助' '--help:查看帮助')
      _describe 'boss option' options
    else
      commands=(
        'kanban:启动或停止项目任务看板'
        'code:启动或停止网页代码编辑器'
        'list-skills:查看技能树'
        'sync-skills:同步第三方技能'
        'setup-runtime:安装或检查独立运行环境'
      )
      _describe 'boss command' commands
    fi
    return
  fi

  case "$command" in
    kanban|code)
      if [[ "$prev" == "-p" || "$prev" == "--port" ]]; then
        return
      fi
      if [[ "$cur" == -* ]]; then
        options=('-p:指定端口' '--port:指定端口' '-h:查看帮助' '--help:查看帮助')
        _describe 'command option' options
      else
        actions=('stop:停止服务')
        _describe 'action' actions
        _files -/
      fi
      ;;
    list-skills)
      skill_dirs=("${(@f)$(command boss _complete skill-dirs "$cur" 2>/dev/null)}")
      (( ${#skill_dirs} )) && _describe 'skill directory' skill_dirs
      ;;
    sync-skills)
      options=('--check:仅检查更新，不写入文件' '-h:查看帮助' '--help:查看帮助')
      _describe 'command option' options
      ;;
    setup-runtime)
      options=('-s:查看运行环境状态' '--status:查看运行环境状态' '-h:查看帮助' '--help:查看帮助')
      _describe 'command option' options
      ;;
  esac
}

# 直接 source 时也能工作，不要求用户额外调整 fpath。
if ! typeset -f compdef >/dev/null 2>&1; then
  autoload -Uz compinit
  compinit
fi
compdef _boss_completion boss
