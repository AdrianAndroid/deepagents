# Skills Loading Implementation

- Time: 2026-07-02T20:12:40+08:00
- Project: deepagents

## Prompt

这个项目是如何实现skills加载的<environment_details>
Current time: 2026-07-02T20:12:40+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Open tabs:
  资料文档/通过1panel创建pypiserver详细步骤.md
  资料文档/1Panel 搭建私有 PyPI 仓库最终落地文档（解决403_405报错、永久可用）.md
  libs/code/deepagents_code/remote_client.py
</environment_details>

## AI Response

Skills 加载分两层：

1. SDK 层：`SkillsMiddleware`
   - 入口：`libs/deepagents/deepagents/middleware/skills.py:748`
   - `before_agent`/`abefore_agent` 在每个会话首次执行前扫描 `sources`，读取每个子目录下的 `SKILL.md`，解析 YAML frontmatter 得到 `name`、`description`、`allowed_tools` 等元数据。
   - 后加载的 source 覆盖先加载的同名 skill，见 `libs/deepagents/deepagents/middleware/skills.py:968`。
   - `wrap_model_call` 把 skill 列表注入 system prompt，但只注入元数据和路径；完整内容由模型按需 `read_file` 读取，见 `libs/deepagents/deepagents/middleware/skills.py:913`。
   - `create_deep_agent(..., skills=[...])` 会把 `SkillsMiddleware` 加进主 agent、默认 general-purpose subagent、以及声明了 `skills` 的子 agent，见 `libs/deepagents/deepagents/graph.py:653`、`libs/deepagents/deepagents/graph.py:728`、`libs/deepagents/deepagents/graph.py:776`。

2. dcode 层：本地目录发现 + slash command 调用
   - 技能目录定义在 `libs/code/deepagents_code/config.py:2278`：内置、用户、项目、`.agents`、`.claude`。
   - agent 构建时启用 `SkillsMiddleware`，source 优先级为 built-in -> user -> project -> claude，见 `libs/code/deepagents_code/agent.py:1505`。
   - UI 启动时 `_discover_skills` 扫描技能并生成 `/skill:<name>` 自动补全，见 `libs/code/deepagents_code/app.py:3017`。
   - `/skill:<name>` 会直接读取完整 `SKILL.md`，包装成用户消息发送给 agent，而不是只靠 prompt 中的 metadata，见 `libs/code/deepagents_code/app.py:7682` 和 `libs/code/deepagents_code/skills/invocation.py:68`。

技能目录结构是：`skill-name/SKILL.md`。`SKILL.md` 必须有 frontmatter，且 `name` 要和父目录名一致。
