---
name: manage-project-kanban
description: 项目任务看板工具指南 - 教导 AI 如何在目标项目中从零初始化（Setup）基于 Mermaid 语法的项目任务看板，并在后续开发中持续读写维护任务流转与归档。
---

# manage-project-kanban 技能指南

本技能是一套面向软件项目的 **项目任务看板工具**。

它的核心职责有两个：
1. **给项目搭建看板（Setup）**：把基于 Mermaid 文本驱动的轻量无框看板安装到目标项目中，并拉起本地热重载预览；
2. **日常维护与生命周期管理（Manage）**：AI 在日常对话中自动接单、推进任务泳道流转，并在任务验收通过后**物理移出看板**，永久归档至历史记录。

---

## 零、 跨平台独立运行时调用规范

本技能配套的所有工具执行，严格依赖本 skills 仓库自带的沙箱运行时，不污染宿主全局环境：

- **标准基准路径**：`~/.agents/skills/.runtime/`
- **各操作系统与 Shell 执行对照**：

| 平台 / 环境 | 路径写法示例 | 说明 |
| :--- | :--- | :--- |
| **macOS / Linux (Bash/Zsh)** | `~/.agents/skills/.runtime/bin/bun` | Shell 会自动将 `~` 展开为当前用户主目录 |
| **Windows (PowerShell)** | `$HOME\.agents\skills\.runtime\bin\bun.exe` | PowerShell 中 `$HOME` 对应用户主目录 |
| **Windows (cmd.exe)** | `%USERPROFILE%\.agents\skills\.runtime\bin\bun.exe` | cmd 不支持 `~` 展开，必须使用 `%USERPROFILE%` 环境变量 |

> **提示**：AI 在向系统终端发送命令时，应根据当前宿主操作系统自动选取上述对应的执行路径。

---

## 一、 Setup：如何为项目从零初始化看板

当用户发出诸如“帮这个项目建个任务看板”、“用看板管理当前任务”、“初始化项目进度看板”等指令时，AI 首选使用一键安装脚本完成搭建：

### 方式 A：使用一键安装脚本（推荐）

AI 可直接在终端调用本技能配套的安装脚本，将 `kanban-app` vendor 资源一键部署到目标项目，并自动初始化 `kanban.html` 与 `history.md`：

- **macOS / Linux**：
  ```bash
  ~/.agents/skills/skills-router/registry/workflow/manage-project-kanban/scripts/install-kanban-app [目标目录，默认当前目录 .]
  ```
- **Windows (PowerShell)**：
  ```powershell
  powershell -ExecutionPolicy Bypass -File "$HOME\.agents\skills\skills-router\registry\workflow\manage-project-kanban\scripts\install-kanban-app.ps1" [目标目录，默认当前目录 .]
  ```

---

### 方式 B：手动复制 Vendor 应用资产

若无需使用脚本，AI 也可以直接复制独立封装的静态前端应用包：

- **应用模版目录**：
  `~/.agents/skills/skills-router/registry/workflow/manage-project-kanban/assets/kanban-app/`
- **核心文件说明**：
  1. `kanban.html`：画板入口，内嵌 Mermaid 纯文本数据源；
  2. `kanban-style.css`：Linear / Raycast 质感的暗黑/明亮自适应无框样式；
  3. `kanban-app.js`：看板驱动引擎（包含画板自适应渲染、缩放、卡片抽屉与国际化多语言支持）。
- **初始化归档**：
  在目标目录建立 `history.md`，用于存放未来所有验收移出的已完成卡片。

---

### 步骤：填充初始任务并拉起预览

安装就绪后：
1. 打开目标项目中的 `kanban.html`，定位到底部的 `<script type="text/mermaid" id="kanban-source">` 区块，根据项目现状填入初始卡片或保留四大标准泳道；
2. 启动本地轻量热重载预览服务器：
   - **macOS / Linux**：
     ```bash
     ~/.agents/skills/.runtime/bin/bun x vite --port 5173
     ```
   - **Windows (PowerShell)**：
     ```powershell
     & "$HOME\.agents\skills\.runtime\bin\bun.exe" x vite --port 5173
     ```
