# boss CLI 的 Bash 补全：子命令、选项和技能分类目录。
_boss_completion() {
  local cur prev command line
  local commands="kanban code list-skills search-skills sync-skills setup-runtime bun uv python node npm"
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD - 1]}"
  command="${COMP_WORDS[1]}"

  if (( COMP_CWORD == 1 )); then
    if [[ "$cur" == -* ]]; then
      COMPREPLY=( $(compgen -W "-h --help" -- "$cur") )
    else
      COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
    fi
    return
  fi

  case "$command" in
    kanban|code)
      if [[ "$prev" == "-p" || "$prev" == "--port" ]]; then
        return
      fi
      if [[ "$cur" == -* ]]; then
        COMPREPLY=( $(compgen -W "-p --port -h --help" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "stop" -- "$cur") )
        while IFS= read -r line; do
          COMPREPLY+=("$line")
        done < <(compgen -d -- "$cur")
      fi
      ;;
    list-skills)
      while IFS= read -r line; do
        COMPREPLY+=("$line")
      done < <(command boss _complete skill-dirs "$cur" 2>/dev/null)
      ;;
    search-skills)
      if [[ "$prev" == "--limit" ]]; then
        return
      fi
      COMPREPLY=( $(compgen -W "--limit -h --help" -- "$cur") )
      ;;
    sync-skills)
      COMPREPLY=( $(compgen -W "--check -h --help" -- "$cur") )
      ;;
    setup-runtime)
      COMPREPLY=( $(compgen -W "-s --status -h --help" -- "$cur") )
      ;;
    bun|uv|python|node|npm)
      # 无候选时使用 Bash 默认补全，仍可方便地补全脚本路径。
      ;;

  esac
}

complete -o bashdefault -o default -F _boss_completion boss
