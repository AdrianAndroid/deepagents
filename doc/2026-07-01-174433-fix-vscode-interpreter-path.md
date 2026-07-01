# Fix VS Code Interpreter Path

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T17:44:33+08:00
- Project: deepagents

## Prompt

怎样修改?<environment_details>
Current time: 2026-07-01T17:44:33+08:00
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

已修改 `.vscode/settings.json`：

```json
"python.defaultInterpreterPath": "./libs/code/.venv/bin/python"
```

并确认解释器存在：

```text
/Users/zhaojian/Desktop/deepagents/libs/code/.venv/bin/python
```

修改后需要在 VS Code 执行：

```text
Python: Restart Language Server
```

或重载窗口：

```text
Developer: Reload Window
```
