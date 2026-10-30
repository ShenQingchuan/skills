---
name: skills-router
description: 技能路由器，当需要调用技能时先用此技能查找。
---

# Skills Router

当需要调用技能时：

1. **查阅技能树**：执行 `skill-boss list-skills`（若终端尚未加载 PATH，可执行 `~/.local/bin/skill-boss list-skills`，或 `python3 <本技能目录>/scripts/list_skills.py` ）查看每个技能的一句话描述与入口路径。
2. **定位技能**：按描述选出最匹配的 1 个；确有互补需要时最多再加 1 个（例如「架构规约」配「API 参考」）。
3. **按需装载**：只读取选中技能目录下的 `SKILL.md`。其中若指向 `references/`、`reference/` 或 `scripts/`，再逐层按需取用。

不要预加载无关技能，也不要一次性读完所有技能。
