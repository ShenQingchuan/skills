---
name: manage-project-kanban
description: 管理可独立验收的产品需求、功能和用户可感知缺陷的交付状态。重构、架构迁移、依赖升级、性能优化、CI 与测试设施等内部工程工作不适用。
---

# manage-project-kanban 技能指南

本技能是一套面向软件项目的**产品交付看板工具**。

它像 PM 管理产研团队一样管理产品成果，而不是记录所有编程活动：

1. **给项目搭看板（Setup）**：把轻量网页看板装进项目里，方便在浏览器随时看产品交付进度；
2. **平时怎么用（Manage）**：管理关联产品 spec、能够独立验收的需求、功能和用户可感知缺陷，从待办推进到产品验收并归档。

---

## 零、准入边界：先判断，再建卡

### 可以进入 Kanban

- 能独立交付和验收的产品需求、新功能或需求变更；
- 用户可感知、可按产品行为验收的 Bug 或体验问题。

### 不得进入 Kanban

- 重构、架构迁移、依赖升级、内部性能优化；
- CI、测试设施、内部工具、可观测性和稳定性建设；
- 用户无感知的技术缺陷修复；
- 产品需求下面的前端、后端、测试、重构等实施子任务。

这些工作调用 `/manage-engineering`，记录在 `.agents/engineering/`。独立工程工作不建卡；产品需求下的工程单元只关联现有产品卡片，不复制产品状态。

**硬门槛：没有可独立验收的产品 spec，就不得进入 Kanban。** 不得使用不存在的产品 spec 路径绕过检查，看板也会拒绝缺少有效 `spec` 属性的卡片。

---

## 一、跨平台独立运行时调用规范

本技能配套工具执行时，使用本仓库内置的运行环境：

- **标准基准路径**：`~/.agents/skills/.runtime/`
- **各操作系统与 Shell 执行对照**：

| 平台 / 环境 | 路径写法示例 | 说明 |
| :--- | :--- | :--- |
| **macOS / Linux (Bash/Zsh)** | `~/.agents/skills/.runtime/bin/python3` | Shell 会自动将 `~` 展开为当前用户主目录 |
| **Windows (PowerShell)** | `$HOME\.agents\skills\.runtime\bin\python.exe` | PowerShell 中 `$HOME` 会自动展开 |
| **Windows (cmd.exe)** | `%USERPROFILE%\.agents\skills\.runtime\bin\python.exe` | cmd 不支持 `~` 展开，必须使用 `%USERPROFILE%` |

> AI 应根据当前宿主操作系统选取对应的执行路径。

---

## 二、Setup：为项目初始化看板

当用户说“帮这个项目建个产品看板”、“用看板管一下产品需求”、“不知道功能做到哪了”时，看板默认统一部署在项目工作区的 `.agents/kanban/` 目录下。

### 方式 A：使用一键命令（最推荐）

```bash
boss kanban [项目路径，默认当前项目 .]
```

命令会初始化看板应用，并在后台启动预览服务。

也可以使用安装脚本单独部署文件：

- **macOS / Linux**：
  ```bash
  ~/.agents/skills/registry/workflow/manage-project-kanban/scripts/install-kanban-app [目标项目路径，默认当前目录 .]
  ```
- **Windows (PowerShell)**：
  ```powershell
  powershell -ExecutionPolicy Bypass -File "$HOME\.agents\skills\skills-router\registry\workflow\manage-project-kanban\scripts\install-kanban-app.ps1" [目标项目路径，默认当前目录 .]
  ```

### 方式 B：手动复制应用文件

将 `assets/kanban-app/` 中的三个文件复制到项目的 `.agents/kanban/`：

1. `kanban.html`：网页看板和产品卡片数据；
2. `kanban-style.css`：黑白自适应的网页样式；
3. `kanban-app.js`：网页看板的交互、校验和渲染脚本。

再建一个 `history.md`，保存验收通过并归档的产品成果。

### 必须设置项目名标题

无论使用哪种初始化方式，完成后都必须立即设置项目名，不得保留通用标题：

1. 找到 `.agents/` 所在的工作区根目录，而不是 `.agents/`、`.agents/kanban/` 或技能仓库目录；
2. 取该工作区根目录的目录名作为项目名；
3. 将项目名写入 `.agents/kanban/kanban.html` 根节点的 `data-project-name` 属性。

