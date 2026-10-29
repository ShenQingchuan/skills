# workflow

本目录下的技能由 `python3 tools/sync_skills.py` 从上游仓库同步而来。
**不要手改这里的文件**——下次同步会原样覆盖。要改就改上游，或把 `tools/sources.json` 里的 `repo` 换成你自己的 fork。

## 上游

| 上游 | 定位 |
| --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock 从自己 `.agents` 目录整理出的技能套件，按 `engineering` / `productivity` / `misc` 分组 |

这个上游的技能目录是**三层结构**（`skills/<分组>/<技能>/`），所以 `tools/sources.json` 里
`skill` 字段写的是带子目录的相对路径，例如 `productivity/grilling`。

## 已安装技能

| 技能 | 上游路径 | 作用 |
| --- | --- | --- |
| `grilling` | `productivity/grilling` | 把模糊的想法逼成共识。把决策组织成一棵「设计树」，按轮次问完当前**前沿**（前置条件已定的那些问题），每个问题都附上推荐答案，等用户答复后再重算前沿。事实由 Agent 自己查，决策交给人 |
| `writing-for-agents` | `productivity/writing-for-agents` | 写给 Agent 消费的文档怎么写：上下文指针、两种负载（上下文负载 / 认知负载）、信息层级、渐进式披露、完成判据 |

这两个是**元技能**：不解决具体业务问题，而是改善你和 Agent 协作的过程本身。
`grilling` 用在动手之前，`writing-for-agents` 用在写文档的时候。

## 和本仓库的关系

`writing-for-agents` 的 `SKILL-MECHANICS.md` 里有一节专门讲 **router skills**，
和本仓库的 `skills-router` 是同一个思路的两个变种：

| | 解决谁的负载 | 机制 |
| --- | --- | --- |
| mattpocock 的 router | **人的**认知负载 | 面向 user-invoked 技能。这类技能没有 `description`，模型够不着，只有人能唤起；于是用一个 router 让人「只记一个」 |
| 本仓库的 `skills-router` | **模型的**上下文负载 | 面向 model-invoked 技能。它们的 `description` 会常驻系统提示，于是把技能藏进 `registry/`，改成用工具按需查阅、按需读取 |

两者不冲突，可以同时成立。本仓库自己的 `README.md`、`AGENTS.md` 和 `skills-router/SKILL.md`
就是按 `writing-for-agents` 的规范写的。

## 怎么更新

```bash
python3 tools/sync_skills.py          # 本地手动同步
python3 tools/sync_skills.py --check  # 只看有没有更新，退出码 1 表示有
```

或交给 CI：`.github/workflows/sync-skills.yml` 每天自动同步。

## 怎么加新技能

1. 在 `tools/sources.json` 的 `sources` 里登记仓库（没有的话）。
2. 在 `install` 里加一行，`skill` 写上游 `skills/` 下的相对路径：

   ```json
   { "skill": "engineering/tdd", "from": "mattpocock", "to": "workflow/tdd" }
   ```

3. 跑一次 `python3 tools/sync_skills.py`。

上游 `engineering` / `misc` / `in-progress` 分组下的技能也可以用同样方式引进来。
