# Fix Ty Deepagents Export Diagnostic

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T17:45:18+08:00
- Project: deepagents

## Prompt

Module `deepagents` has no member `create_deep_agent`tyClick for full diagnostic<environment_details>
Current time: 2026-07-01T17:45:18+08:00
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

已继续修复 VS Code ty 配置。

问题原因：
- 从仓库根目录运行 `uv run --all-groups ty ...` 失败，因为根目录不是 uv project，没有 `ty`。
- 从 `libs/code` 运行 `uv run --all-groups ty check deepagents_code/agent.py` 通过，说明代码和依赖本身没问题。
- VS Code 的 ty language server 从仓库根目录启动时，没有读取 `libs/code/pyproject.toml` 里的 `[tool.ty.environment].extra-paths`，所以解析 `deepagents` 错误。

已修改 `.vscode/settings.json`：
- 保留 Python 解释器：`./libs/code/.venv/bin/python`
- 新增 `ty.interpreter`
- 新增 `ty.configuration.environment`，显式指定：
  - `python`: `./libs/code/.venv`
  - `root`: `./libs/code`、`./libs/deepagents` 和 partner 包路径
  - `extra-paths`: `./libs/deepagents` 和 partner 包路径
  - `python-version`: `3.11`

验证：

```bash
uv run --all-groups python -c "import deepagents; print(deepagents.__file__); print(hasattr(deepagents, 'create_deep_agent'))"
```

输出确认：

```text
/Users/zhaojian/Desktop/deepagents/libs/deepagents/deepagents/__init__.py
True
```

需要在 VS Code 执行：

```text
Developer: Reload Window
```

或：

```text
Ty: Restart Server
```

如果仍残留旧诊断，关闭并重新打开 `libs/code/deepagents_code/agent.py`。
