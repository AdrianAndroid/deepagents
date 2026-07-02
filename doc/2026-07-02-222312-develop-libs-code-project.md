# Develop Libs Code Project

- Time: 2026-07-02T22:23:12+08:00
- Project: deepagents

## Prompt

想二开lib/code下的项目

hello

hello

hello

hello

## AI Response

你要二开的是 `libs/code` 下的 `deepagents-code` / `dcode`。推荐流程：

```bash
cd /Users/zhaojian/code/deepagents/libs/code
uv sync --group test
./dcode-dev.sh
```

改源码后重启 `dcode-dev` 即可生效；重点看 `main.py`、`app.py`、`agent.py`、`model_config.py`、`skills/`、`widgets/`。验证用：`make lint && make test`。