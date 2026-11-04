# 001 统一 Fskillhub 下载方法

- 状态：done
- 关联规格：无
- 关联产品卡片：无

## 背景与目标

公司技能由 Fskillhub 直接安装时，只有工具私有的 `.fskillhub/` 记录，Profile 的 `sources.json` 无法声明和重建这些依赖。本次改造让 `boss sync-skills` 统一识别 Git 与 Fskillhub 来源，并统一维护安装锁。

## 范围

- 为来源增加命名下载方法，Git 保持默认和完全兼容。
- 增加 Fskillhub 临时目录下载、版本解析、内容指纹与只读检查。
- 将公司 Profile 中已有的三个 Fskillhub 技能迁回 `sources.json` 声明。
- 补齐自动化测试、使用文档并重新执行安装。

不包含任意 shell 命令模板，也不改变技能路由结构。

## 技术方案

`method: "fskillhub"` 选择独立下载器。下载器使用仓库 `.runtime` 中的 npx，在临时工作目录调用公司工具，验证 `SKILL.md` 与来源信息，移除带时间戳的工具元数据后交给统一同步流程。`sources.lock.json` 记录实际版本和内容指纹；`--check` 只写临时目录。

## 实施清单

- [x] 确认 Fskillhub CLI 参数与安装目录协议
- [x] 实现下载器和统一同步分派
- [x] 补齐测试与文档
- [x] 迁移本机 futu Profile
- [x] 全量验证并重新安装

## 风险与回滚

公司工具不可用或认证失效时保留旧锁和旧技能，并明确提示需要同步。Git 下载路径继续沿用原有逻辑。回滚时移除新下载器及清单中的 Fskillhub 条目即可，已下载目录可保留。

## 验证

- `python3 -m unittest discover -s tests -v`
- `boss sync-skills --check`
- `sh install.sh`
- `boss list-skills futu/`

## 完成记录

- 11 项自动化测试全部通过，覆盖声明安装、版本参数、幂等、只读检查、失败保留和未知方法校验。
- `install.sh` 完整执行成功，默认 Profile 与 futu Profile 均完成同步。
- `fservice-cli`、`frpc-skills`、`observability-skills` 均由 futu Profile 的 `sources.json` 声明，并写入统一 `sources.lock.json`。
- 全量 `boss sync-skills --check` 返回全部最新，`boss list-skills futu/` 能正确展示公司技能。
- 旧 `.synced/.fskillhub/` 记录已清理，正式技能目录不再包含带安装时间的工具元数据。
