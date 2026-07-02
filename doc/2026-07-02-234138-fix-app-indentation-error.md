# Fix App Indentation Error

- Time: 2026-07-02T23:41:38+08:00
- Project: deepagents

## Prompt

用户运行 `uv run dcode` 报错：

```text
Application error: expected an indented block after 'if' statement on line 9662 (app.py, line 9663)
IndentationError: expected an indented block after 'if' statement on line 9662
```

## AI Response

已修复 `libs/code/deepagents_code/app.py` 中 `_mount_error` 的错误缩进，去掉了空的 `if command is not None:` 分支。

验证命令已通过：

```bash
uv --directory libs/code run python -m py_compile deepagents_code/app.py
```

现在可以重新运行：

```bash
uv --directory libs/code run dcode
```