<div align="center">

# Skills

**让你的 Agent 一次只看见一个技能。**

一个用「渐进式披露」打理的个人 Agent Skills 库。
常驻上下文的只有路由器本身，其余技能用到才装载。

[为什么](#为什么需要它) · [工作原理](#工作原理) · [快速开始](#快速开始) · [技能目录 (Catalog)](./CATALOG.md) · [目录结构](#目录结构) · [日常使用](#日常使用) · [Agent 指引](#agent-使用指引) · [设计原则](#设计原则)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-1_routed-informational.svg)](https://agentskills.io/specification)
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

- **① 常驻** —— Agent 默认只认识一个技能：`skills-router`。它自己只说一句话：「有技能树，先查再读」。成本恒定，约 40 tokens。
- **② 查阅** —— 它跑 `list_skills.py`，拿到一棵带分类和一句话描述的技能树。
- **③ 装载** —— 它只读命中的那个技能目录下的 `SKILL.md`；文件里指向 `references/` 时再往下钻。

一次典型的查阅输出：

```text
📦 skills-router（技能路由中心根目录: /Users/admin/.agents/skills/skills-router/registry）
  ├── 📂 dev/
  │   └── 📂 frontend/
  │       ├── 🎯 vue - Vue 3 Composition API, script setup macros… (入口: dev/frontend/vue/SKILL.md)
  │       └── …
  └── 📂 workflow/
      ├── 🎯 grilling - Grill the user relentlessly about a plan, decision… (入口: workflow/grilling/SKILL.md)
      └── …
```

**关键点**：`registry/` 里的技能不会自动进入上下文。它们只有被路由器点名、并被显式读取时才会出现。

## 快速开始

```bash
git clone git@github.com:ShenQingchuan/skills.git ~/.agents/skills
cd ~/.agents/skills
python3 tools/sync_skills.py  # 类似 npm install：依据 sources.lock.json 一键恢复并安装全部技能
```

放好并同步后：

- 你的 Agent 默认**只感知到 `skills-router` 一个技能**；
- `registry/` 下的技能对它来说是隐身的，直到它真的需要。

验证一下（只需要 Python 3，无第三方依赖）：

```bash
python3 skills-router/scripts/list_skills.py
```

## 目录结构

```text
.
├── CATALOG.md                     ← 技能清单索引（含上游源链接 Credit）
├── skills-router/                 ← 唯一被 Agent 默认感知的技能
│   ├── SKILL.md                   ← 路由规则（刻意写得极短）
│   ├── scripts/
│   │   └── list_skills.py         ← 技能树探测：Agent 靠它「看目录」
│   └── registry/                  ← 技能库本体（类似 node_modules，第三方技能不入库）
│       ├── .gitignore             ← 自动精准忽略第三方下载产物，绝不误伤本地自建技能
│       ├── dev/
│       │   ├── agent-friendly/    ← 本地自建原创技能（受 Git 跟踪与保护）
│       │   └── ...                ← 第三方安装产物（本地存在但 Git 忽略）
│       ├── office/lark/           ← 飞书套件安装产物（Git 忽略）
│       ├── workflow/              ← 工作流技能（Git 忽略）
│       └── …
│
├── tools/                         ← 维护用工具，不参与 Agent 运行时
│   ├── sources.json               ← 上游清单（人写声明，类似 package.json）
│   ├── sources.lock.json          ← 同步状态（机器写锁，类似 package-lock.json）
│   ├── generate_catalog.py        ← CATALOG.md 自动生成脚本
│   └── sync_skills.py             ← 同步与安装脚本（类似 npm install）
│
└── .github/workflows/
    └── sync-skills.yml            ← 每日自动同步
```

**`registry/` 下怎么分类随你，多少层都行。** 唯一的硬约束来自 [Agent Skills 规范](https://agentskills.io/specification)：**一个 skill 的最小单元是一个目录**，目录里至少有一个 `SKILL.md`。

`scripts/`、`references/`、`assets/` 这些是目录内部的约定，属于技能自己的私事。`list_skills.py` 据此工作——见到 `SKILL.md` 就认定这是一个完整技能，不再往里看，所以技能内部的文件名不会泄露到技能树上。

Agent 的技能发现只认**仓库根目录下的第一层**。`tools/` 里没有 `SKILL.md`，`registry/` 也不是技能（它只是技能的上级分类），所以两者都不会被自动发现——这正是整个结构成立的原因。

## 日常使用

### 同步上游更新

```bash
python3 tools/sync_skills.py          # 拉取并更新 registry/
python3 tools/sync_skills.py --check  # 只看有没有更新（有则退出码 1）
```

也可以完全交给 CI：`.github/workflows/sync-skills.yml` 每天自动跑一次，有变化就自动提交回 `main`，没变化就什么也不做。你只需要 `git pull`。

同步的可靠性来自三条设计：**幂等**（跑一百遍结果一样）、**可重复**（内容只取决于上游 commit，不取决于时间或机器）、**可无人值守**（CI 里也能跑）。

### 新增一个技能或技能套件

本仓库支持两种引入方式，分别应对「单品挑选」与「整套镜像」：

#### 方式一：单点选品（Pick 模式，适合散装仓库）
上游仓库是个大杂烩，你只想要其中一两个技能时：
1. 在 `tools/sources.json` 的 `sources` 里登记仓库（如果还没有）。
2. 在 `install` 里指定具体的相对路径：
   ```json
   { "skill": "productivity/grilling", "from": "mattpocock", "to": "workflow/grilling" }
   ```

#### 方式二：套件整包镜像（Suite 模式，适合官方套件库）
像 `larksuite/cli` 这种官方自成体系的完整能力套件，内部技能紧密联动且随版本动态演进，不需要逐个维护清单：
1. 在 `sources` 里登记套件仓库与 `skillsDir`。
2. 在 `install` 里使用通配符 `"*"`，并指定归属分类目录：
   ```json
   { "skill": "*", "from": "larksuite", "to": "office/lark" }
   ```
3. 跑一次 `python3 tools/sync_skills.py`，上游全部技能会自动同步到 `registry/office/lark/` 下。未来上游无论新增、更名还是废弃子技能，同步脚本都会自动对齐，零人工维护成本。

### 移除一个技能或套件

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
3. **产物与源头分离（依赖不入库 No-Vendoring）** —— `registry/` 下的第三方技能是安装产物（就像前端项目的 `node_modules`），源头永远是上游仓库。Git 仓库只维护声明（`sources.json`）、事实与指纹（`sources.lock.json`）以及本地自创技能，其余第三方代码全部由脚本拉取并被 Git 忽略，保持仓库极致轻量纯粹。
4. **幂等优先** —— 同步跑一百遍和跑一遍结果相同。CI 才可以放心每天跑，你也才敢随时手动跑。
5. **冲突先在安装前解决** —— 装之前先比对同一话题的几个上游，明确各自分工；装进来之后靠「最多 1+1」的规则避免同时加载。

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
- [larksuite/cli](https://github.com/larksuite/cli) —— Lark / Feishu
- [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) —— Vercel Labs

## 许可

本仓库自身的代码（`skills-router/` 与 `tools/`）以 [MIT](./LICENSE) 授权。
`registry/` 下的第三方技能保留其上游许可证，详见各技能目录。

<div align="center">

由 [@ShenQingchuan](https://github.com/ShenQingchuan) 维护

</div>
