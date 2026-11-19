# 从已有文档目录迁移

很多项目已经有自己的文档目录。迁移时按内容的性质归位，不按原目录名一刀切：同一个 `docs/` 里可能同时有规约、背景资料和过期计划。

## 先决定：搬走还是留在原处

- **搬到 `.agents/`**：内容主要供开发者和 Agent 阅读，没有对外发布。
- **留在原处**：内容是对外文档站的一部分（如 VitePress、Docusaurus、MkDocs 的源目录），或被外部网站、issue 大量链接。这类目录不搬，在 `.agents/docs/README.md` 或对应 spec 中写一行指向原路径即可，不要复制一份。

## 通用对应关系

| 原有内容 | 常见位置 | 迁移到 |
| :--- | :--- | :--- |
| 仍然有效的架构决策（ADR） | `docs/decisions/`、`docs/adr/`、`adr/` | 相关 spec 的「架构决策」小节；没有对应 spec 时，按主题新建 `.agents/specs/<topic>/` |
| 已被取代或否决的决策 | 同上 | 在取代它的 spec 里写一句「曾放弃 X，原因是 Y」；没有长期价值的直接删除 |
| 已落地的 RFC、设计文档、PRD | `docs/rfcs/`、`docs/design/`、`docs/prd/` | `.agents/specs/` |
| 尚未完成的实施方案、迁移计划、技术债清单 | `docs/plans/`、`MIGRATION.md`、`TECH_DEBT.md` | `.agents/engineering/` 的工程单元 |
| 编码规范、贡献约定、AI 规则文件 | `CONTRIBUTING.md` 中的规范部分、`.cursor/rules/`、`.github/copilot-instructions.md`、`.windsurfrules` | `.agents/rules/`；能由 linter 检查的写进 linter 配置 |
| 待办、路线图 | `TODO.md`、`ROADMAP.md` | 产品成果进 Kanban 或外部追踪系统，技术事项进 engineering |
| 背景资料、术语表、外部参考、会议结论 | `docs/notes/`、`docs/reference/` | `.agents/docs/` |
| 重复执行的操作手册 | `docs/runbooks/`、`scripts/README.md` | `.agents/skills/` |
| Agent 入口说明 | `CLAUDE.md`、`.cursorrules` 中的项目概况 | `AGENTS.md`，原 `CLAUDE.md` 改为只有一行 `@AGENTS.md` |

拆分时以内容为准：一份 ADR 里既有决策又有实施步骤，决策进 spec，步骤进 engineering。

## 必须同时更新互相引用

迁移和改链接放在同一次变更中完成，不留失效链接：

1. **迁移前列出引用**：对每个要移动的文件，在整个仓库中搜索它的路径和文件名，覆盖 Markdown 链接、`README.md`、`AGENTS.md`、代码注释、CI 配置、文档站配置（如侧边栏、导航）。
2. **用 `git mv` 移动**：保留文件历史。
3. **改写所有引用**：被移动文件之间的相对链接按新位置重新计算；ADR 编号等旧标识被别处引用时，在新文档中保留原编号，便于检索。
4. **验证**：再次搜索所有旧路径，结果必须为空；项目有链接检查工具时运行一次。
5. **清理旧目录**：确认迁空后删除，不留只写着「已迁移」的占位文件。原目录必须保留时，按上文「留在原处」处理。
