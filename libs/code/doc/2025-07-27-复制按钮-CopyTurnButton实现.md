# deepagents-code 复制按钮功能

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

### 轮次 1 - 添加复制按钮到 AssistantMessage

#### 用户提问要点
在每次问答结束时，在左下角添加一个复制按钮，点击按钮复制那次的问答（用户提问 + 助手回答）。

#### 结论/方案
在 `AssistantMessage` widget 中添加了一个 `CopyTurnButton` 子组件：
- 流式传输期间隐藏，`stop_stream()` 完成后显示
- 点击时向上遍历 `#messages` 容器找到最近的 `UserMessage`
- 将用户提问和助手回答拼接后复制到剪贴板
- 支持虚拟化：重新水合时 `_stream_finalized` 标志从构造函数内容推断

#### 关键操作或文件改动
1. `deepagents_code/widgets/messages.py`:
   - 新增 `CopyTurnButton(Static)` 类，含 CSS 样式和点击处理
   - `AssistantMessage.__init__` 新增 `_stream_finalized: bool` 标志
   - `AssistantMessage.compose` 新增 `yield CopyTurnButton`
   - `AssistantMessage.on_mount` 调用 `_show_copy_button()`
   - `AssistantMessage._show_copy_button()` 用 `contextlib.suppress` 安全显示按钮
   - `stop_stream()`, `set_content()`, `write_initial_content()` 均调用 `_show_copy_button()`
   - 新增 `import contextlib` 和 `from textual.css.query import NoMatches, WrongType`
2. `tests/unit_tests/test_messages.py`:
   - 新增 `TestCopyTurnButton` 测试类，4 个测试用例

#### 后续 TODO
- 可考虑在 headless 模式下禁用此按钮
- 可考虑添加键盘快捷键支持
