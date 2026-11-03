---
name: draw-with-pele
description: 使用 Pele 将 Mermaid 文本渲染为可定制主题的 SVG。当用户要求 /draw-with-pele、绘制流程图/时序图/架构图/类图/ER 图/甘特图/思维导图，或将 Mermaid 转成 SVG 时使用。
---

# Draw with Pele

先梳理信息，再写 Mermaid，最后用随附脚本生成 SVG。统一使用 Pele 渲染，保留可继续编辑的源文件。

## 工作流程

### 1. 选择最简单的合适图型

- 流程、分支、依赖：`flowchart`
- 多方按时间传递消息：`sequenceDiagram`
- 系统与容器关系：C4 或 `architecture-beta`
- 类、数据表及其关系：`classDiagram`、`erDiagram`
- 计划与阶段：`gantt`、`timeline`
- 层级与拆解：`mindmap`、`treemap`
- 数值比较：`xychart`、`pie`

图型不确定时，读取 [reference.md](reference.md) 的速查表。优先表达用户给出的核心关系，不为了显得丰富而堆叠图型。

### 2. 编写 Mermaid 源文件

确定图型后，只读取 [reference.md](reference.md) 中链接的对应官方示例，以其语法为准；复杂变体沿示例文件顶部的链接查阅。然后在用户的工作目录保存为 `<名称>.mmd`：

- 一张图只回答一个主要问题；节点使用简短、明确的标签。
- 中文或含空格、标点的节点标签使用引号，例如 `A["提交订单"]`。
- 流程图先选方向：步骤较少且横向展示用 `LR`，层级较深或步骤较多用 `TD`。
- 保留事实之间的关系；缺少的信息不自行编造。
- 仅需要视觉微调时，优先使用 Pele CSS 变量，具体写法见 [reference.md](reference.md)。

### 3. 渲染 SVG

使用仓库自带的 Node.js runtime 执行：

```bash
"$HOME/.agents/skills/.runtime/bin/node" \
  "$HOME/.agents/skills/registry/writing/draw-with-pele/scripts/render.mjs" \
  "<名称>.mmd" -o "<名称>.svg"
```

runtime 未就绪时先执行 `boss setup-runtime`。如果提示缺少 `pele` 依赖，使用自带 npm 安装后重新执行：

```bash
"$HOME/.agents/skills/.runtime/bin/npm" ci \
  --prefix "$HOME/.agents/skills/registry/writing/draw-with-pele"
```

尺寸、字体、主题 CSS 等可选参数通过 `--help` 查看：

```bash
"$HOME/.agents/skills/.runtime/bin/node" \
  "$HOME/.agents/skills/registry/writing/draw-with-pele/scripts/render.mjs" --help
```

### 4. 修复并复验

脚本报告语法错误时，根据行号、列号和源码片段修改 `.mmd`，再运行同一渲染命令。完成标准是脚本退出码为 0，且目标 SVG 已生成。

### 5. 检查并交付

检查 SVG 的尺寸、文字和连线是否完整；过密时先精简标签或拆分图，再考虑调整方向与 `--max-width`。最终同时给出：

- `<名称>.svg`：可直接打开或嵌入文档的成品；
- `<名称>.mmd`：便于继续修改的源文件。

用户只要求源文本时，也至少运行一次渲染来验证语法。
