---
name: skills-router
description: 技能路由器，当需要调用技能时先用此技能查找。
---

# Skills Router

当需要调用技能时：

1. **定位技能**：任务明确时执行 `boss search-skills "<能力关键词>"`（支持多个关键词，如 `"vue testing"`）；不明确时执行 `boss list-skills` 查看顶层分类，再用 `boss list-skills <分类路径>` 完整展开。若 `boss` 不在 PATH，改用 `~/.local/bin/boss`。
2. **选择技能**：按描述选出最匹配的 1 个；确有互补需要时最多再加 1 个（例如「架构规约」配「API 参考」）。
3. **按需装载**：只读取搜索或列表为选中技能输出的真实入口 `SKILL.md`（绝对路径，可直接读取）。其中若指向 `references/`、`reference/` 或 `scripts/`，再逐层按需取用。

不要预加载无关技能，也不要一次性读完所有技能。
