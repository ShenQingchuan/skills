---
name: write-merge-request-description
description: 根据真实代码变更撰写并更新图文并茂的公司 GitLab Merge Request 描述，组合 draw-with-pele 生成 SVG、Bun.WebView 转成 PNG、persist-img-by-gitlab 持久化图片。当用户要求写 MR 描述、补充架构图或流程图、避免 GitLab 自带 Mermaid.js 渲染时使用。
---

# Write GitLab MR Description

负责理解变更、组织描述、调用画图与存图技能、更新目标 MR。不要自行实现 Mermaid 渲染，也不要在最终描述中保留会触发 GitLab 自带 Mermaid.js 的代码块。

## 技能分工

- **`/draw-with-pele`**：把需要表达的架构、流程、调用链或状态变化画成 SVG。需要图示时直接调用此技能，不额外研究或展开 Pele 的用法。
- **`/persist-img-by-gitlab`**：把本地图片上传到合适的 GitLab 项目，取得可嵌入 MR 的持久链接。
- **本技能**：读取真实变更，写清楚评审所需信息，把 SVG 转成适合 MR 内嵌的 PNG，组织最终描述并写回 MR。

## 工作流程

1. **锁定目标**：确认 MR IID 与项目，不猜测。读取 MR 当前描述、源/目标分支和实际 diff，避免覆盖已有但仍有效的内容。
2. **理解变更**：以代码事实为准，识别行为变化、关键实现、兼容性、风险和验证证据；不要只根据提交标题扩写。
3. **规划图文**：先列评审者需要快速看懂的重点，再决定用架构图、流程图、时序图或前后对比图表达。默认至少加入一张有助于评审的图；纯错别字等确无图示价值的变更不要硬画装饰图。
4. **生成 SVG**：把明确的图示目标和 Mermaid 内容交给 `/draw-with-pele`，取得本地 SVG。
5. **转成 PNG**：用本技能的 `scripts/svg-to-png.ts` 转换后再内嵌；不要直接把 SVG 嵌入 MR。转换只依赖 Bun 内置 WebView，不安装 Playwright 或第三方图片库。
6. **持久化图片**：调用 `/persist-img-by-gitlab` 上传 PNG。图床项目默认使用 MR 所在项目，避免跨项目权限问题；使用独立长期项目时，确保所有 MR 读者都有查看权限。
7. **组装描述**：在对应文字附近插入 `![准确的图片说明](图片绝对URL)`。图负责减少理解成本，文字负责说明原因、影响和验证，不要用图片替代必要文字。
8. **检查并更新**：核对事实、链接、目标 MR 与最终 Markdown，再写回用户指定的 MR。

SVG 转 PNG 命令：

```bash
bun "$HOME/.agents/skills/registry/writing/write-merge-request-description/scripts/svg-to-png.ts" \
  diagram.svg diagram.png
```

## 描述组织

按变更实际内容选择小节，不硬凑空标题：

- **变更摘要**：解决了什么问题，为什么需要改。
- **关键实现**：主要模块、调用链或数据流如何变化，配图放在对应段落。
- **验证结果**：列真实执行过的测试与关键结果；没跑的不要写成已验证。
- **兼容性与风险**：接口、配置、数据、部署或回滚注意事项；没有则省略。

## 更新命令

将最终内容保存为本地 Markdown 文件后：

```bash
glab mr update MR_IID \
  --repo group/project \
  --description-file description.md \
  --yes
```

非当前认证实例或上下文不明确时，使用完整项目 URL 作为 `--repo`，或正确设置 `GITLAB_HOST`。只生成草稿时不执行更新命令。

## 完成前检查

- 描述与实际 diff 一致，旧描述中仍有效的背景、验证或注意事项没有被误删。
- 图示由 `/draw-with-pele` 生成，上传用于内嵌的是 PNG，不是 SVG。
- 图片已由 `/persist-img-by-gitlab` 上传，放在对应段落内，替代文字准确，链接使用绝对 URL。
- 最终描述没有 ```` ```mermaid ```` 代码块，不依赖 GitLab 自带 Mermaid.js。
- 不包含 Token、未脱敏敏感信息或读者无权访问的图片。
