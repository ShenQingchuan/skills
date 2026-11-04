<div align="center">

# Skills

**让 Agent 更有条理地调度技能。**

一个基于「渐进式披露」理念的个人 Agent 技能治理框架。
常驻上下文的只有一个技能路由器，其余技能用到才载入。
内置跨平台 CLI 工具 `boss`，一行命令完成全套安装与技能同步。

[为什么](#为什么需要它) · [工作原理](#工作原理) · [一键安装与快速开始](#一键安装与快速开始) · [CLI 使用指引](#cli-使用指引-boss) · [目录结构](#目录结构) · [日常使用](#日常使用) · [Agent 指引](#agent-使用指引) · [设计原则](#设计原则)

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
- **③ 装载** —— 它按技能树输出的真实绝对路径读取 `SKILL.md`；文件里指向 `references/` 时再往下钻。

一次典型的查阅输出：

```text
📦 skills-router（技能路由中心根目录: /Users/admin/.agents/skills/registry）
  ├── 📂 dev/
  │   └── 📂 frontend/
  │       ├── 🎯 vue - Vue 3 Composition API, script setup macros… (入口: /Users/admin/.agents/skills/registry/.synced/dev/frontend/vue/SKILL.md)
  │       └── …
  └── 📂 workflow/
      ├── 🎯 grilling - Grill the user relentlessly about a plan, decision… (入口: /Users/admin/.agents/skills/registry/.synced/workflow/grilling/SKILL.md)
      └── …
```

**关键点**：`registry/` 里的技能不会自动进入上下文。它们只有被路由器点名、并被显式读取时才会出现。

## 一键安装与快速开始

本框架提供了一键安装脚本，**自动配置环境变量、自动管理脚本权限、自动同步完整技能库，全程零手动 `chmod`**：

### 1. 克隆仓库

```bash
git clone git@github.com:ShenQingchuan/skills.git ~/.agents/skills
cd ~/.agents/skills
```

### 2. 一键安装 `boss` CLI

- **macOS / Linux**：
  ```bash
  sh install.sh
  ```
  *(脚本会自动配置 `~/.local/bin` 软包装器、写入 shell profile 并同步技能库，全程无需 sudo)*

- **Windows**：
  直接双击 `install.cmd`，或在命令行运行：
  ```cmd
  install.cmd
  ```
  *(自动以 Bypass 策略调用安装，免除 PowerShell 执行策略阻拦，自动注册用户 PATH 并同步技能库。没有 Python 时会通过 uv 自动安装独立的 Python 3.12，无需管理员权限)*

### 3. 验证就绪

```bash
boss list-skills
```

你的 Agent 默认**只感知到 `skills-router` 这一个入口技能**；`registry/` 下的所有技能对它保持静默，直到真正需要时由路由器按需展开。

安装脚本会从 `config.example.json` 创建本机 `config.json`，并创建 `registry/.synced/` 与 `profiles/`。`config.json` 和私有 Profile 都被 Git 忽略，重复安装不会覆盖已有配置。

### Shell Tab 自动补全

安装脚本会自动配置 Tab 补全，支持子命令、常用参数和 `boss list-skills` 的技能分类目录：

- macOS / Linux：支持当前使用的 **zsh 或 Bash**
- Windows：支持 **PowerShell**

重新打开终端后生效，也可以在当前终端重新加载对应的 Shell 配置文件。已有安装需要补全功能时，重新执行对应平台的安装脚本即可：

```bash
sh install.sh
```

```powershell
.\install.ps1
```

补全脚本安装在用户目录的 `.local/share/boss/completions/`。所有安装脚本都可以重复执行：程序与补全脚本会更新到最新版，PATH 和 Shell 加载配置不会重复写入。

---

## CLI 使用指引 (`boss`)

框架提供自包含的 `boss` 命令，既方便人类日常打理，也是 Agent 调度的绝佳接口：

| 命令 | 职责说明 |
| :--- | :--- |
| `boss kanban [路径] [--port 5173]` | 启动当前项目的 `.agents/kanban/` 网页看板（Vite 驱动 HMR，无缓存残留，未安装时自动初始化） |
| `boss kanban stop [--port 5173]` | 停止看板服务（按端口释放进程，不留任何临时文件） |
| `boss code [路径] [--port 6063]` | 启动网页版 VS Code（coderaft），自动打开浏览器并预装常用插件；同一目录重复调用只重新激活，不换端口；闲置 2 小时自动关闭 |
| `boss code stop [--port 6063]` | 停止网页编辑器服务 |
| `boss list-skills` | 查看当前技能树，输出包含分类、一句话描述与入口路径（支持子路径过滤，如 `boss list-skills dev/`） |
| `boss sync-skills` | 同步默认 Profile 及 `config.json` 中启用的私有 Profile，对齐指纹锁定（支持 `--check` 纯只读检查） |
| `boss setup-runtime` | 一键部署/检查独立绿色沙盒引擎 (Node/Bun/uv/Python/rg，支持 `-s` 查看状态) |

---

## 目录结构

```text
.
├── config.example.json            ← 本机配置模板（Git 跟踪）
├── config.json                    ← 当前电脑启用的 Profile（Git 忽略，安装时自动创建）
├── sources.json                   ← 默认 Profile 的上游清单（Git 跟踪）
├── sources.lock.json              ← 默认 Profile 的同步锁定状态（Git 跟踪）
├── registry/
│   ├── dev/                       ← 共享手写技能，直接按逻辑分类存放（Git 跟踪）
│   ├── workflow/                  ← 共享手写技能（Git 跟踪）
│   └── .synced/                   ← 默认 Profile 的下载产物（Git 整体忽略）
├── profiles/                      ← 本机私有 Profile（Git 整体忽略）
│   └── company/                   ← 示例：一个公司 Profile
│       ├── sources.json
│       ├── sources.lock.json
│       └── registry/
│           ├── skills/                ← 手写、未分类技能
│           └── .synced/skills/        ← 下载、未分类技能
├── install.sh                     ← macOS / Linux 免 chmod 一键安装脚本
├── install.ps1                    ← Windows PowerShell 一键安装脚本
├── install.cmd                    ← Windows 双击即装批处理脚本
├── bin/
│   ├── boss                       ← 框架统一 CLI 入口
│   ├── skill_boss_profiles.py     ← Profile 路径与本机配置的统一约定
│   ├── install-python.ps1         ← Windows Python 检测与自动安装引导
│   ├── sync_skills.py             ← 依赖同步引擎
│   ├── setup-runtime.sh           ← Unix 运行环境部署引擎
│   └── setup-runtime.ps1          ← Windows 运行环境部署引擎
├── skills-router/                 ← 唯一被 Agent 默认感知的入口技能
│   ├── SKILL.md                   ← 路由规则（刻意写得极短）
│   └── scripts/
│       └── list_skills.py         ← 合并默认与已启用 Profile 的技能树
└── .github/workflows/
    └── sync-skills.yml            ← 每日自动同步默认 Profile
```

**`registry/` 下怎么分类随你，多少层都行。** 唯一的硬约束来自 [Agent Skills 规范](https://agentskills.io/specification)：**一个 skill 的最小单元是一个目录**，目录里至少有一个 `SKILL.md`。

`scripts/`、`references/`、`assets/` 这些是目录内部的约定，属于技能自己的私事。`list_skills.py` 据此工作——见到 `SKILL.md` 就认定这是一个完整技能，不再往里看，所以技能内部的文件名不会泄露到技能树上。

Agent 的技能发现只认**仓库根目录下的第一层**。`bin/` 里没有 `SKILL.md`，`registry/` 也不是技能（它只是技能的上级分类），所以两者都不会被自动发现——这正是整个结构成立的原因。

手写技能和下载产物共享同一套逻辑分类。例如 `registry/dev/frontend/my-skill/` 与 `registry/.synced/dev/frontend/vue/` 会合并显示在 `dev/frontend/` 下；`.synced/` 只是存储细节，不会成为逻辑分类。同一逻辑技能路径出现冲突时，路由会直接报错。每个技能条目都会输出可直接读取的真实绝对路径，因此 router 主技能不需要理解这些存储映射。

### 本机配置与私有 Profile

顶层就是默认 Profile；`profiles/<name>/` 则使用完全相同的清单、锁文件和 `registry/` 结构。默认 Profile 始终加载，额外 Profile 由本机 `config.json` 启用。在技能树中，私有 Profile 以自身名称作为顶层命名空间，例如 `profiles/company/registry/dev/demo/` 显示为 `company/dev/demo/`，不会把内部分类提升到共享根目录。`registry/skills/` 和 `registry/.synced/skills/` 分别存放手写与下载的未分类技能；它们直接显示在所属 Profile 名称下，不额外增加 `skills/` 分类。如果需要更细的分类，可以使用 `dev/`、`workflow/` 等其他目录，手写与下载仍然分开放置：

```json
{
  "activeProfiles": ["company"]
}
```

公司技能清单只需放在 `profiles/company/sources.json`，其锁文件和下载目录由同步程序维护。家里电脑没有该目录且未启用该 Profile，就只同步和展示共享技能。

根目录 `.gitignore` 是人工维护的固定规则，程序不会改写：

```gitignore
/config.json
/profiles/
/registry/.synced/
```

因此 GitHub 只展示共享清单、共享锁文件和手写技能；本机配置、私有 Profile 与下载产物都不会进入远端。

## 日常使用

### 同步上游更新

```bash
boss sync-skills          # 更新默认与已启用 Profile 的 registry/.synced/
boss sync-skills --check  # 只检查全部已加载 Profile（有更新则退出码 1，不写文件）
```

也可以完全交给 CI：`.github/workflows/sync-skills.yml` 每天自动跑一次，有变化就自动提交回 `main`，没变化就什么也不做。你只需要 `git pull`。

同步的可靠性来自三条设计：**幂等**（跑一百遍结果一样）、**可重复**（内容只取决于上游 commit，不取决于时间或机器）、**可无人值守**（CI 里也能跑）。

### 新增一个技能或技能套件

本仓库支持两种引入方式，分别应对「单品挑选」与「整套镜像」：

#### 方式一：单点选品（Pick 模式，适合散装仓库）
上游仓库是个大杂烩，你只想要其中一两个技能时：
1. 在 `sources.json` 的 `sources` 里登记仓库（如果还没有）。
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
3. 跑一次 `boss sync-skills`，上游全部技能会自动同步到 `registry/.synced/office/lark/` 下。未来上游无论新增、更名还是废弃子技能，同步脚本都会自动对齐，零人工维护成本。

### 移除一个技能或套件

把 `install` 里对应的那一行删掉，再跑一次同步脚本。脚本会连目录一起清理，让对应 Profile 的 `registry/.synced/` 始终等于清单。

## Agent 使用指引

> 这一节同时是 [`AGENTS.md`](./AGENTS.md) 的内容——本仓库的 README 就直接充当 Agent 的工作须知。

### 运行时：需要技能时

1. 跑 `boss list-skills`（或 `python3 skills-router/scripts/list_skills.py`）。
2. 按描述挑最匹配的 **1 个**；确有互补需要时最多再加 1 个（例如「架构规约」配「API 参考」）。
3. **只**读选中技能目录下的 `SKILL.md`；其中若指向 `references/`、`reference/` 或 `scripts/`，再按需下钻。

硬性约束：

- 不要一次性读完 `registry/` 下所有 `SKILL.md`。
- 不要把 `registry/` 下的技能批量加载进上下文——这会直接毁掉这个仓库存在的意义。
- `registry/.synced/` 中由 `sources.json` 管理的目录是**产物**，不要手改；下次同步会原样覆盖。
- 本仓库原创技能的 Node.js 脚本、文档示例与验证命令统一使用 `.runtime/bin/node`，npm/npx 同样使用 `.runtime/bin/` 内的垫片；未就绪先执行 `boss setup-runtime`，不调用系统 Node。

### 修改时：要动这个仓库

| 你想做的事 | 推荐做法 |
| --- | --- |
| 新增 / 移除第三方技能 | 改 `sources.json` 后执行 `boss sync-skills` |
| 升级上游技能 | 跑 `boss sync-skills` |
| 本地新建原创技能 | 在 `registry/` 对应分类下新建即可，受 Git 自动跟踪保护 |
| 调整路由规则 | `skills-router/SKILL.md` |
| 调整技能树展示 | `skills-router/scripts/list_skills.py` |
| 调整底层同步逻辑 | `bin/sync_skills.py` |
| 部署绿色运行时沙盒 | 跑 `boss setup-runtime` |
| 启动项目任务看板 | 跑 `boss kanban [项目路径]` |
| 调整自动同步节奏 | `.github/workflows/sync-skills.yml` |

`sources.lock.json` 由脚本自动生成，不要手改。它记录上游 commit 与每个技能目录的内容指纹，同步脚本靠它判断「有没有变」。

运行自动化测试：

```bash
python3 -m unittest discover -s tests -v
```

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
3. **产物与源头分离（依赖不入库 No-Vendoring）** —— 第三方技能统一下载到 `registry/.synced/`，就像前端项目的 `node_modules`。Git 仓库只维护声明（`sources.json`）、事实与指纹（`sources.lock.json`）以及 `registry/` 下的原创技能；忽略规则固定在目录边界上，不需要程序维护。
4. **共享与私有隔离** —— 顶层默认 Profile 对大家一致，`profiles/` 和 `config.json` 只保留在本机，公司能力不会进入公开仓库。
5. **幂等优先** —— 同步跑一百遍和跑一遍结果相同。CI 才可以放心每天跑，你也才敢随时手动跑。
6. **冲突先在安装前解决** —— 装之前先比对同一话题的几个上游，明确各自分工；装进来之后靠「最多 1+1」的规则避免同时加载。

## 参与贡献

这是一个高度个人化的技能库（比较 opinionated），服务于个人的工作习惯与 Agent 架构思考。

- **不接收 Pull Request**：本项目不合并外部代码 PR，请勿提交 Pull Request；
- **欢迎提 Issue**：如果你在使用过程中发现了 Bug、规则缺陷或有建设性的想法，非常欢迎在 [Issues](../../issues) 区讨论与反馈问题；
- **Feel free to Fork**：代码完全开源，欢迎自由 Fork 到你自己的账号下进行二次开发与个性化定制。

## 致谢

技能库的内容来自这些优秀的开源项目，版权归各自作者所有：

- [antfu/skills](https://github.com/antfu/skills) —— Anthony Fu
- [vuejs-ai/skills](https://github.com/vuejs-ai/skills) —— vuejs-ai
- [mattpocock/skills](https://github.com/mattpocock/skills) —— Matt Pocock
- [larksuite/cli](https://github.com/larksuite/cli) —— Lark / Feishu
- [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) —— Vercel Labs

## 许可

本仓库自身的代码（`skills-router/` 与 `bin/`）以 [MIT](./LICENSE) 授权。
`registry/.synced/` 下的第三方技能保留其上游许可证，详见各技能目录。

<div align="center">

由 [@ShenQingchuan](https://github.com/ShenQingchuan) 维护

</div>
