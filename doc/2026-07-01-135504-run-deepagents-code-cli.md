# Run Deepagents Code CLI

- Time: 2026-07-01T13:55:04+08:00
- Project: deepagents

## Prompt

这个项目,我应该如何将cli跑起来?

## AI Response

这个仓库里类似 Codex 的终端 CLI 是 `libs/code` 包，入口命令是 `deepagents-code` 或 `dcode`。

推荐在项目根目录执行：

```bash
cd libs/code
uv sync --group test
uv run dcode --help
uv run dcode
```

如果只想非交互执行一次任务：

```bash
cd libs/code
uv run dcode -x "总结这个项目的结构"
```

如果要跑部署管理 CLI，则是另一个包：

```bash
cd libs/cli
uv sync --group test
uv run deepagents --help
```

运行前需要配置模型 API Key，例如 OpenAI/Anthropic/Google 对应环境变量；也可以启动后通过 CLI 的认证/模型配置流程设置。
