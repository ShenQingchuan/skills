---
name: create-issue-ticket
description: 快速记录关联产品 spec 的功能、需求或用户可感知缺陷卡片。内部重构、性能优化、依赖升级、技术待办不建卡，转交 manage-engineering。
---

# create-issue-ticket 技能指南

本技能用于把用户随口提到的**产品需求、功能想法或用户可感知缺陷**快速记录到产品交付看板。它不是通用任务收集器。

---

## 一、先过分流与 spec 两道门

### 1. 判断是否属于产品成果

- 新功能、需求变更、用户可感知的 Bug 或体验问题：可以继续建卡；
- 重构、性能优化、依赖升级、架构迁移、CI、测试设施和内部技术待办：不要建卡，调用 `/manage-engineering`；
- 某个产品需求下面的技术子任务：只写入对应 engineering 单元，不另建产品卡片。

### 2. 检查产品 spec

每张卡必须关联真实存在、包含验收标准的产品 spec：

```text
.agents/specs/<spec-name>/README.md
```

如果尚无产品 spec，先调用 `/create-spec` 补齐。不得编造路径，不得将纯技术设计当作产品验收 spec。

---

## 二、标准操作步骤

### 第一步：检查看板

检查 `.agents/kanban/kanban.html`（或旧项目的根目录 `kanban.html`）：

- 如果还没有看板，说明可先运行 `boss kanban` 或调用 `/manage-project-kanban` 初始化；
- 如果用户要求先建看板再记录，初始化后继续；
- 不要在项目里新建 `TODO.md`、`issues/xxx.md` 等零碎待办文件。

### 第二步：自动取唯一编号

读取已有卡片编号，按产品成果类型递增：

- 用户可感知问题或缺陷：`fix001`、`fix002`；
- 新功能或产品想法：`feat001`、`feat002`。

不要使用 `refactor`、`perf`、`chore` 或通用 `task` 前缀；这些类型不应进入产品看板。

### 第三步：提炼标题与优先级

- 用 15 字以内的大白话描述可验收的产品结果；
- 用户明确表示紧急或重要时，添加 `priority: "High"`；
- 默认放入 `backlog[待处理]`；明确要求立即排期时放入 `todo[待开发]`。

### 第四步：写入卡片

写入时必须携带已经核实的产品 `spec` 路径：

```text
backlog[待处理]
  fix004[登录页手机号校验报错缺失]@{ spec: ".agents/specs/login-validation/README.md", priority: "High" }
```

看板会拒绝缺少有效 `spec` 属性的卡片，不要绕过校验。

### 第五步：一句话汇报

> “已记到产品看板待处理栏：`fix004[登录页手机号校验报错缺失]`。”

如果分流到了工程实施，则改为说明 engineering 单元路径，不要声称已经建卡。

---

## 三、常见触发与分流

- “记个 bug：手机端点开菜单会闪退” → 核实产品 spec 后建卡；
- “/create-issue-ticket 夜间模式下边框看不清” → 核实产品 spec 后建卡；
- “有个新想法，后面做个一键导出表格功能” → 先建产品 spec，再建卡；
- “把这个接口的重试次数改成 3 次” → 内部技术调整，进入 engineering；
- “顺手把认证模块重构掉” → 进入 engineering，不建 Kanban 卡片。
