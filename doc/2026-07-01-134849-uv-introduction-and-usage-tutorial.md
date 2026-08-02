# UV Introduction And Usage Tutorial

- Time: 2026-07-01T13:48:49+08:00
- Project: deepagents

## Prompt

uv工具我已经看见很多次了,但还不知道怎么用,帮我生成一个uv的详细介绍及使用教程

## AI Response

# uv 详细介绍及使用教程

## 1. uv 是什么

`uv` 是一个 Python 项目管理工具，由 Astral 开发。它可以替代很多传统工具：

- `pip`
- `pip-tools`
- `virtualenv`
- `venv`
- `poetry` 的一部分能力
- `pipx` 的一部分能力
- `pyenv` 的一部分能力

它的核心目标是：

- 更快地安装依赖
- 自动管理虚拟环境
- 自动管理 Python 版本
- 使用 `pyproject.toml` 管理项目
- 使用 `uv.lock` 锁定依赖版本
- 让 Python 项目开发流程更稳定、更可复现

在这个 `deepagents` 项目里，官方推荐使用 `uv`，不要直接用 `pip`、`poetry` 或 `conda`。

---

## 2. uv 解决了什么问题

传统 Python 项目经常需要手动处理：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m pytest
```

使用 `uv` 后，很多步骤可以简化成：

```bash
uv sync
uv run pytest
```

`uv` 会自动：

- 创建 `.venv`
- 安装依赖
- 读取 `pyproject.toml`
- 使用 `uv.lock` 中的锁定版本
- 在正确的虚拟环境中运行命令

通常不需要手动执行：

```bash
source .venv/bin/activate
```

---

## 3. 常见命令总览

| 命令 | 作用 |
|---|---|
| `uv --version` | 查看 uv 版本 |
| `uv python list` | 查看可用 Python 版本 |
| `uv python install 3.12` | 安装 Python 3.12 |
| `uv init` | 初始化新 Python 项目 |
| `uv add package` | 添加运行依赖 |
| `uv add --dev package` | 添加开发依赖 |
| `uv remove package` | 移除依赖 |
| `uv sync` | 根据项目配置同步环境 |
| `uv lock` | 更新锁文件 |
| `uv lock --check` | 检查锁文件是否最新 |
| `uv run command` | 在项目环境中运行命令 |
| `uv tool run command` | 临时运行工具 |
| `uvx command` | `uv tool run` 的简写 |
| `uv pip install package` | pip 兼容安装方式 |

---

## 4. 安装 uv

macOS/Linux 推荐：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

也可以用 Homebrew：

```bash
brew install uv
```

检查安装：

```bash
uv --version
```

当前项目环境里已经安装：

```txt
uv 0.11.19
```

---

## 5. uv 的核心概念

### 5.1 `pyproject.toml`

现代 Python 项目的主配置文件。

里面通常包含：

- 项目名
- 版本号
- Python 版本要求
- 运行依赖
- 开发依赖
- 构建配置
- lint/test/typecheck 配置

例如：

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
]
```

---

### 5.2 `uv.lock`

`uv.lock` 是锁文件。

它记录所有依赖的精确版本，作用类似：

- JavaScript 的 `package-lock.json`
- Rust 的 `Cargo.lock`
- Poetry 的 `poetry.lock`

有了 `uv.lock`，团队成员和 CI 可以安装完全一致的依赖版本。

通常：

- 应该提交 `uv.lock`
- 不要手动编辑 `uv.lock`
- 通过 `uv lock` 或 `uv sync` 更新它

---

### 5.3 `.venv`

`uv` 默认会在项目目录下创建 `.venv`。

你通常不需要手动激活它。

推荐：

```bash
uv run python
uv run pytest
uv run ruff check .
```

而不是：

```bash
source .venv/bin/activate
python
pytest
```

---

### 5.4 dependency groups

很多项目会把依赖分组。

例如这个项目里常见：

