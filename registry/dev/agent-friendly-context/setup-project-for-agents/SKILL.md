---
name: setup-project-for-agents
description: 为项目初始化对 Agent 友好的上下文环境与目录结构，引导渐进式信息披露。
---

# Setup Project for Agents

本技能用于为任何代码仓库或项目目录，搭建一套**对 AI 智能体（Agent）高度友好**的上下文环境。

---

## 核心理念：什么是好的上下文管理？

Agent 不是人脑，它没有长期肉身记忆；但它也不是垃圾桶，如果一上来把所有代码和文档都塞进对话，它的“注意力”就会被稀释，容易抓不住重点甚至产生幻觉。

- **本质**：控制 Agent 的注意力。
- **原则**：**渐进式披露（Progressive Disclosure）**。先给看路牌，需要哪块知识，再去翻哪个抽屉；用不到的知识绝对不提前加载。

---

## 项目的标准骨架

一个对 Agent 友好的项目，在根目录应具备清晰、标准的双层结构：

```text
<项目根目录>/
├── AGENTS.md                  # 门面大招牌：项目的全局导航与核心概况
└── .agents/                   # Agent 的专属百宝箱
    ├── skills/                # 本项目专属技能（私有工作流与操作手册）
    ├── docs/                  # 补充资料（背景说明、参考文档与素材索引）
    ├── specs/                 # 稳定规约（产品行为、业务逻辑、架构契约）
    ├── rules/                 # 规则约束（编码规范、安全红线、行为禁忌）
    ├── engineering/           # 工程实施（技术方案、步骤、迁移与验证）
    └── kanban/                # 产品交付（可独立验收的产品成果；外部追踪模式不建）
```

四个维度的职责不得混用：

- **Specs 定义正确性**：记录长期有效的产品与系统规约；
- **Rules 限定边界**：记录必须持续遵守的约束；
- **Engineering 管理工程实施**：记录技术工作的过程，不管理产品排期；
- **Kanban 管理产品交付**：只接收关联产品 spec、可独立验收的产品成果；交付状态在外部系统维护时改用「外部追踪」模式。

**Docs 提供补充信息**：存放背景说明、参考文档、外部资料与素材索引，按需查阅；不重复 Specs 和 Rules，也不记录工程实施过程或产品交付状态。

---

## 标准执行流程

当被唤醒去为一个项目初始化或梳理 Agent 环境时，请按顺序执行以下 4 步：

### 第一步：探查项目现状
在动手建文件之前，先用工具看看当前项目的实际情况：
- **如果是全新空仓库**：重点向用户了解项目的初衷、要做什么产品、用什么技术栈。
- **如果是已有成熟仓库**：先浏览现有的 `README.md`、各类配置文件以及主要目录，提炼出项目的核心轮廓。
- **如果已有自己的文档目录**（如 `docs/decisions/`、`docs/adr/`、`docs/rfcs/`、`.cursor/rules/`、`CLAUDE.md`）：按 [references/migration.md](references/migration.md) 的对应关系迁移，并同时更新文档之间的互相引用。
- **确认交付状态放在哪里**：项目已经用 GitHub Project、GitHub Issues、Jira、Linear 等外部系统排期时，采用下文的「外部追踪」模式；没有外部系统时，默认使用本地 Kanban。

### 第二步：建立基础目录骨架
在项目根目录下确保存在以下目录与文件骨架：
1. 根目录创建 `AGENTS.md`（如果尚未存在）。
2. 创建 `.agents/` 目录，并在其下建立五个子目录：
   - `.agents/skills/`
   - `.agents/docs/`
   - `.agents/specs/`
   - `.agents/rules/`
   - `.agents/engineering/`
3. 按交付追踪模式处理产品交付：
   - **本地 Kanban（默认）**：需要产品交付看板时，调用 `/manage-project-kanban` 初始化 `.agents/kanban/`，不要手工创建缺少应用的看板空目录。多个 worktree 并行开发时，可启用其中的并行模式。
   - **外部追踪**：不创建 `.agents/kanban/`，见下文。

#### 外部追踪模式

交付状态以外部系统为准，仓库里不再复制一份：

- **AGENTS.md 声明**：上下文指引中把产品交付一行写成指向外部系统，例如 `- 产品成果交付状态：GitHub Project「Roadmap」（https://github.com/orgs/acme/projects/3），本仓库不建 Kanban`。
- **Spec 链接 issue**：每个产品 spec 的 README 开头写一行 `- 交付追踪：<issue 链接>`，多个 issue 逐个列出。只写链接，不抄录状态、负责人或排期。
- **Engineering 关联 issue**：工程单元的「关联产品卡片」改填 issue 编号或链接。
- **不在本地建卡**：`/manage-project-kanban`、`/create-issue-ticket` 不再使用。需要新建 issue 时，把标题和正文草稿交给用户；用户明确同意后才能通过 `gh` 等工具代为创建。

### 第三步：编写项目门面导航（AGENTS.md）
- `AGENTS.md` 是高频消费的入口文件，必须控制篇幅（建议 50~100 行内），只放定调、针对性测试命令、服务自启与可观测验证闭环、以及指向 `.agents/` 的指路牌。
- 在上下文指引中明确：内部工程工作进入 `.agents/engineering/`，不得创建 Kanban 卡片。
- 👉 调用技能 `/manage-agents-md` 创建或持续维护 AGENTS.md。

### 第四步：后续内容填充指引
基础环境搭建完毕后，当需要进一步为该项目沉淀具体内容时，引导调用专门的工具技能：
- **需要将讨论好的业务方案或需求落盘到 `.agents/specs/`？**
  👉 调用技能：`/create-spec`
- **需要记录重构、升级、迁移或其他技术实施过程？**
  👉 调用技能：`/manage-engineering`
- **需要管理可独立验收的产品成果交付？**
  👉 调用技能：`/manage-project-kanban`（外部追踪模式下直接在外部系统操作）
- **需要将项目专属套路固化到 `.agents/skills/`？**
  👉 调用技能：`/create-skill`
- **需要制定项目硬性规范或红线到 `.agents/rules/`？**
  👉 调用技能：`/create-rule`
