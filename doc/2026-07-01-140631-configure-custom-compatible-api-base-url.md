# Configure Custom Compatible API Base URL

- Time: 2026-07-01T14:06:31+08:00
- Project: deepagents

## Prompt

要使用这个cli跑大模型,如何配置api, 我是自定义兼容的api和baseurl

## AI Response

如果你的接口是 **OpenAI 兼容 API**，最简单用 `openai` provider 配：

```bash
cd libs/code
export OPENAI_API_KEY="你的key"
export OPENAI_BASE_URL="https://你的baseurl/v1"
uv run dcode --model openai:你的模型名
```

例如：

```bash
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.example.com/v1"
uv run dcode --model openai:qwen2.5-coder-32b-instruct
```

也可以用 DeepAgents Code 专属环境变量，优先级更高：

```bash
export DEEPAGENTS_CODE_OPENAI_API_KEY="你的key"
export DEEPAGENTS_CODE_OPENAI_BASE_URL="https://你的baseurl/v1"
uv run dcode --model openai:你的模型名
```

进入交互式后也可以用：

```txt
/auth
/model
```

`/auth` 管理 key 和 endpoint，`/model` 选择模型。

如果你不想每次 export，可以写到 shell 配置或项目 `.env`：

```env
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=https://你的baseurl/v1
```

注意：模型名要用你的服务端实际支持的名字；base URL 通常需要带 `/v1`，但以你的兼容 API 文档为准。
