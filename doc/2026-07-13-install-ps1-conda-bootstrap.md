# 2026-07-13 · libs/code 环境分析 & Windows install.ps1 完善（Miniconda 自举）

## 轮次 1 - libs/code 运行环境 & Windows 安装脚本增强

### 用户提问要点
- 分析 `libs/code` 需要的运行环境。
- 完善 `web/install.ps1`：当 Windows 上没有 `conda` 时，自动安装 Miniconda 并用它提供 Python。

### `libs/code` (deepagents-code) 环境要求
来源：`libs/code/pyproject.toml`。

- **Python `>=3.11,<4.0`**（硬性约束，也就是 3.11 / 3.12 / 3.13 / 3.14 都可，3.10 及以下不行）。
- 安装方式：`uv tool install deepagents-code`（`dcode` / `deepagents-code` 是入口）。
- 主要运行时依赖：
  - 框架：`deepagents==0.7.0a3`、`langchain>=1.3.11`、`langgraph-checkpoint-sqlite`、`langgraph-sdk`、`langgraph-cli[inmem]`、`langgraph-runtime-inmem`、`httpx`。
  - 模型/Provider：`langchain-anthropic`、`langchain-google-genai`、`langchain-openai`（更多 provider 走 optional-extras）。
  - TUI：`textual`、`textual-autocomplete`、`textual-speedups`、`prompt-toolkit`、`rich`、`markdownify`。
  - Sandbox：`langsmith[sandbox]`。
  - 工具：`tavily-python`、`langchain-quickjs`。
  - 其它：`pyperclip`、`packaging`、`uuid-utils`、`python-dotenv`、`requests`、`pillow`、`pyyaml`、`aiosqlite`、`tomli-w`、`langchain-mcp-adapters`、`deepagents-acp`、`mcp`。
- Windows 相关注意：以上 wheel 都能从 PyPI 拉预编译包，不需要本地 C/C++ 工具链；`textual` 建议搭配 Windows Terminal / PowerShell 7 以获得完整颜色和 emoji。

### `web/install.ps1` 关键改动
增加 **第 0 步**：确保存在满足 3.11 的 conda 环境；将该环境的 `python.exe` 通过 `uv tool install --python` 传给 uv，从而避免依赖 uv 自己下载 CPython 或用户机器上已有的低版本 Python。

新增/修改点：

1. 新增顶部注释里 4 个可覆盖环境变量：`MINICONDA_URL`、`MINICONDA_PREFIX`、`CONDA_ENV_NAME`（默认 `deepagents`）、`PYTHON_VERSION`（默认 `3.11`）。
2. 工具函数：
   - `Add-CondaToPath($prefix)`：把 `$prefix`、`$prefix\Scripts`、`$prefix\Library\bin`、`$prefix\condabin` 追加进当前会话 `PATH`。
   - `Get-CondaExe`：优先 PATH 上的 `conda`，其次 `$MinicondaPrefix\Scripts\conda.exe`。
   - `Install-Miniconda`：`Invoke-WebRequest` 下载 `Miniconda3-latest-Windows-x86_64.exe`，`Start-Process` 静默安装 (`/InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D=$MinicondaPrefix`)。参数拼成 **单一字符串**，绕开 `/D=` 必须“无引号且末尾”的限制。
   - `Ensure-CondaPython`：如果没 conda 就装；确保 `$CondaEnvName` 存在，`python=$RequiredPyVer`；若已存在但 Python < 3.11 则 `conda install python=$RequiredPyVer` 升级；返回该环境的 `python.exe` 路径。
3. `$CondaPython = Ensure-CondaPython`，之后 `uv tool install` 增加 `--python $CondaPython`。
4. 私有 PyPI 的精确 pin 与 `--index-strategy unsafe-best-match` 说明 **不动**（那是为了避开公共 PyPI 上同名的 0.1.x 包）。

### 用户体验
Windows 上零 Python 环境的用户执行 `irm http://.../install.ps1 | iex` 后：
Miniconda 静默安装 → conda 创建 `deepagents` env (`python=3.11`) → 装 uv → uv 用该 env 的 python 从私有 PyPI 精确 pin 安装 `deepagents-code` → 校验 `dcode` 命令。

### 关键操作 / 文件改动
- 修改：`web/install.ps1`
  - 顶部注释新增 4 个环境变量说明。
  - 新增 conda / Miniconda 自举段（约 100 行）。
  - `uv tool install` 追加 `--python $CondaPython`。

### 后续 TODO（未做）
- `web/install.sh` (macOS/Linux) 是否也希望走 conda 路径？当前只按用户要求改了 Windows。
- 是否需要 `uninstall.ps1` 同步移除 conda env（当前保留 env，避免误伤用户其它工具）。
- Miniconda 官方安装器只有 x86_64 版本；如果未来需要 ARM64（Windows on ARM），应换成 `Miniforge3` 的 arm64 安装器并加架构
