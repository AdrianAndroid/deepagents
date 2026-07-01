# UV Vs Conda Differences

- Time: 2026-07-01T13:53:45+08:00
- Project: deepagents

## Prompt

uv和conda的区别

## AI Response

`uv` 和 `conda` 的定位不同：

| 对比项 | uv | conda |
|---|---|---|
| 核心定位 | Python 包管理、虚拟环境、锁文件、运行工具 | 跨语言环境管理和科学计算发行生态 |
| 主要管理对象 | Python 项目依赖 | Python、R、C/C++库、CUDA、系统级二进制依赖 |
| 依赖来源 | PyPI | conda channel，如 defaults、conda-forge |
| 配置文件 | `pyproject.toml`、`uv.lock` | `environment.yml`、conda env |
| 虚拟环境 | 通常项目内 `.venv` | 全局/指定路径 conda env |
| 速度 | 很快 | 通常较慢 |
| 适合场景 | Python 应用、CLI、Web、Agent、库开发 | 数据科学、机器学习、GPU、复杂原生依赖 |
| 本项目推荐 | 推荐使用 | 不推荐直接用于本仓库开发 |

简单理解：

- `uv` 更像现代 Python 项目的 `npm`/`cargo`。
- `conda` 更像跨语言的环境发行版和二进制依赖管理器。

在 `deepagents` 这类 Python monorepo 中，推荐用 `uv`：

```bash
uv sync --group test
uv run pytest
uv add <package>
```

如果你做 CUDA、PyTorch、Jupyter、科学计算，且依赖复杂二进制库，`conda` 仍然有优势。