3. 在对话中引导用户：
   > “项目任务看板已安装完毕！可在浏览器中打开 `http://localhost:5173/kanban.html` 实时查看任务进展。后续任何任务变动，画板都会自动无感热重载刷新。”

---

## 二、 Manage：已有看板的项目如何日常维护

当项目已经存在 `kanban.html` 时，AI 的日常工作遵循以下四大核心原则与操作规范：

### 1. 核心设计哲学
- **待验收即是看板的终点**：实时看板只保留“正在流动”的任务，**坚决不在看板中堆积已完成（Done）卡片**，保持画板紧凑清爽；
- **验收通过必须物理移出**：一旦人类确认验收，AI 必须将该任务从 Mermaid 源码中**物理删除**，并转移归档至 `history.md`；
- **WIP 严格限制**：进行中泳道（In Progress）同时严格只允许有 **1 个** 任务，强迫聚焦，防止上下文发散。

---

### 2. 标准四大泳道定义

| 泳道 Key | 中文标签 | 英文标签 | 职责与准入准出规则 |
| :--- | :--- | :--- | :--- |
| `backlog` | **待处理** | Backlog | **任务池**：收集尚未细化的高层想法、临时待办事项或 Bug 报告；待方案明确后排期移入待开发。 |
| `todo` | **待开发** | Todo | **排期就绪**：方案清晰、优先级已定（如 `@{ priority: "High" }`），随时可以接单。 |
| `in_progress` | **进行中** | In Progress | **AI 执行中**：AI 正在编写代码与自测（**严格限制同时仅 1 项**），标记 `@{ assigned: "AI" }`。 |
| `ready_for_review` | **待验收** | Ready for Review | **看板终点**：AI 开发自测完成，提交人类验收。验收通过即刻物理移出看板。 |

---

### 3. AI 的四大流转动作（SOP）

#### 动作 A：录入新任务（入库）
用户提出新想法、新任务或讨论出新缺陷时：
- 分配唯一的短 ID（如 `feat003`、`fix004`、`perf005`）；
- 用文件编辑工具在 `kanban.html` 的 `backlog` 或 `todo` 下插入卡片：
  ```text
  feat003[增加用户权限导出功能]@{ priority: "High" }
  ```

#### 动作 B：开始开发（接单）
AI 准备攻坚某一任务时：
- 确认当前 `in_progress` 泳道为空；
- 将卡片从 `todo` 剪切挪入 `in_progress`，并附带 `assigned: "AI"`：
  ```text
  in_progress[进行中]
    feat003[增加用户权限导出功能]@{ assigned: "AI", priority: "High" }
  ```
- 告知用户：“已将 `feat003` 移入进行中，现在开始攻坚实现。”

#### 动作 C：开发与自测完成（提测）
AI 编码完成并已通过测试验证：
- 将该卡片从 `in_progress` 剪切挪入 `ready_for_review`：
  ```text
  ready_for_review[待验收]
    feat003[增加用户权限导出功能]@{ assigned: "AI" }
  ```
- 主动在对话中向人类发起验收请求：“任务 `[feat003]` 已就绪并通过自测，请验收！”

#### 动作 D：人类验收通过（物理移出与沉淀）
当人类回复“验收通过”、“OK”、“搞定”、“通过”等确认词时：
1. **物理删除**：直接用 `edit` 工具把该卡片从 `kanban.html` 的 Mermaid 代码中**整行删掉**；
2. **沉淀历史**：将该卡片详细信息追加写进项目根目录的 `history.md`：
   ```markdown
   ### [FEAT-003] 增加用户权限导出功能
   - **完成时间**: 2025-10-30
   - **负责人**: AI Agent
   - **验收结论**: 人类验收通过，功能完整
   - **核心改动**: `src/services/export.ts`, `src/components/ExportBtn.vue`
   ```

---

## 三、 卡片语法速查字典

Mermaid Kanban 遵循严格而极简的语法规范，AI 编辑时必须确保语法合法：

- **普通卡片**：`cardId[卡片简明标题]`
- **带优先级卡片**：`cardId[标题]@{ priority: "High" }` （可选值：`High` / `Medium` / `Low`）
- **带负责人卡片**：`cardId[标题]@{ assigned: "AI" }`
- **组合属性**：`cardId[标题]@{ assigned: "AI", priority: "High" }`
