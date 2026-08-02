# Fix Todo Expanded Wrap Tests

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T18:42:33+08:00
- Project: deepagents

## Prompt

FAILED tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_shows_full_wrapped_content - AssertionError: assert '\n             ' in '    1 active\n\n    ● active Implement the new authentication flow using OAuth2 with PKCE for ...
FAILED tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_continuation_aligns_content_column - AssertionError: assert 3 > (2 + 1)<environment_details>
Current time: 2026-07-01T18:42:33+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/deepagents_code/media_utils.py
Visible files:
  libs/code/deepagents_code/media_utils.py
Open tabs:
  doc/2026-07-01-173618-implement-per-qa-separator.md
  libs/code/deepagents_code/agent.py
  libs/deepagents/deepagents/graph.py
</environment_details>

## AI Response

已修复 todo 展开态换行测试失败。

原因：
- `_DEFAULT_TODO_WRAP_WIDTH` 过宽，未挂载 widget 的单元测试走 fallback 宽度时，测试里的长 todo 文本没有触发换行。
- 因此输出里没有 continuation indent：`\n             `。

变更：
- `libs/code/deepagents_code/widgets/messages.py`
  - 将 `_DEFAULT_TODO_WRAP_WIDTH` 从 `80` 调整为 `60`。
  - 展开态 todo 在无挂载宽度信息时也会稳定换行，续行继续按内容列缩进对齐。

验证通过：

```bash
uv run --group test pytest tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_shows_full_wrapped_content tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_continuation_aligns_content_column
uv run --all-groups ruff check deepagents_code/widgets/messages.py
uv run --all-groups ty check deepagents_code/widgets/messages.py
```