```toml
[dependency-groups]
test = [
    "pytest",
    "ruff",
    "ty",
]
```

安装测试依赖：

```bash
uv sync --group test
```

运行测试命令：

```bash
uv run --group test pytest
```

---

## 6. 新建一个 Python 项目

```bash
mkdir my-agent
cd my-agent
uv init
```

生成结构大致是：

```txt
my-agent/
├── pyproject.toml
├── README.md
└── main.py
```

运行：

```bash
uv run python main.py
```

---

## 7. 添加依赖

添加运行依赖：

```bash
uv add requests
```

添加指定版本范围：

```bash
uv add "langchain>=1.0,<2.0"
```

添加开发依赖：

```bash
uv add --dev pytest
uv add --dev ruff
```

如果项目使用 dependency group，也可以：

```bash
uv add --group test pytest
uv add --group test ruff
```

添加后，`uv` 会更新：

- `pyproject.toml`
- `uv.lock`
- `.venv`

---

## 8. 移除依赖

```bash
uv remove requests
```

移除开发组依赖：

```bash
uv remove --group test pytest
```

---

## 9. 同步依赖环境

进入一个已有项目后，通常第一步是：

```bash
uv sync
```

如果需要测试依赖：

```bash
uv sync --group test
```

如果需要所有依赖组：

```bash
uv sync --all-groups
```

在这个 `deepagents` 仓库中，推荐进入具体包目录运行，例如：

```bash
cd libs/code
uv sync --group test
```

---

## 10. 运行命令

使用 `uv run` 在项目环境中执行命令：

```bash
uv run python --version
uv run pytest
uv run ruff check .
uv run ty check .
```

运行项目脚本：

```bash
uv run deepagents-code --help
```

如果当前包定义了 console script，`uv run` 会自动找到它。

---

## 11. Python 版本管理

查看可用版本：

```bash
uv python list
```

安装 Python 3.12：

```bash
uv python install 3.12
```

用指定 Python 版本创建/同步环境：

```bash
uv sync --python 3.12
```

运行指定 Python：

```bash
uv run --python 3.12 python --version
```

在这个项目中：

- 大多数包支持 `>=3.11,<4.0`
- 仓库批量 lock 默认很多包使用 `3.12`
- `libs/acp` 在 Makefile 中按 `3.14` 处理

---

## 12. 运行一次性工具

`uvx` 可以临时运行 Python 工具，类似 `pipx run`。

例如：

```bash
uvx ruff check .
uvx pyright
uvx pre-commit run --all-files
```

完整写法是：

```bash
uv tool run ruff check .
```

`uvx` 是简写。

---

## 13. pip 兼容模式

`uv` 也提供接近 `pip` 的命令：

```bash
uv pip install requests
uv pip freeze
uv pip list
```

但在现代项目中，优先使用：

```bash
uv add
uv sync
uv run
```

而不是长期依赖 `uv pip install`。

---

## 14. 在 deepagents 项目里的典型用法

### 14.1 开发核心 SDK

```bash
cd libs/deepagents
uv sync --group test
uv run --group test pytest
make lint
make test
```

### 14.2 开发 CLI coding agent

```bash
cd libs/code
uv sync --group test
uv run deepagents-code --help
make lint
make test
```

### 14.3 检查锁文件

```bash
make -C libs lock-check
```

### 14.4 更新某个包锁文件

例如在 `libs/code`：

```bash
cd libs/code
uv lock
```

### 14.5 同步所有测试依赖

进入具体包目录：

```bash
uv sync --group test
```

不建议在仓库根目录直接乱跑，因为这是 monorepo，多个包各自有自己的 `pyproject.toml` 和 `uv.lock`。

---

## 15. `uv sync` 和 `uv lock` 的区别

### `uv lock`

只解决依赖版本并更新 `uv.lock`。

```bash
uv lock
```

适合：

