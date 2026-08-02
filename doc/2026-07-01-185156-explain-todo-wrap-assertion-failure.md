# Explain Todo Wrap Assertion Failure

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T18:51:56+08:00
- Project: deepagents

## Prompt

FAILED tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_shows_full_wrapped_content - AssertionError: assert '\n             ' in '    1 active\n\n    ● active Implement the new authentication flow using OAuth2 with PKCE for ...
FAILED tests/unit_tests/test_messages.py::TestToolCallMessageTodos::test_todo_expanded_continuation_aligns_content_column - AssertionError: assert 3 > (2 + 1)

为什么会报这个错误<environment_details>
Current time: 2026-07-01T18:51:56+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
</environment_details>

## AI Response

这两个失败都说明同一件事：展开状态的 todo 长文本没有换行。

测试期望：

```text
    ● active 第一行内容
             第二行续行内容
```

也就是续行前面必须有 13 个空格：`\n             `，让续行对齐到 todo 内容列。

实际输出：

```text
    1 active

    ● active Implement the new authentication flow using OAuth2 with PKCE for ...
```

没有第二行，所以：
- 第一个断言找不到 `\n             `。
- 第二个断言发现总行数不够，`len(lines)` 没有大于 `todo_start + 1`。

根因是 `_format_todo_line()` 只有在 `textwrap.wrap(...)` 判断文本超过可用宽度时才会插入续行。当前测试运行环境里计算出的 todo 内容宽度太宽，长文本被认为一行能放下，因此不换行。

当前修复方向：
- 降低未挂载 widget 时的 fallback 宽度 `_DEFAULT_TODO_WRAP_WIDTH`。
- 或让 `_todo_content_width()` 在单元测试/未挂载情况下稳定返回较小宽度。

当前工作区已经把 `_DEFAULT_TODO_WRAP_WIDTH` 从 `80` 改成 `60`，我本地重新跑这两个测试是通过的。如果你那里仍失败，通常是因为测试跑的不是当前这份代码，或者运行目录/环境不对。
