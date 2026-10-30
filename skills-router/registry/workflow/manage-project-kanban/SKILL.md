---
name: manage-project-kanban
description: 项目任务看板工具。在项目事情多、容易忘、分不清做到哪一步时使用。用来给任务排队、记录当前正在做什么、做完了让人检查确认，确认通过后归档到历史记录。支持一键搭建网页看板，方便随时看进度。
---

# manage-project-kanban 技能指南

本技能是一套面向软件项目的 **项目任务看板工具**。

它的核心用途就两个：
1. **给项目搭看板（Setup）**：把轻量网页看板装进项目里，方便在浏览器随时看任务进度；
2. **平时怎么用（Manage）**：AI 接单干活、把任务从待办挪到进行中、做完让人确认，确认没问题就从看板删掉并记入历史。

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

当用户说“帮这个项目建个任务看板”、“用看板管一下现在的任务”、“不知道做到哪了，做个进度看板”时，AI 优先使用一键安装脚本完成搭建：

### 方式 A：使用一键安装脚本（推荐）

直接在终端调用安装脚本，把 `kanban-app` 文件包拷到目标项目，并自动生成初始的 `kanban.html` 与 `history.md`：

- **macOS / Linux**：
  ```bash
  ~/.agents/skills/skills-router/registry/workflow/manage-project-kanban/scripts/install-kanban-app [目标目录，默认当前目录 .]
  ```
- **Windows (PowerShell)**：
  ```powershell
  powershell -ExecutionPolicy Bypass -File "$HOME\.agents\skills\skills-router\registry\workflow\manage-project-kanban\scripts\install-kanban-app.ps1" [目标目录，默认当前目录 .]
  ```

---

### 方式 B：手动复制应用文件

如果不方便运行脚本，也可以直接复制前端文件包：

- **模版目录**：
  `~/.agents/skills/skills-router/registry/workflow/manage-project-kanban/assets/kanban-app/`
- **里面的 3 个文件**：
  1. `kanban.html`：网页看板，里面放着任务文本数据；
  2. `kanban-style.css`：黑白自适应的网页样式；
  3. `kanban-app.js`：网页画板的交互驱动脚本。
- **再建一个归档文件**：
  在项目里建一个 `history.md`，专门放以后做完并确认通过的历史任务。

---

### 步骤：填入初始任务并打开网页预览

安装好之后：
1. 打开项目里的 `kanban.html`，滑到底部的 `<script type="text/mermaid" id="kanban-source">`，把当前手头要办的事填进去；
2. 启动本地轻量预览服务：
   - **macOS / Linux**：
     ```bash
     ~/.agents/skills/.runtime/bin/bun x vite --port 5173
     ```
   - **Windows (PowerShell)**：
     ```powershell
     & "$HOME\.agents\skills\.runtime\bin\bun.exe" x vite --port 5173
     ```
3. 告诉用户：
   > “项目任务看板已经搭好了！在浏览器打开 `http://localhost:5173/kanban.html` 就能看进度。后面改了任务，网页会自动刷新。”

---

## 二、 Manage：已有看板的项目如何日常维护

项目里已经有 `kanban.html` 后，AI 平时干活按这几个规矩来：

### 1. 核心规矩
- **做完确认了就删掉**：看板上只留“还没做”和“正在做”的事，**不要在看板上堆一堆已完成卡片**，保持页面干净；
- **移到历史文件保存**：只要人看过了说确认、没问题，AI 就把任务从看板里**整行删掉**，写进 `history.md` 留档；
- **一次只做一件事**：“进行中”这一栏，同时**只能有 1 个任务**。做完一个再领下一个，不能三心二意。

---

### 2. 四个泳道分别放什么

| 泳道 Key | 中文标签 | 英文标签 | 什么时候放这里 |
| :--- | :--- | :--- | :--- |
| `backlog` | **待处理** | Backlog | **任务池**：刚想到的点子、临时发现的小毛病，还没想清楚怎么做的，先扔在这里。 |
| `todo` | **待开发** | Todo | **排好队的**：已经想好怎么做、分好轻重缓急的，随时准备开工。 |
| `in_progress` | **进行中** | In Progress | **AI 正在做的**：AI 正在写代码、做验证（**必须严格保证只有 1 个**）。 |
| `ready_for_review` | **待验收** | Ready for Review | **做完了等确认**：AI 做完也自测过了，放这里等用户看。用户确认没问题就删掉归档。 |

---

### 3. AI 的日常操作步骤

#### 步骤 A：记下新任务（存进待办）
有了新想法、新任务或者发现新 Bug：
- **推荐捷径**：直接调起配套技能 `/create-issue-ticket`，由它自动计算短编号并一键写进看板待处理池；
- **手动录入**：起一个简单的编号（如 `feat003`、`fix004`），写进 `kanban.html` 的 `backlog`（待处理）或 `todo`（待开发）里：
  ```text
  feat003[增加用户权限导出功能]@{ priority: "High" }
  ```

#### 步骤 B：开始做这个任务（接单开工）
AI 准备开工时：
- 先看一眼 `in_progress` 是不是空的（确保手头没压着别的事）；
- 把任务从 `todo` 剪切到 `in_progress`，加上 `assigned: "AI"`：
  ```text
  in_progress[进行中]
    feat003[增加用户权限导出功能]@{ assigned: "AI", priority: "High" }
  ```
- 跟用户说一声：“已把 `feat003` 移到进行中，现在开始做。”

#### 步骤 C：做完并自测过（请人检查）
代码写完了、自己也测试跑通了：
- 把任务从 `in_progress` 剪切到 `ready_for_review`：
  ```text
  ready_for_review[待验收]
    feat003[增加用户权限导出功能]@{ assigned: "AI" }
  ```
- 叫用户来看：“任务 `[feat003]` 已经做完并通过了自测，请您检查一下！”

#### 步骤 D：用户确认通过（从看板删掉并记入历史）
用户回复“没问题”、“通过”、“搞定”、“OK”之后：
1. **彻底删掉**：直接把这行卡片从 `kanban.html` 里面**删掉**；
2. **记进历史**：把做了什么、改了哪些文件追加写进 `history.md`：
   ```markdown
   ### [FEAT-003] 增加用户权限导出功能
   - **完成时间**: 2025-10-30
   - **负责人**: AI Agent
   - **确认结果**: 用户确认通过，功能正常
   - **改动文件**: `src/services/export.ts`, `src/components/ExportBtn.vue`
   ```

---

## 三、 卡片怎么写（简明语法）

卡片语法非常简单：

- **普通卡片**：`cardId[卡片标题]`
- **带优先级**：`cardId[卡片标题]@{ priority: "High" }` （可选：`High` / `Medium` / `Low`）
- **带负责人**：`cardId[卡片标题]@{ assigned: "AI" }`
- **两个都有**：`cardId[卡片标题]@{ assigned: "AI", priority: "High" }`
