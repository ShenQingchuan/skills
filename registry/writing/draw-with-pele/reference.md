# Pele 参考

仅在需要选择图型、查询语法差异或调整主题时读取本文件。

## 图型速查

Pele 支持 Mermaid 12.1.0 内置的图型，但使用自己的布局与视觉风格。

| 表达目的 | Mermaid 起始关键字 | 官方精选示例 |
| --- | --- | --- |
| 流程、决策、依赖 | `flowchart` 或 `graph` | [flowchart](references/examples/flowchart.md) |
| 泳道流程 | `swimlane-beta` | [swimlane](references/examples/swimlane.md) |
| 消息调用顺序 | `sequenceDiagram` | [sequence](references/examples/sequence.md) |
| 类与继承 | `classDiagram` | [class](references/examples/class.md) |
| 状态迁移 | `stateDiagram-v2` | [state](references/examples/state.md) |
| 实体与数据关系 | `erDiagram` | [er](references/examples/er.md) |
| 日程与工期 | `gantt` | [gantt](references/examples/gantt.md) |
| Git 分支历史 | `gitGraph` | [git](references/examples/git.md) |
| 占比 | `pie` | [pie](references/examples/pie.md) |
| 层级想法 | `mindmap` | [mindmap](references/examples/mindmap.md) |
| 任务看板 | `kanban` | [kanban](references/examples/kanban.md) |
| 事件时间线 | `timeline` | [timeline](references/examples/timeline.md) |
| 用户体验过程 | `journey` | [journey](references/examples/journey.md) |
| 象限分析 | `quadrantChart` | [quadrant](references/examples/quadrant.md) |
| 柱状图、折线图 | `xychart` | [xychart](references/examples/xychart.md) |
| 需求追踪 | `requirementDiagram` | [requirement](references/examples/requirement.md) |
| 流量分配 | `sankey-beta` | [sankey](references/examples/sankey.md) |
| 系统架构 | `architecture-beta` | [architecture](references/examples/architecture.md) |
| C4 架构 | `C4Context`、`C4Container`、`C4Component`、`C4Dynamic`、`C4Deployment` | [c4](references/examples/c4.md) |
| 块状布局 | `block-beta` | [block](references/examples/block.md) |
| Agent 工作流 | `agentflow-beta` | [agentflow](references/examples/agentflow.md) |
| 语法铁路图 | `railroad-beta` | [railroad](references/examples/railroad.md) |
| 树状文件结构 | `treeView-beta` | [treeview](references/examples/treeview.md) |
| Cynefin 决策分析 | `cynefin-beta` | [cynefin](references/examples/cynefin.md) |
| Wardley 战略地图 | `wardley-beta` | [wardley](references/examples/wardley.md) |
| 事件建模 | `eventmodeling` | [eventmodeling](references/examples/eventmodeling.md) |
| 用例关系 | `usecase-beta` | [usecase](references/examples/usecase.md) |
| 韦恩图 | `venn-beta` | [venn](references/examples/venn.md) |
| 鱼骨图 | `ishikawa-beta` | [ishikawa](references/examples/ishikawa.md) |
| 数据包结构 | `packet-beta` | [packet](references/examples/packet.md) |
| 雷达图 | `radar-beta` | [radar](references/examples/radar.md) |
| 矩形树图 | `treemap-beta` | [treemap](references/examples/treemap.md) |

## 示例的使用

确定图型后，只读取上表对应的示例文件。文件收录 Pele 官方 Examples 首页的精选示例；需要更多变体或边界语法时，沿文件顶部的链接查阅该图型的完整官方示例。

## Pele 与 Mermaid 的关键差异

- Pele 面向 Mermaid 12.1.0 语法；ZenUML 等外部插件不在支持范围内。
- 布局、节点位置、间距和连线路径由 Pele 自己计算，与 Mermaid.js 不完全相同。
- 标签支持文本、换行、粗体和斜体；复杂排版使用多个简洁标签表达。
- Mermaid 主题不会直接生效；通用配色使用下文的 CSS 变量。
- `style`、`classDef` 中写死的颜色不会随主题切换。
- 数学公式需要应用提供排版器；随附脚本保留 TeX 源文本。
- 随附脚本默认关闭外部链接和图片，避免打开 SVG 时产生网络请求；确有需要时使用 `--allow-external`。

官方兼容性说明见 <https://pele.run/compatibility>。

## 主题

先用渲染器的 `--css <文件>` 注入主题。CSS 以 `.pele` 为作用域：

```css
.pele {
  --pele-bg: #fffcf0;
  --pele-fg: #100f0f;
  --pele-muted: #6f6e69;
  --pele-line: #100f0f;
  --pele-surface: #f2f0e5;
  --pele-surface-alt: #e6e4d9;
  --pele-border: #cecdc3;
  --pele-accent: #205ea6;
  --pele-critical: #af3029;
  --pele-radius: 4px;
}
```

常用变量：

| 变量 | 用途 |
| --- | --- |
| `--pele-bg` | 背景 |
| `--pele-fg` | 正文与标签 |
| `--pele-muted` | 次要文字 |
| `--pele-line` | 连线与箭头 |
| `--pele-surface` | 节点填充 |
| `--pele-surface-alt` | 分组填充 |
| `--pele-border` | 边框 |
| `--pele-accent` | 强调色 |
| `--pele-series-1` 至 `--pele-series-8` | 图表系列颜色 |
| `--pele-font` | 正文字体 |
| `--pele-font-mono` | 等宽文字字体 |

使用自定义字体时，同时向脚本传入相同的 `--font-family`，让文字测量与最终显示一致。完整主题文档见 <https://pele.run/theming>，渲染 API 见 <https://pele.run/api>。
