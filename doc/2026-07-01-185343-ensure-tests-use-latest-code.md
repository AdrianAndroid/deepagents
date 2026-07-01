# Ensure Tests Use Latest Code

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T18:53:43+08:00
- Project: deepagents

## Prompt

如何确保是新代码?<environment_details>
Current time: 2026-07-01T18:53:43+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
</environment_details>

## AI Response

在项目根目录执行：

```bash
git diff -- libs/code/deepagents_code/widgets/messages.py libs/code/deepagents_code/config.py
```

确认能看到：

```python
_DEFAULT_TODO_WRAP_WIDTH = 60
_ASCII_BANNER = rf"""
zhaojian shuai v{__version__}
"""
```

然后必须从 `libs/code` 目录运行测试：

```bash
cd libs/code
uv run --group test pytest tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_shows_full_wrapped_content tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_continuation_aligns_content_column -q
```

如果仍失败，清缓存后再跑：

```bash
rm -rf .pytest_cache deepagents_code/**/__pycache__ tests/**/__pycache__
uv run --group test pytest tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_shows_full_wrapped_content tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_continuation_aligns_content_column -q
```
