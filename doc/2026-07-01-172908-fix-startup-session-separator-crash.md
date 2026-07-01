# Fix Startup Session Separator Crash

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T17:29:08+08:00
- Project: deepagents

## Prompt

╭─────────────────────────────────────────────────────── Traceback (most recent call last) ───────────────────────────────────────────────────────╮
│ /Users/zhaojian/Desktop/deepagents/libs/code/deepagents_code/app.py:5966 in _run_session_start_sequence                                         │
│                                                                                                                                                 │
│    5963 │   │   │   │   │   return                                                                                                              │
│    5964 │   │   │                                                                                                                               │
│    5965 │   │   │   # Add session separator for new sessions with no history                                                                    │
│ ❱  5966 │   │   │   if self._message_store.is_empty():                                                                                          │
│    5967 │   │   │   │   await self._mount_message(SessionSeparator())                                                                           │
│    5968 │   │   │                                                                                                                               │
│    5969 │   │   │   if self._startup_cmd:                                                                                                       │
╰───────────────────────────────────────────────────────────────────


新增的代码有崩溃<environment_details>
Current time: 2026-07-01T17:29:08+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/deepagents_code/app.py
Visible files:
  libs/code/deepagents_code/app.py
</environment_details>

## AI Response

Fixed the startup crash by replacing the nonexistent `MessageStore.is_empty()` call with `total_count == 0` and added a regression test for mounting `SessionSeparator` on empty sessions.

Validation:
- `uv run --group test pytest tests/unit_tests/test_app.py::TestStartupSequence::test_new_session_mounts_separator`
- `uv run --all-groups ruff check deepagents_code/app.py tests/unit_tests/test_app.py`
- `uv run --all-groups ty check deepagents_code/app.py tests/unit_tests/test_app.py`

Note: full `make lint` / `make typecheck` still fail on pre-existing unrelated issues in `media_utils.py`, `chat_input.py`, and `widgets/messages.py`.
