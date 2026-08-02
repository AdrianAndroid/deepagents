# Explain Dcode Command

- Time: 2026-07-01T13:58:02+08:00
- Project: deepagents

## Prompt

dcode是什么

## AI Response

`dcode` 是这个项目里 `deepagents-code` 包提供的命令行入口。

它是一个基于 Deep Agents 的终端编程助手，类似 Claude Code / Codex CLI，可以在终端里和 AI 对话，让 AI 读取代码、修改文件、执行命令、运行测试。

在 `libs/code/pyproject.toml` 中定义了两个等价命令：

```toml
deepagents-code = "deepagents_code:cli_main"
dcode = "deepagents_code:cli_main"
```

所以：

```bash
uv run dcode
```

等价于：

```bash
uv run deepagents-code
```
