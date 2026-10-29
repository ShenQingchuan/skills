# Skills Catalog

本仓库已收纳的完整技能索引目录。通过单一入口 `skills-router` 渐进式披露，避免平铺污染 Agent 上下文。

- **外部引入技能**：均提供指向原仓库和原始 `SKILL.md` 的链接以标明版权与来源（Credit）。
- **本地自建技能**：标记为 `Local（自建）`，无外部链接。

## Core & Routing (核心路由)

| 技能 (Skill) | 简介 (Description) | 来源 (Source) |
| --- | --- | --- |
| **skills-router** | 技能路由中心。处理专业领域任务或系统工作流前，探查并按需加载具体技能。 | Local（自建） |

## Browser & Automation (浏览器自动化)

| 技能 (Skill) | 简介 (Description) | 来源 (Source) |
| --- | --- | --- |
| [agent-browser](https://github.com/vercel-labs/agent-browser/blob/HEAD/skills/agent-browser/SKILL.md) | Browser automation CLI for AI agents. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking ... | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) |

## Frontend Development (前端开发 / Vue 生态)

| 技能 (Skill) | 简介 (Description) | 来源 (Source) |
| --- | --- | --- |
| [create-adaptable-composable](https://github.com/vuejs-ai/skills/blob/HEAD/skills/create-adaptable-composable/SKILL.md) | Create a library-grade Vue composable that accepts maybe-reactive inputs (MaybeRef / MaybeRefOrGetter) so callers can pass a plain value, ref, or getter. Nor... | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) |
| [pinia](https://github.com/antfu/skills/blob/HEAD/skills/pinia/SKILL.md) | Pinia official Vue state management library, type-safe and extensible. Use when defining stores, working with state/getters/actions, or implementing store pa... | [antfu/skills](https://github.com/antfu/skills) |
| [pnpm](https://github.com/antfu/skills/blob/HEAD/skills/pnpm/SKILL.md) | Node.js package manager with strict dependency resolution. Use when running pnpm specific commands, configuring workspaces via pnpm-workspace.yaml, or managi... | [antfu/skills](https://github.com/antfu/skills) |
| [unocss](https://github.com/antfu/skills/blob/HEAD/skills/unocss/SKILL.md) | UnoCSS instant atomic CSS engine, superset of Tailwind CSS. Use when configuring UnoCSS, writing utility rules, shortcuts, or working with presets like Wind,... | [antfu/skills](https://github.com/antfu/skills) |
| [vite](https://github.com/antfu/skills/blob/HEAD/skills/vite/SKILL.md) | Vite build tool configuration, plugin API, SSR, and Vite 8 Rolldown migration. Use when working with Vite projects, vite.config.ts, Vite plugins, or building... | [antfu/skills](https://github.com/antfu/skills) |
| [vitepress](https://github.com/antfu/skills/blob/HEAD/skills/vitepress/SKILL.md) | VitePress static site generator powered by Vite and Vue. Use when building documentation sites, configuring themes, or writing Markdown with Vue components. | [antfu/skills](https://github.com/antfu/skills) |
| [vitest](https://github.com/antfu/skills/blob/HEAD/skills/vitest/SKILL.md) | Vitest fast unit testing framework powered by Vite with Jest-compatible API. Use when writing tests, mocking, configuring coverage, or working with test filt... | [antfu/skills](https://github.com/antfu/skills) |
| [vue](https://github.com/antfu/skills/blob/HEAD/skills/vue/SKILL.md) | Vue 3 Composition API, script setup macros, reactivity system, and built-in components. Use when writing Vue SFCs, defineProps/defineEmits/defineModel, watch... | [antfu/skills](https://github.com/antfu/skills) |
| [vue-best-practices](https://github.com/vuejs-ai/skills/blob/HEAD/skills/vue-best-practices/SKILL.md) | MUST be used for Vue.js tasks. Strongly recommends Composition API with `<script setup>` and TypeScript as the standard approach. Covers Vue 3, SSR, Volar, v... | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) |
| [vue-debug-guides](https://github.com/vuejs-ai/skills/blob/HEAD/skills/vue-debug-guides/SKILL.md) | Vue 3 debugging and error handling for runtime errors, warnings, async failures, and SSR/hydration issues. Use when diagnosing or fixing Vue issues. | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) |
| [vue-pinia-best-practices](https://github.com/vuejs-ai/skills/blob/HEAD/skills/vue-pinia-best-practices/SKILL.md) | Pinia stores, state management patterns, store setup, and reactivity with stores. | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) |
| [vue-router-best-practices](https://github.com/vuejs-ai/skills/blob/HEAD/skills/vue-router-best-practices/SKILL.md) | Vue Router 4 patterns, navigation guards, route params, and route-component lifecycle interactions. | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) |
| [vue-testing-best-practices](https://github.com/vuejs-ai/skills/blob/HEAD/skills/vue-testing-best-practices/SKILL.md) | Use for Vue.js testing. Covers Vitest, Vue Test Utils, component testing, mocking, testing patterns, and Playwright for E2E testing. | [vuejs-ai/skills](https://github.com/vuejs-ai/skills) |

## Office & Collaboration (办公协同 / 飞书套件)

| 技能 (Skill) | 简介 (Description) | 来源 (Source) |
| --- | --- | --- |
| [lark-approval](https://github.com/larksuite/cli/blob/HEAD/skills/lark-approval/SKILL.md) | 飞书审批：查询和处理审批待办/已办/实例，搜索可发起审批定义、查看定义详情并发起原生审批实例。当用户要处理审批任务、查看审批实例、搜索或发起审批时使用。审批待办不是飞书任务；非审批类待办走 lark-task。不负责创建审批定义；三方审批定义不走原生提单。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-apps](https://github.com/larksuite/cli/blob/HEAD/skills/lark-apps/SKILL.md) | 妙搭（Spark/Miaoda）应用开发与托管：应用创建、本地全栈开发、云端生成迭代、创意设计（UI mockup / 可交互原型 / 线框图 / 落地页 / 仪表盘 / 幻灯片 deck / 视觉探索）、AI相关能力和飞书平台能力或者其他外部能力集成、日志/Trace/监控指标/PV/UV 查询、环境变量管理、... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-attendance](https://github.com/larksuite/cli/blob/HEAD/skills/lark-attendance/SKILL.md) | 飞书考勤打卡：查询自己的考勤打卡记录 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-base](https://github.com/larksuite/cli/blob/HEAD/skills/lark-base/SKILL.md) | 飞书多维表格（Base）操作：建表、字段、记录、视图、统计、公式/lookup、表单、仪表盘、应用模式（BaseApp/AppMode 页面与组件）、Workspace 目录、workflow、角色权限、模板中心（多维表格模板分类/列表/搜索）；遇到 Base/多维表格/bitable、BaseApp/AppMo... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-calendar](https://github.com/larksuite/cli/blob/HEAD/skills/lark-calendar/SKILL.md) | 飞书日历：管理日历日程和会议室。查看/搜索日程、创建/更新日程、管理参会人、查询忙闲和推荐时段、预定会议室。当用户需要查看日程安排、创建/修改会议、查询/预定会议室时使用。不负责：查询过去的视频会议记录（走 lark-meeting）、待办任务（走 lark-task）。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-contact](https://github.com/larksuite/cli/blob/HEAD/skills/lark-contact/SKILL.md) | 飞书 / Lark 通讯录:按姓名 / 邮箱解析成 open_id,或按 open_id 反查姓名 / 部门 / 邮箱 / 联系方式 / 个人状态 / 签名,以及按关键词搜索当前用户可见的机器人 / 智能体(agent)。当用户提到一个名字要下一步发消息 / 排日程,或拿到 open_id 想查具体信息时使用。不... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-doc](https://github.com/larksuite/cli/blob/HEAD/skills/lark-doc/SKILL.md) | 飞书云文档（Docx / Wiki）内容操作：读取、创建、编辑文档，插入或下载图片附件，以及操作思维笔记。用户提供文档 URL/token（包括 doubao.com 的 /docx/、/wiki/）时使用；按 URL 路径/token 而非域名路由；`/page/<token>` 是妙搭应用，非飞书云文档。文档... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-drive](https://github.com/larksuite/cli/blob/HEAD/skills/lark-drive/SKILL.md) | 飞书云空间（云盘/云存储）：管理 Drive 文件和文件夹，包含上传/下载、创建文件夹、复制/移动/删除、查看元数据、查询权限设置、评论/权限/订阅、标题、版本、飞书文档密级标签（secure labels）和本地文件导入。用户需要整理云盘目录、处理云空间资源 URL/token、判断链接类型/真实 token/... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-event](https://github.com/larksuite/cli/blob/HEAD/skills/lark-event/SKILL.md) | Lark/Feishu real-time event listening / subscribing / consuming: stream events as NDJSON via `lark-cli event consume <EventKey>` (covers IM messages/reaction... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-im](https://github.com/larksuite/cli/blob/HEAD/skills/lark-im/SKILL.md) | 飞书即时通讯：收发消息和管理群聊。发送和回复消息、搜索聊天记录、管理群聊成员、上传下载图片和文件、管理表情回复、发送应用内/短信/电话加急、发送和处理交互卡片（Interactive Card）、监听卡片按钮回调（card.action.trigger）。当用户需要发消息、查看或搜索聊天记录、下载聊天中的文件、查... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-mail](https://github.com/larksuite/cli/blob/HEAD/skills/lark-mail/SKILL.md) | 飞书邮箱：Use when user mentions 起草邮件、写邮件、草稿、发送/回复/转发邮件、查阅邮件、看邮件、搜索邮件、邮件文件夹、邮件标签、邮件联系人、监听新邮件、邮件收信规则等；use for mail/email intent only. Do not use for docs/sheets/ca... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-markdown](https://github.com/larksuite/cli/blob/HEAD/skills/lark-markdown/SKILL.md) | 飞书 Markdown：查看、创建、上传、编辑和比较飞书中的原生 Markdown 文件。当用户要操作飞书 Markdown 文件，或比较其远端版本及本地草稿时使用。纯本地 Markdown 文件操作不触发本 skill。不负责将 Markdown 导入为飞书在线文档，也不负责文件搜索、权限、评论、移动、删除等云... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-meeting](https://github.com/larksuite/cli/blob/HEAD/skills/lark-meeting/SKILL.md) | 飞书视频会议：查询会议记录与会议产物(纪要/逐字稿/妙记)、妙记搜索/上传/下载/编辑、机器人参与会议；查询进行中的会议、实时会议内容(发言/聊天/共享文档)问答(会上/会里)、发送会中聊天/表情；基于 meeting_id、meeting_no、event_id、note_id、minute_token、vc-... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-minutes](https://github.com/larksuite/cli/blob/HEAD/skills/lark-minutes/SKILL.md) | 仅当用户或上游配置显式指定 lark-minutes 时使用，相关请求统一交由 lark-meeting 技能处理。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-note](https://github.com/larksuite/cli/blob/HEAD/skills/lark-note/SKILL.md) | 仅当用户或上游配置显式指定 lark-note 时使用，相关请求统一交由 lark-meeting 技能处理。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-okr](https://github.com/larksuite/cli/blob/HEAD/skills/lark-okr/SKILL.md) | 飞书 OKR：管理目标与关键结果。查看和编辑 OKR 周期、目标、关键结果、对齐关系、量化指标和进展记录。当用户需要查看或创建 OKR、管理目标和关键结果、查看对齐关系时使用。不负责：待办任务管理（lark-task）、日程/会议安排（lark-calendar）、绩效评估 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-openapi-explorer](https://github.com/larksuite/cli/blob/HEAD/skills/lark-openapi-explorer/SKILL.md) | 飞书/Lark 原生 OpenAPI 探索：从官方文档库中挖掘未经 CLI 封装的原生 OpenAPI 接口。当用户的需求无法被现有 lark-* skill 或 lark-cli 已注册命令满足，需要查找并调用原生飞书 OpenAPI 时使用。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-shared](https://github.com/larksuite/cli/blob/HEAD/skills/lark-shared/SKILL.md) | Use for lark-cli setup/auth tasks: auth login/status/logout, user vs bot identity, business-domain permissions (--domain, including all/docs/drive), missing ... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-sheets](https://github.com/larksuite/cli/blob/HEAD/skills/lark-sheets/SKILL.md) | 飞书电子表格：创建和操作电子表格。支持工作表与行列结构（增删/合并/尺寸/隐藏/冻结/分组）、单元格读写（值/公式/样式/批注/单元格图片）、区域复制移动排序填充、查找替换、批量更新，图表、透视表、条件格式、筛选器与筛选视图、下拉列表、迷你图、浮动图片等对象的创建与维护，以及公式校验、历史版本回滚、本地 Exce... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-skill-maker](https://github.com/larksuite/cli/blob/HEAD/skills/lark-skill-maker/SKILL.md) | 创建 lark-cli 的自定义 Skill。当用户需要把飞书 API 操作封装成可复用的 Skill（包装原子 API 或编排多步流程）时使用。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-slides](https://github.com/larksuite/cli/blob/HEAD/skills/lark-slides/SKILL.md) | 飞书幻灯片：创建和编辑幻灯片。创建演示文稿、读取幻灯片内容、管理幻灯片页面（创建、删除、读取、局部替换）。当用户需要创建或编辑幻灯片、读取或修改单个页面时使用。当用户给出 doubao.com 的 /slides/ URL/token 时，也应直接使用本 skill，不要因为域名不是飞书而回退到 WebFetch... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-task](https://github.com/larksuite/cli/blob/HEAD/skills/lark-task/SKILL.md) | 飞书任务：管理任务、清单和任务智能体。创建待办任务、查看和更新任务状态、拆分子任务、组织任务清单、分配协作成员、上传任务附件、注册或注销任务智能体、更新任务智能体的主页数据、写入智能体任务记录。当用户需要创建待办事项、查看任务列表、跟踪任务进度、管理项目清单或给他人分配任务、为任务上传附件文件、注册注销任务智能体... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-vc](https://github.com/larksuite/cli/blob/HEAD/skills/lark-vc/SKILL.md) | 仅当用户或上游配置显式指定 lark-vc 时使用，相关请求统一交由 lark-meeting 技能处理。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-vc-agent](https://github.com/larksuite/cli/blob/HEAD/skills/lark-vc-agent/SKILL.md) | 仅当用户或上游配置显式指定 lark-vc-agent 时使用，相关请求统一交由 lark-meeting 技能处理。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-whiteboard](https://github.com/larksuite/cli/blob/HEAD/skills/lark-whiteboard/SKILL.md) | 飞书画板：查询和编辑飞书云文档中的画板。支持导出画板为预览图片、导出原始节点结构、使用多种格式更新画板内容。 当用户需要查看画板内容、导出画板图片、编辑画板时使用此 skill。不负责：飞书云文档内容编辑（lark-doc）、文档内嵌电子表格/Base（lark-sheets / lark-base）。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-wiki](https://github.com/larksuite/cli/blob/HEAD/skills/lark-wiki/SKILL.md) | 飞书知识库：管理知识空间、空间成员和文档节点。创建和查询知识空间、查看和管理空间成员、管理节点层级结构、在知识库中组织文档和快捷方式。当用户需要在知识库中查找或创建文档、浏览知识空间结构、查看或管理空间成员、移动或复制节点时使用。当用户给出 doubao.com 的 /wiki/ URL/token 时，也应直接... | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-workflow-meeting-summary](https://github.com/larksuite/cli/blob/HEAD/skills/lark-workflow-meeting-summary/SKILL.md) | 会议纪要整理工作流：汇总指定时间范围内的会议纪要并生成结构化报告。当用户需要整理会议纪要、生成会议周报、回顾一段时间内的会议内容时使用。 | [larksuite/cli](https://github.com/larksuite/cli) |
| [lark-workflow-standup-report](https://github.com/larksuite/cli/blob/HEAD/skills/lark-workflow-standup-report/SKILL.md) | 日程待办摘要：编排 calendar +agenda 和 task +get-my-tasks，生成指定日期的日程与未完成任务摘要。适用于了解今天/明天/本周的安排。 | [larksuite/cli](https://github.com/larksuite/cli) |

## Workflow & Engineering (工作流与工程)

| 技能 (Skill) | 简介 (Description) | 来源 (Source) |
| --- | --- | --- |
| [grilling](https://github.com/mattpocock/skills/blob/HEAD/skills/productivity/grilling/SKILL.md) | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. | [mattpocock/skills](https://github.com/mattpocock/skills) |
| [writing-for-agents](https://github.com/mattpocock/skills/blob/HEAD/skills/productivity/writing-for-agents/SKILL.md) | Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md. | [mattpocock/skills](https://github.com/mattpocock/skills) |

