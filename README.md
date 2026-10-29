<div align="center">

# Skills

**让你的 Agent 一次只看见一个技能。**

一个用「渐进式披露」打理的个人 Agent Skills 库。
常驻上下文的只有路由器本身，其余技能用到才装载。

[为什么](#为什么需要它) · [工作原理](#工作原理) · [快速开始](#快速开始) · [技能目录](#技能目录) · [日常使用](#日常使用) · [Agent 指引](#agent-使用指引) · [设计原则](#设计原则)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-1_routed-informational.svg)](#快速开始)
[![Sync skills](https://github.com/ShenQingchuan/skills/actions/workflows/sync-skills.yml/badge.svg)](https://github.com/ShenQingchuan/skills/actions/workflows/sync-skills.yml)

</div>

---

## 为什么需要它

现在流行的 Skill 管理方式是**平铺**的：一个目录里躺几十个技能目录，Agent 一启动就把所有技能的 `description` 灌进系统提示。

后果很直接：

- **Token 白烧** —— 几十条技能描述常年占着上下文，而你绝大多数时间只用得上其中一两个。
- **注意力被稀释** —— 候选越多，模型越容易挑错人。
- **规则互相打架** —— 不同技能对同一件事说法不一致时，平铺结构没有任何优先级可言。
- **不敢多装** —— 于是你被迫做减法，宁可少装也不愿污染上下文。

这个仓库给出的答案是：**只暴露一个入口。**

## 工作原理

三层，层层收窄，每一层只为下一层付一次代价。

| 层 | Agent 看到什么 | 成本 |
| --- | --- | --- |
| ① 常驻 | 只有一个技能：`skills-router`。它自己只说一句话——「有技能树，先查再读」 | 恒定，约 40 tokens |
| ② 查阅 | 跑 `list_skills.py`，得到一棵带分类和一句话描述的技能树 | 随技能数量线性增长，但每项极短 |
| ③ 装载 | 只读命中的那个技能目录下的 `SKILL.md`；它指向 `references/` 时再往下钻 | 只为你真正要用的技能付钱 |

一次典型的查阅输出：

```text
📦 skills-router 已注册技能树 (根目录: /Users/admin/.agents/skills/skills-router/registry)
  ├── 📂 dev/
  │   └── 📂 frontend/
  │       ├── 🎯 vue - Vue 3 Composition API, script setup macros, reactivity system… (入口: dev/frontend/vue/SKILL.md)
  │       ├── 🎯 vue-debug-guides - Vue 3 debugging and error handling for runtime errors… (入口: …)
  │       └── …
  ├── 📂 research/ （空）
  └── 📂 workflow/ （空）
```

**关键点**：`registry/` 里的技能不会自动进入上下文。它们只有被路由器点名、并被显式读取时才会出现。

## 快速开始

```bash
git clone git@github.com:ShenQingchuan/skills.git ~/.agents/skills
```

把整个仓库放到你的 Agent 扫描技能的位置（例如 `~/.agents/skills`）。放好后：

- 你的 Agent 默认**只感知到 `skills-router` 一个技能**；
- `registry/` 下的技能对它来说是隐身的，直到它真的需要。

验证一下（只需要 Python 3，无第三方依赖）：

```bash
python3 skills-router/scripts/list_skills.py
```

## 目录结构

```text
.
├── skills-router/                 ← 唯一被 Agent 默认感知的技能
│   ├── SKILL.md                   ← 路由规则（刻意写得极短）
│   ├── scripts/
│   │   └── list_skills.py         ← 技能树探测：Agent 靠它「看目录」
│   └── registry/                  ← 技能库本体
│       ├── dev/frontend/          ← 前端技能（13 项）
│       ├── workflow/              ← 工作方式技能（2 项）
│       └── research/              ← 调研分析（预留）
│
├── tools/                         ← 维护用工具，不参与 Agent 运行时
│   ├── sources.json               ← 上游清单（人写）
│   ├── sources.lock.json          ← 同步状态（机器写）
│   └── sync_skills.py             ← 同步脚本
│
└── .github/workflows/
    └── sync-skills.yml            ← 每日自动同步
```

`tools/` 里没有 `SKILL.md`，`registry/` 里的技能也不是仓库根目录的一级技能、那一层同样没有 `SKILL.md`，所以两者都不会被 Agent 发现。这正是这个结构成立的原因。

## 技能目录

### 前端 · `dev/frontend`

13 项技能，来自两个定位互补的上游：

| 上游 | 回答的问题 | 形态 |
| --- | --- | --- |
| [antfu/skills](https://github.com/antfu/skills) | **怎么写**（API 参考） | 从官方文档生成的索引 + `references/` 详解 |
| [vuejs-ai/skills](https://github.com/vuejs-ai/skills) | **怎么写好、怎么不踩坑**（实践规约） | 架构工作流 + 「现象 → 修复」速查表 |

**API 参考层（antfu）**：`vue` · `pinia` · `vite` · `vitepress` · `vitest` · `unocss` · `pnpm`

**实践规约层（vuejs-ai）**：`vue-best-practices` · `vue-debug-guides` · `vue-pinia-best-practices` · `vue-router-best-practices` · `vue-testing-best-practices` · `create-adaptable-composable`

> 两个上游会不会打架？逐对比对过了：**不冲突，只有分工不同**。唯一的口径差异（Options API 的取舍）对你的现代 Composition API 路线没有影响。
> 完整的对照表在 [`skills-router/registry/dev/frontend/README.md`](./skills-router/registry/dev/frontend/README.md)。

### 工作方式 · `workflow`

2 项技能，来自 [mattpocock/skills](https://github.com/mattpocock/skills)。

| 技能 | 作用 |
| --- | --- |
| `grilling` | 把模糊的想法逼成共识。把决策组织成一棵「设计树」，按轮次问完当前**前沿**，每个问题都附上推荐答案 |
| `writing-for-agents` | 写给 Agent 消费的文档怎么写：上下文指针、两种负载、信息层级、渐进式披露、完成判据 |

这两个是**元技能**——不解决具体业务问题，而是改善你和 Agent 协作的过程本身。
`grilling` 用在动手之前，`writing-for-agents` 用在写文档的时候。

本仓库的 `README.md`、`AGENTS.md` 和 `skills-router/SKILL.md` 就是按 `writing-for-agents` 的规范写的。它的 `SKILL-MECHANICS.md` 里还有一节专门讲 **router skills**——和本仓库的 `skills-router` 是同一个思路的两个变种：一个化解人的认知负载，一个化解模型的上下文负载。

> 详情见 [`skills-router/registry/workflow/README.md`](./skills-router/registry/workflow/README.md)。

## 日常使用

### 同步上游更新

```bash
python3 tools/sync_skills.py          # 拉取并更新 registry/
python3 tools/sync_skills.py --check  # 只看有没有更新（有则退出码 1）
```

也可以完全交给 CI：`.github/workflows/sync-skills.yml` 每天自动跑一次，有变化就自动提交回 `main`，没变化就什么也不做。你只需要 `git pull`。

同步的可靠性来自三条设计：**幂等**（跑一百遍结果一样）、**可重复**（内容只取决于上游 commit，不取决于时间或机器）、**可无人值守**（CI 里也能跑）。

### 新增一个技能

1. 在 `tools/sources.json` 的 `sources` 里登记仓库（如果还没有）。
2. 在 `install` 里加一行，`skill` 写「上游 `skills/` 下的相对路径」（可以带子目录），`to` 写「本仓库 `registry/` 下的相对目录」：

   ```json
   { "skill": "productivity/grilling", "from": "mattpocock", "to": "workflow/grilling" }
   ```

   两者都是你自己定的，不必跟上游同名。

3. 跑一次 `python3 tools/sync_skills.py`。

索引不用手工维护——`list_skills.py` 会自动发现新目录。

### 移除一个技能

把 `install` 里对应的那一行删掉，再跑一次同步脚本。脚本会连目录一起清理，让 `registry/` 始终等于清单。

## Agent 使用指引

> 这一节同时是 [`AGENTS.md`](./AGENTS.md) 的内容——本仓库的 README 就直接充当 Agent 的工作须知。

### 运行时：需要技能时

1. 跑 `python3 skills-router/scripts/list_skills.py`。
2. 按描述挑最匹配的 **1 个**；确有互补需要时最多再加 1 个（例如「架构规约」配「API 参考」）。
3. **只**读选中技能目录下的 `SKILL.md`；其中若指向 `references/`、`reference/` 或 `scripts/`，再按需下钻。

硬性约束：

- 不要一次性读完 `registry/` 下所有 `SKILL.md`。
- 不要把 `registry/` 下的技能批量加载进上下文——这会直接毁掉这个仓库存在的意义。
- `registry/` 中由 `tools/sources.json` 管理的目录是**产物**，不要手改；下次同步会原样覆盖。

### 修改时：要动这个仓库

| 你想做的事 | 改哪里 |
| --- | --- |
| 新增 / 移除第三方技能 | `tools/sources.json` |
| 升级上游技能 | 跑 `python3 tools/sync_skills.py` |
| 调整路由规则 | `skills-router/SKILL.md` |
| 调整技能树展示 | `skills-router/scripts/list_skills.py` |
| 调整同步行为 | `tools/sync_skills.py` |
| 调整自动同步节奏 | `.github/workflows/sync-skills.yml` |

`tools/sources.lock.json` 由脚本自动生成，不要手改。它记录上游 commit 与每个技能目录的内容指纹，同步脚本靠它判断「有没有变」。

### 提交信息

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```text
<type>(<scope>): <subject>

[optional body]
```

- `type`：`feat` / `fix` / `docs` / `chore` / `ci` / `refactor`
- `scope`：用目录或模块名，如 `router`、`sync`、`registry`
- `subject`：一句话说清「做了什么」，不加句号

示例：

```text
feat(sync): 支持按技能粒度校验内容指纹
docs(registry): 补充 antfu 与 vuejs-ai 的对照结论
chore(registry): 同步上游技能
```

## 设计原则

1. **单一入口** —— 路由器是唯一常驻上下文的技能。它的 `SKILL.md` 必须保持极短，任何一句多余的叮嘱都在收全体技能的税。
2. **渐进式披露** —— 描述 → `SKILL.md` → `references/`，三级递进。每一级只在上一级明确指向时才展开。
3. **产物与源头分离** —— `registry/` 下的第三方技能是产物，源头永远是上游仓库。所以这里只维护「声明」（`sources.json`）和「事实」（`sources.lock.json`），其余全部由脚本推导。
4. **幂等优先** —— 同步跑一百遍和跑一遍结果相同。CI 才可以放心每天跑，你也才敢随时手动跑。
5. **冲突先在安装前解决** —— 装之前先比对同一话题的几个上游，明确各自分工；装进来之后靠「最多 1+1」的规则避免同时加载。

### 为什么不用 Git submodule / 插件市场

- **submodule** 会把整个上游仓库（含大量你不需要的目录）带进来，且文件是子模块引用而非真实文件，Agent 的读取工具往往读不到；符号链接在 Windows 上还会直接失效。
- **插件市场**解决的是「分发」，不是「上下文」。真正的瓶颈是感知面，不是安装方式。

这个仓库选择的是：**稀疏检出 + 原样复制 + 内容指纹**。技能在磁盘上是实实在在的普通文件，任何工具都能读；同步只下载需要的目录，不拉整个仓库。

## 参与贡献

这是个人技能库，但欢迎提 Issue 和 PR：

- 想加某个上游的技能：改 `tools/sources.json` 并跑一次同步脚本，一起提交。
- 发现两个上游的规则冲突：在对应的 `registry/<分类>/README.md` 里补上对照结论。
- 路由器或同步脚本的改进：请附上「为什么现有做法不够好」。

提交前请确认 `python3 tools/sync_skills.py --check` 是干净的（退出码 0）。

## 致谢

技能库的内容来自这些优秀的开源项目，版权归各自作者所有：

- [antfu/skills](https://github.com/antfu/skills) —— Anthony Fu
- [vuejs-ai/skills](https://github.com/vuejs-ai/skills) —— vuejs-ai
- [mattpocock/skills](https://github.com/mattpocock/skills) —— Matt Pocock

## 许可

本仓库自身的代码（`skills-router/` 与 `tools/`）以 [MIT](./LICENSE) 授权。
`registry/` 下的第三方技能保留其上游许可证，详见各技能目录。

<div align="center">

由 [@ShenQingchuan](https://github.com/ShenQingchuan) 维护

</div>
