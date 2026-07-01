# Explain Ty Type Checker

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T17:49:00+08:00
- Project: deepagents

## Prompt

刚才提到的ty是什么东西, 有什么作用?<environment_details>
Current time: 2026-07-01T17:49:00+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: doc/2026-07-01-174518-fix-ty-deepagents-export-diagnostic.md
Visible files:
  doc/2026-07-01-174518-fix-ty-deepagents-export-diagnostic.md
Open tabs:
  doc/2026-07-01-173618-implement-per-qa-separator.md
  libs/code/deepagents_code/agent.py
  libs/deepagents/deepagents/graph.py
  doc/2026-07-01-174518-fix-ty-deepagents-export-diagnostic.md
</environment_details>

## AI Response

`ty` 是 Astral 开发的 Python 静态类型检查器和语言服务器，类似 Pyright / mypy。

作用：
- 在不运行代码的情况下检查类型错误、导入错误、属性不存在等问题。
- 给 VS Code 提供诊断、跳转定义、补全、悬停信息等语言服务。
- 本项目用它做类型检查，配置在各 package 的 `pyproject.toml` 里，例如 `libs/code/pyproject.toml` 的 `[tool.ty.environment]`。

你看到的 `Module deepagents has no member create_deep_agent` 就是 ty 在 VS Code 里解析 Python 环境/源码路径时给出的静态诊断，不是运行时错误。
