# Clarify Deepagents Secondary Development

- Time: 2026-07-01T13:46:57+08:00
- Project: deepagents

## Prompt

你的意思是让我在这个开源项目中进行二次开发吗?

## AI Response

不一定。

我的建议是：先把这个开源项目当作“参考实现 + 技术底座”来研究；如果你想快速做出产品，可以 fork 后二次开发 `libs/code`；如果你想做独立产品，建议新建自己的仓库/包，只依赖 `deepagents` SDK，并参考 `deepagents-code` 的架构。

推荐路径：独立新项目 + 复用 Deep Agents SDK + 借鉴 `libs/code/deepagents_code`，这样后续产品边界、发布、品牌和定制都会更清晰。
