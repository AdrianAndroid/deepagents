# Agent APIConnectionError Internal Error

- Time: 2026-07-02T17:26:56+08:00
- Project: deepagents

## Prompt

这个项目报这个错误:Agent error: APIConnectionError: An internal error occurred<environment_details>
Current time: 2026-07-02T17:26:56+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Open tabs:
  资料文档/通过1panel创建pypiserver详细步骤.md
  资料文档/1Panel 搭建私有 PyPI 仓库最终落地文档（解决403_405报错、永久可用）.md
</environment_details>

## AI Response

`Agent error` 是 `libs/code/deepagents_code/app.py:8195` 包装出来的显示文本；真正错误是 `APIConnectionError: An internal error occurred`，通常表示模型服务/API 网关连不上或服务端 5xx。

优先检查：API Key 是否正确、`OPENAI_BASE_URL`/`ANTHROPIC_BASE_URL`/对应 provider 的 base_url 是否配错、代理/VPN/内网网关是否可达、模型服务是否返回 500。

如果你用的是 `deepagents-code/dcode`，建议开启调试日志复现：`DEEPAGENTS_CODE_DEBUG=1 DEEPAGENTS_CODE_DEBUG_FILE=/tmp/dcode.log dcode`，再看 `/tmp/dcode.log` 里的完整请求异常。

相关位置：`libs/code/deepagents_code/app.py:8190` 捕获并展示错误，`libs/code/deepagents_code/remote_client.py:75` 格式化远端异常。
