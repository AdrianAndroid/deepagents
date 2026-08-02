# Explain Three Unit Test Failures

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T18:34:25+08:00
- Project: deepagents

## Prompt

FAILED tests/unit_tests/test_charset.py::TestGetBanner::test_ascii_banner_is_pure_ascii - AssertionError: Non-ASCII character found: '▀'
FAILED tests/unit_tests/test_media_utils.py::TestGetClipboardImage::test_unsupported_platform_returns_none_and_warns - AssertionError: Expected 'warning' to have been called once. Called 0 times.
FAILED tests/unit_tests/test_app.py::TestLangsmithGatewayKeyMismatch::test_detects_non_langsmith_key_on_gateway - AssertionError: assert 'DEEPAGENTS_C...PENAI_API_KEY' == 'OPENAI_API_KEY'

这是啥错误<environment_details>
Current time: 2026-07-01T18:34:25+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: .vscode/settings.json
Visible files:
  .vscode/settings.json
Open tabs:
  doc/2026-07-01-173618-implement-per-qa-separator.md
  libs/code/deepagents_code/agent.py
  libs/deepagents/deepagents/graph.py
</environment_details>

## AI Response

这是 3 个单元测试断言失败，不是 VS Code/ty 本身错误：

1. `test_ascii_banner_is_pure_ascii`
   - ASCII 模式的 banner 里出现了非 ASCII 字符 `▀`。
   - 说明 ASCII 降级逻辑没生效，或 banner 文案/字形用了 Unicode。

2. `test_unsupported_platform_returns_none_and_warns`
   - 测试期望不支持的平台会调用一次 `logger.warning(...)`。
   - 实际没有 warning，说明实现改成静默返回 `None`，或日志级别/分支没走到。

3. `test_detects_non_langsmith_key_on_gateway`
   - 测试期望检测到的 key 名是 `OPENAI_API_KEY`。
   - 实际返回了 `DEEPAGENTS_C...PENAI_API_KEY`，说明环境变量优先级或网关 key mismatch 检测逻辑变了。

结论：这是代码行为和测试预期不一致。需要分别检查 charset/banner、clipboard 平台分支、LangSmith gateway key 检测逻辑。
