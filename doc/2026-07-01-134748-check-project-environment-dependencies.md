# Check Project Environment Dependencies

- Time: 2026-07-01T13:47:48+08:00
- Project: deepagents

## Prompt

帮我检查一下这个项目需要的环境依赖

## AI Response

已检查。这个仓库是 Python monorepo，核心环境依赖如下：

- 包管理/运行：`uv`，已安装 `uv 0.11.19`
- Python：项目要求 `>=3.11`；仓库批量任务默认多数包用 `3.12`，`libs/acp` 用 `3.14`；当前系统 `Python 3.13.13`
- 构建工具：`make`，已安装 GNU Make 3.81
- Git：已安装 `git 2.50.1`
- Node/npm：仅部分前端/桥接组件需要；当前 `node v24.15.0`、`npm 11.12.1`

重点包：
- `libs/deepagents`：SDK，依赖 LangChain/LangGraph/LangSmith，Python `>=3.11,<4.0`
- `libs/code`：终端 coding agent，依赖 Textual、Rich、LangGraph CLI/runtime、MCP、QuickJS、各模型 provider，Python `>=3.11,<4.0`
- `libs/cli`：部署 CLI，Python `>=3.11,<4.0`
- `libs/acp`：ACP 适配，声明 `>=3.11`，但仓库 Makefile 注释说明本地批量 lock 使用 Python `3.14`

开发命令：
- 安装某包依赖：`uv sync --group test`，在对应包目录运行，例如 `libs/code`
- 测试 coding agent：`make -C libs/code test`
- lint/typecheck：`make -C libs/code lint`
- 全仓库 lint：`make -C libs lint`
- 锁文件检查：`make -C libs lock-check`

当前环境基本满足开发要求；如果要完全复现仓库批量 CI，建议额外确保 `uv` 能自动下载/使用 Python 3.12 和 3.14。
