# Implement Per-QA Separator

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T17:36:18+08:00
- Project: deepagents

## Prompt

修改代码,每次问答都有分隔符<environment_details>
Current time: 2026-07-01T17:36:18+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Open tabs:
  doc/2026-07-01-173205-summary-of-startup-separator-changes.md
</environment_details>

## AI Response

已修改代码：每次用户消息进入问答流程前都会先挂载 `SessionSeparator`，因此每轮问答都有分隔符。

变更：
- `libs/code/deepagents_code/app.py`：把分隔符挂载逻辑从会话启动阶段移到 `_handle_user_message()`，确保每次普通用户提问都会显示分隔符。
- `libs/code/deepagents_code/widgets/messages.py`：补全 `SessionSeparator.__init__` 的类型标注、docstring 和格式，解决该组件自身 lint 问题。
- `libs/code/tests/unit_tests/test_app.py`：新增/调整测试 `test_user_message_mounts_separator_before_prompt`，断言挂载顺序为 `SessionSeparator` → `UserMessage`。

验证通过：
- `uv run --group test pytest tests/unit_tests/test_app.py::TestStartupSequence::test_user_message_mounts_separator_before_prompt`
- `uv run --all-groups ruff check deepagents_code/app.py deepagents_code/widgets/messages.py tests/unit_tests/test_app.py`
- `uv run --all-groups ty check deepagents_code/app.py deepagents_code/widgets/messages.py tests/unit_tests/test_app.py`
