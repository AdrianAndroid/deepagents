# Explain VS Code Deepagents Diagnostic

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T17:43:02+08:00
- Project: deepagents

## Prompt

在vscode打开deepangents项目, 为什么会有这个错误?

import tomllib
create_deep_agent
Module `deepagents` has no member `create_deep_agent`tyClick for full diagnostic
Unknown<environment_details>
Current time: 2026-07-01T17:43:02+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/deepagents_code/agent.py
Visible files:
  libs/code/deepagents_code/agent.py
Open tabs:
  doc/2026-07-01-173618-implement-per-qa-separator.md
  libs/code/deepagents_code/agent.py
</environment_details>

## AI Response

原因是 VS Code 选错/找不到 Python 环境：`.vscode/settings.json` 配的是 `./.venv/bin/python`，但根目录没有这个解释器；ty/Pylance 没用 `libs/code` 的 uv 环境和 `[tool.ty.environment].extra-paths`，所以把 `deepagents` 解析成已安装包或错误路径。

本地源码里 `create_deep_agent` 确实存在：`libs/deepagents/deepagents/__init__.py` 从 `deepagents.graph` 导出它。

建议在 `libs/code` 下同步环境并让 VS Code 选这个解释器：

```bash
uv sync --all-groups
```

然后在 VS Code 里选择：

```text
/Users/zhaojian/Desktop/deepagents/libs/code/.venv/bin/python
```

也可以把工作区打开到 `libs/code`，或把 VS Code 的解释器设置改成 `./libs/code/.venv/bin/python`。