- 更新锁文件
- CI 检查锁文件
- 依赖版本调整后重新解析

### `uv sync`

根据 `pyproject.toml` 和 `uv.lock` 同步本地虚拟环境。

```bash
uv sync
```

适合：

- 第一次进入项目
- 拉取别人更新后的依赖
- 创建或刷新 `.venv`

简单理解：

```txt
uv lock  = 更新依赖清单
uv sync  = 安装依赖到环境
```

---

## 16. `uv run` 为什么重要

不要直接运行：

```bash
pytest
ruff check .
python script.py
```

推荐运行：

```bash
uv run pytest
uv run ruff check .
uv run python script.py
```

原因：

- 确保使用当前项目的 `.venv`
- 确保依赖版本一致
- 避免误用系统 Python
- 避免误用全局安装的工具

---

## 17. 常见开发流程

### 第一次克隆项目

```bash
git clone <repo>
cd <repo>/<package-dir>
uv sync --group test
uv run pytest
```

### 添加依赖

```bash
uv add httpx
uv run python -c "import httpx; print(httpx.__version__)"
```

### 添加测试依赖

```bash
uv add --group test pytest-mock
uv run --group test pytest
```

### 更新锁文件

```bash
uv lock
```

### 检查锁文件是否过期

```bash
uv lock --check
```

### 运行 lint

```bash
uv run ruff check .
uv run ruff format . --diff
```

### 自动格式化

```bash
uv run ruff format .
uv run ruff check --fix .
```

---

## 18. 和 pip/venv 的对比

传统方式：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

uv 方式：

```bash
uv sync --group test
uv run pytest
```

传统方式的问题：

- 容易忘记激活虚拟环境
- 依赖解析慢
- 版本不容易稳定
- 多 Python 版本管理麻烦

uv 的优势：

- 快
- 自动管理 `.venv`
- 自动使用锁文件
- 对 monorepo 更友好
- 命令更统一

---

## 19. 常见问题

### Q1：还需要手动激活 `.venv` 吗？

通常不需要。

推荐：

```bash
uv run python
```

如果你确实想激活，也可以：

```bash
source .venv/bin/activate
```

但在项目自动化、CI、AI agent 执行命令时，推荐始终使用 `uv run`。

---

### Q2：为什么 `uv sync` 后多了 `.venv`？

这是项目虚拟环境，正常现象。

一般 `.venv` 不提交到 Git。

---

### Q3：为什么有 `uv.lock`？

为了锁定依赖版本，保证别人、CI、你自己下次安装时得到一致环境。

---

### Q4：什么时候用 `uv add`，什么时候直接改 `pyproject.toml`？

优先用：

```bash
uv add package
```

它会自动更新 `pyproject.toml` 和 `uv.lock`。

只有复杂配置时才手动编辑 `pyproject.toml`。

---

### Q5：什么时候用 `uv pip install`？

临时调试可以用。

正式项目依赖建议用：

```bash
uv add package
```

---

## 20. 针对你开发 CLI 工具的推荐用法

如果你要新建一个类似 Codex 的 CLI 项目，可以这样开始：

```bash
mkdir mycode
cd mycode
uv init --package
uv add deepagents
uv add typer rich prompt-toolkit
uv add --group test pytest ruff ty
uv sync --group test
```

运行：

```bash
uv run mycode --help
```

如果要本地依赖当前仓库里的 `deepagents` SDK，可以在 `pyproject.toml` 中配置：

```toml
[tool.uv.sources]
deepagents = { path = "../deepagents/libs/deepagents", editable = true }
```

然后：

```bash
uv sync --group test
```

---

## 21. 最推荐记住的 8 个命令

```bash
uv --version
uv init
uv add <package>
uv remove <package>
uv sync
uv sync --group test
uv run <command>
uv lock --check
```

如果只记住一句话：

```txt
用 uv sync 安装环境，用 uv run 执行命令，用 uv add 管理依赖。
```
