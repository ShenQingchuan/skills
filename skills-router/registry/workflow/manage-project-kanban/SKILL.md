---
name: manage-project-kanban
description: 项目看板与敏捷工作流维护指南 - 教导 AI 如何读写基于 Mermaid 与 Pele 的需求画板，以清晰泳道推进任务流转，并在验收通过后将任务归档移出看板。
---

# manage-project-kanban 技能指南

本技能定义了一套基于 **Mermaid Kanban 纯文本** 与 **Pele 交互式 HTML 画板** 的轻量敏捷研发工作流。

让普通软件开发就像在 GitHub Project / Issue 中协同一样直观自然：遇到问题提 Issue、排期进入看板、AI 读取看板接单开发、自测完成提交待验收，最终验收通过后归档沉淀。

---

## 一、 核心设计哲学（第一性原理）

1. **待验收即是看板的终点**：
   实时看板只记录“正在流转”的高价值信息。**绝不在看板中堆积已完成（Done）卡片**，避免看板变成沉重的垃圾堆。
2. **验收通过必须物理移出**：
   一旦用户确认验收通过（Accepted），AI 必须将该卡片从 Mermaid 看板中**彻底删除**，并转移记录到项目根目录或 `.workflow/history.md` 的归档历史中。
3. **文本即数据，画板即呈现**：
   - **对 AI**：直接读写 `board.html` 中的 Mermaid 纯文本（`<script type="text/mermaid" id="kanban-source">`），0 额外格式开销；
   - **对人类**：浏览器直接打开 `board.html`，通过 Pele (WebAssembly/SVG) 与 Halfmoon v2 呈现出高颜值、可交互、可缩放的现代化画板。

---

## 二、 看板的四大法定泳道

Mermaid 看板必须严格维护以下 4 个泳道，不要随意增添混乱分类：

```mermaid
kanban
  Backlog
    [REQ-001] 原始想法 / 待细化分解的 Bug
  Todo
    [REQ-002] 目标已明确、排期待做
      priority: high
  In Progress
    [REQ-003] AI 正在攻坚的任务 (WIP 限制)
      assignee: AI
  Ready for Review
    [REQ-004] 开发与自测就绪，等待人类最终验收
```

| 泳道名称 | 职责定位 | 进入准则 | 离开准则 |
| :--- | :--- | :--- | :--- |
| **`Backlog`** | 需求池 / 原始议题 | 人类或 AI 提出了新点子、临时 Bug、粗粒度方案。 | 经过讨论明确了具体可执行的目标和方案，移入 `Todo`。 |
| **`Todo`** | 准备开发 / 排期列表 | 目标明确、已评定优先级 (`priority: high/medium/low`)。 | AI 准备开始攻坚该任务，移入 `In Progress`。 |
| **`In Progress`** | 正在开发中 | AI 正在编写代码与自测（**WIP 限制：同时仅能进行 1 项**）。 | 代码实现完毕且通过本地测试，移入 `Ready for Review`。 |
| **`Ready for Review`** | **待验收 (看板终点)** | 交付物已就绪，向用户提供测试验证说明与体验入口。 | 用户体验确认无误并点击验收，**物理移出看板，归档至历史**。 |

---

## 三、 AI 标准操作规范（SOP）

AI 在维护看板时，必须遵循以下标准动作：

### 1. 发现新问题或记录新想法（入库）
- 为新需求分配唯一编号（如 `[FEAT-001]`、`[BUG-002]`、`[PERF-003]`）；
- 追加放入 `Backlog`（粗粒度想法）或 `Todo`（明确可做的任务）；
- 示例：
  ```mermaid
  kanban
    Todo
      [FEAT-006] 增加用户头像裁剪上传功能
        priority: medium
  ```

### 2. 认领任务并开始开发（接单）
- 从 `Todo` 泳道选定优先级最高的任务；
- 将其完整文本从 `Todo` 剪切挪入 `In Progress`；
- 添加 `assignee: AI` 属性，表明当前负责人；
- **自律原则**：`In Progress` 泳道只允许存在 1 个正在攻坚的任务，避免并发上下文发散。

### 3. 完成开发与本地自测（送审）
- 编写完业务代码并跑通本地测试；
- 将卡片从 `In Progress` 剪切挪入 `Ready for Review`；
- 在对话中向人类汇报：“任务 `[XXX]` 已开发完毕并就绪，请验收”。

### 4. 验收通过与归档移出（终极归档）
- 当人类回复“验收通过”、“确认”、“OK”或满意结果时：
  1. **物理删除**：直接使用 `edit` 工具将该卡片从 `board.html` 的 Mermaid 代码中整段删掉；
  2. **沉淀历史**：将该卡片内容、完成时间、影响范围写入项目历史档案（如 `history.md`）：
     ```markdown
     ### [FEAT-006] 增加用户头像裁剪上传功能
     - **完成时间**: 2025-10-29
     - **验收结论**: 人类验收通过，功能正常上线
     - **主要改动**: `src/components/AvatarUpload.vue`, `src/api/user.ts`
     ```

---

## 四、 本地画板极速预览与 HMR（热重载）

当用户需要打开可视化画板时，AI 可提示或协助运行：

```bash
# 利用套件自举自带的 Bun，0 秒拉起 Vite 热重载服务
.runtime/bin/bun x vite
```

- 启动后浏览器访问输出的本地地址（如 `http://localhost:5173`）；
- AI 后续每次通过文件工具修改 `board.html` 中的 Mermaid 内容时，Vite 将通过 WebSocket 实现**毫秒级无感热重载**，人类浏览器里的 SVG 看板卡片会实时自动重绘并滑向下一泳道！