例如工作区根目录为 `/work/astryx-vue`，看板位于 `/work/astryx-vue/.agents/kanban/`，则设置：

```html
<html lang="zh-CN" data-theme="dark" data-project-name="astryx-vue">
```

页面标题和页眉必须完整显示为 `astryx-vue · 项目看板`，不能只显示目录名，也不能省略“项目看板”后缀。切换语言时保留项目名，重新安装或更新看板引擎时不得清除该属性。

### 启动或停止预览

```bash
boss kanban [项目路径] [--port 5173]
boss kanban stop [项目路径] [--port 5173]
```

浏览器打开 `http://localhost:5173/kanban.html`。看板由 Vite 原生 HMR 驱动，修改卡片后页面会自动更新。

---

## 三、Manage：产品成果如何流转

### 1. 核心规矩

- **一张卡片是一项完整产品成果**：不要把技术分工或实施步骤拆成多张卡；
- **每张卡必须关联产品 spec**：spec 必须真实存在，并包含可独立判断的验收标准；
- **看板上只留未完成成果**：验收通过后就删除卡片并写入历史，不堆已完成卡片；
- **一次只交付一项**：`in_progress` 同时只能有 1 个产品成果；
- **验收针对完整产品行为**：技术子任务完成不等于产品卡片可以进入待验收。

### 2. 四个泳道分别放什么

| 泳道 Key | 中文标签 | 什么时候放这里 |
| :--- | :--- | :--- |
| `backlog` | **待处理** | 已有关联合规 spec、尚未排期的产品成果。 |
| `todo` | **待开发** | 已明确验收标准并排好优先级、准备交付的产品成果。 |
| `in_progress` | **进行中** | 正在完整落地的产品成果，严格保证只有 1 个。 |
| `ready_for_review` | **待验收** | 已按 spec 完成全部实施与验证，等待产品验收的成果。 |

### 3. 标准操作步骤

#### 步骤 A：记录产品成果

1. 按“准入边界”判断；内部工程工作转交 `/manage-engineering`；
2. 确认产品 spec 存在且包含验收标准，没有则先调用 `/create-spec`；
3. 推荐使用 `/create-issue-ticket` 自动编号并建卡，或手动写入：

```text
feat003[增加用户权限导出功能]@{ spec: ".agents/specs/permission-export/README.md", priority: "High" }
```

#### 步骤 B：开始完整交付

1. 确认 `in_progress` 为空；
2. 把卡片从 `todo` 移到 `in_progress`，添加 `assigned: "AI"`；
3. 如果技术实施较复杂，调用 `/manage-engineering` 建立工程单元，并在其中记录本卡片编号；
4. 技术步骤只在工程单元中维护，不新建 Kanban 卡片。

```text
in_progress[进行中]
  feat003[增加用户权限导出功能]@{ spec: ".agents/specs/permission-export/README.md", assigned: "AI", priority: "High" }
```

#### 步骤 C：完成并自测

确认 spec 中的产品行为和验收路径均已实现、相关测试通过后，将卡片移到 `ready_for_review`。不要仅因某个工程单元完成就移动产品卡片。

#### 步骤 D：产品验收并归档

用户确认产品成果通过后：

1. 从 `kanban.html` 删除整张卡片；
2. 将成果、关联 spec 和主要改动追加到 `.agents/kanban/history.md`：

```markdown
### [FEAT-003] 增加用户权限导出功能
- **完成时间**: 2025-10-30
- **产品规格**: `.agents/specs/permission-export/README.md`
- **确认结果**: 用户确认通过，功能正常
- **改动文件**: `src/services/export.ts`, `src/components/ExportBtn.vue`
```

---

## 四、卡片语法

```text
cardId[产品成果标题]@{ spec: "产品 spec 路径", priority: "High", assigned: "AI" }
```

- `spec`：**必填**，格式为 `.agents/specs/<spec-name>/README.md` 或对应的真实 Markdown 文件；
- `priority`：可选，`High` / `Medium` / `Low`；
- `assigned`：可选，例如 `AI`；
- 标题描述用户或业务可验收的成果，不使用“重构某模块”“升级某依赖”等工程标题。
