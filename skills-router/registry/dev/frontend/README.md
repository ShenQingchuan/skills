# dev/frontend

本目录下的技能全部由 `python3 tools/sync_skills.py` 从上游仓库同步而来。
**不要手改这里的文件**——下次同步会原样覆盖。要改就改上游，或把 `tools/sources.json` 里的 `repo` 换成你自己的 fork。

## 两个上游，两种定位

| 上游 | 回答的问题 | 内容形态 |
| --- | --- | --- |
| [antfu/skills](https://github.com/antfu/skills) | **怎么写**（API 参考） | 从官方文档自动生成的索引 + `references/` 详解 |
| [vuejs-ai/skills](https://github.com/vuejs-ai/skills) | **怎么写好、怎么不踩坑**（实践规约） | 架构工作流 + 「现象 → 修复」速查表 |

## 已安装技能

### 来自 antfu/skills —— API 参考层

| 技能 | 作用 |
| --- | --- |
| `vue` | Vue 3.5：`<script setup>` 宏、响应式系统、内置组件 |
| `pinia` | Pinia 4：store 定义、`storeToRefs`、插件、SSR、HMR |
| `vite` | Vite 配置、插件 API、SSR、Rolldown 迁移 |
| `vitepress` | VitePress 文档站搭建与配置 |
| `vitest` | Vitest 5：配置、mock、快照、覆盖率、类型测试 |
| `unocss` | UnoCSS 原子化 CSS 引擎 |
| `pnpm` | pnpm 包管理与 workspace |

### 来自 vuejs-ai/skills —— 实践规约层

| 技能 | 作用 |
| --- | --- |
| `vue-best-practices` | Vue 架构工作流：先定组件边界与数据流，再动手编码 |
| `vue-debug-guides` | Vue 运行时报错 / 警告的「现象 → 修复」速查（内容最厚） |
| `vue-pinia-best-practices` | Pinia 常见坑：`getActivePinia` 报错、解构丢响应式 |
| `vue-router-best-practices` | Vue Router 4 守卫与路由生命周期坑 |
| `vue-testing-best-practices` | Vue 测试策略：Vue Test Utils、`flushPromises`、Playwright |
| `create-adaptable-composable` | 写库级 composable：`MaybeRef` / `MaybeRefOrGetter` |

## 会不会打架？逐对核对结论

**结论：没有真正的冲突，只有分工不同，可以兼容并蓄。**
两边的技能名本身就不重名，所以可以并排安装、各自被独立唤起。

| 话题 | antfu 侧 | vuejs-ai 侧 | 关系 | 实际怎么用 |
| --- | --- | --- | --- | --- |
| Vue 本体 | `vue`（语法 / API） | `vue-best-practices`（架构） | 互补 | 架构决策看后者，写语法查前者 |
| Pinia | `pinia`（API） | `vue-pinia-best-practices`（坑） | 互补 | 两边对「用 `storeToRefs` 解构」的说法完全一致 |
| 测试 | `vitest`（测试框架本身） | `vue-testing-best-practices`（Vue 测试策略） | 层级不同 | 框架用法查前者，Vue 组件怎么写测试查后者 |
| 路由 | 无 | `vue-router-best-practices` | 纯增量 | 直接用 |
| 调试 | 无 | `vue-debug-guides` | 纯增量 | 直接用 |
| Composable | `vue` 内含入门内容 | `create-adaptable-composable` | 互补 | 写对外发布的 composable 用后者 |

### 唯一的口径差异（对你无影响）

- antfu 的 `vue` 规定：**一律用 Composition API**，并明确「Discourage using Reactive Props Destructure」。
- vuejs-ai 的 `vue-best-practices` 留了余地：**只有项目显式要求时才用 Options API**，配套还有 `vue-options-api-best-practices`（未安装）。

你走的是现代 Composition API 路线，两边对你完全一致。万一以后接手老项目，以 vuejs-ai 的「项目显式要求才用」为准即可。

## 怎么更新

```bash
python3 tools/sync_skills.py          # 本地手动同步
python3 tools/sync_skills.py --check  # 只看有没有更新，退出码 1 表示有
```

也可以交给 CI：`.github/workflows/sync-skills.yml` 每天自动拉一次，有变化就自动提交。

## 怎么加新技能

1. 在 `tools/sources.json` 的 `sources` 里登记仓库（没有的话）。
2. 在 `install` 里加一行：`{ "skill": "<上游的技能目录名>", "from": "<仓库 id>", "to": "dev/frontend/<目标目录名>" }`。
3. 跑一次 `python3 tools/sync_skills.py`。

脚本会自动处理稀疏检出、覆盖更新和变更记录，不需要手工维护索引。
