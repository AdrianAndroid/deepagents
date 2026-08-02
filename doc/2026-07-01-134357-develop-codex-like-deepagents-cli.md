# Develop Codex Like Deepagents CLI

- Time: 2026-07-01T13:43:57+08:00
- Project: deepagents

## Prompt

我想开发一个类似codex的cli开发辅助工具, 基座使用deepagents,我该如何开发,帮忙分析一个执行计划, 使用AI协助开发项目

## AI Response

建议不要从零开始，直接基于 `libs/code/deepagents_code` 做产品化改造；它已经包含 CLI/TUI、coding agent、命令注册、模型配置、MCP、skills、会话等能力。

执行计划：
1. 调研现有实现：重点看 `libs/code/deepagents_code/main.py`、`app.py`、`agent.py`、`command_registry.py`、`config.py`、`system_prompt.md`。
2. 定义 MVP：实现 `mycode "修复这个 bug"`，支持读取项目、修改文件、执行命令、展示结果。
3. 封装 Agent：用 `deepagents.create_deep_agent()` 组装模型、系统提示词、文件工具、shell 工具、todo、subagent、权限中间件。
4. 加项目上下文：自动读取 `AGENTS.md`、`README.md`、`pyproject.toml`、`package.json` 等，注入开发规范。
5. 加安全策略：限制工作区外写入；危险 shell 命令、`git push`、`rm -rf`、密钥相关操作必须确认。
6. 加交互体验：实现 `/help`、`/model`、`/diff`、`/resume`、`/clear`、`/exit`，再考虑 Textual TUI。
7. 加验证闭环：根据项目类型自动发现并运行 lint、typecheck、test；失败后让 agent 继续修复。
8. 加会话与配置：保存历史、模型配置、权限配置、项目规则、技能目录。

AI 协助开发方式：
- Agent A：分析 `libs/code` 架构，输出可复用模块清单。
- Agent B：实现最小 CLI 包和入口命令。
- Agent C：实现权限系统和危险命令确认。
- Agent D：实现 slash commands 和会话管理。
- Agent E：补单元测试、跑 lint/typecheck/test。

推荐里程碑：
- M1：非交互 CLI 可读写文件并运行命令。
- M2：交互式 CLI + slash commands。
- M3：权限、安全、会话恢复。
- M4：MCP、skills、subagents、代码审查、PR 辅助。
