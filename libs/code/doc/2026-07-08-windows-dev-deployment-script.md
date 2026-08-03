# 2026-07-08 · Windows 开发环境部署脚本

## 轮次 1 - 生成 run-dcode-dev.ps1（对应 run-dcode-dev.sh 的 Windows 版）

### 用户提问要点
- 目标：在开发环境下部署 `libs/code`（deepagents-code），使得终端任何位置都能直接运行命令。
- 现状：项目里已有 macOS/Linux 版脚本 `run-dcode-dev.sh`，希望参考它生成一个 Windows 版部署脚本。

### 现状梳理（既有脚本）
- `libs/code/run-setup-dev-env.sh` + `setup-dev-env.ps1`：基于 conda 环境的**开发依赖安装**脚本（uv sync + test group），不负责暴露全局命令。
- `libs/code/run-dcode-dev.sh`：真正的"全局可用"部署脚本，做法是
  1. 校验 `uv`；
  2. 在 `~/.local/share/dcode-dev` 建立独立 venv；
  3. `uv pip install -e <repo> --upgrade`；
  4. 在 `~/.local/bin/dcode-dev` 建立到 `venv/bin/dcode` 的软链；
  5. 若 `.zshrc` 未包含 `$HOME/.local/bin`，则追加导出 PATH。
- `libs/code/dcode-dev.ps1`：只是"运行时安装并直接调用"的 launcher，不做 shim/PATH 持久化，不满足"任何终端任何目录直接跑"的需求。

### 结论 / 方案
生成 `libs/code/run-dcode-dev.ps1`，严格对齐 `run-dcode-dev.sh` 的语义，Windows 化改造点：
- venv 目录默认 `%LOCALAPPDATA%\dcode-dev`，支持 `$env:DCODE_DEV_VENV` 覆盖。
- 用 `uv pip install --python <venv>\Scripts\python.exe -e <ScriptDir> --upgrade` 完成 editable 安装。
- 全局入口：`%USERPROFILE%\.local\bin\dcode-dev.cmd`，内容 `@echo off` + `"<venv>\Scripts\dcode.exe" %*`。
  - **不使用软链**（`New-Item -ItemType SymbolicLink` 需要开发者模式或管理员权限），改用 `.cmd` 转发脚本，兼容性最好。
- PATH 持久化：通过 `[Environment]::SetEnvironmentVariable("Path", ..., "User")` 写入**用户级** PATH；同时在当前 PowerShell 会话中追加 `$env:Path`，让当前窗口立即生效。
- 幂等：venv 已存在跳过创建；PATH 已包含目标目录跳过写入。

### 关键操作 / 文件改动
- 新增 `D:\deepagents\libs\code\run-dcode-dev.ps1`
  - 打印安装计划（源目录、venv、bin 目录）
  - 校验 `uv` 存在
  - `uv venv $VenvDir`（若缺失）
  - `uv pip install --python $VenvDir\Scripts\python.exe -e $ScriptDir --upgrade`
  - 生成 `.local\bin\dcode-dev.cmd` shim
  - 用户 PATH 持久化 + 当前会话 PATH 注入
  - 打印验证命令 `dcode-dev --help`

### 使用方式
```powershell
cd D:\deepagents\libs\code
.\run-dcode-dev.ps1
# 之后：任意新终端、任意目录
dcode-dev
```

### 先决条件
- 已安装 `uv`。未安装时的一键命令：
  ```powershell
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

### 与既有脚本的差异对照
| 项 | run-dcode-dev.sh (mac/Linux) | run-dcode-dev.ps1 (Windows, 新) |
| --- | --- | --- |
| venv 位置 | `~/.local/share/dcode-dev` | `%LOCALAPPDATA%\dcode-dev` |
| 覆盖变量 | `DCODE_DEV_VENV` | `$env:DCODE_DEV_VENV` |
| 全局入口 | `~/.local/bin/dcode-dev` (symlink → `venv/bin/dcode`) | `%USERPROFILE%\.local\bin\dcode-dev.cmd` (转发脚本) |
| PATH 持久化 | 追加 `export PATH=...` 到 `~/.zshrc` | 用户级 PATH 环境变量（`SetEnvironmentVariable ... "User"`) |
| 立即生效 | 需 `source ~/.zshrc` 或新终端 | 当前会话追加 `$env:Path`；新终端自动 |

### 后续 TODO
- 无强制项。可考虑：
  - 增加 `-Uninstall` 开关：删除 shim 和 venv，并从用户 PATH 移除该目录。
  - 若需要保留符号链接风格，可在检测到开发者模式/管理员时改用 `New-Item -ItemType SymbolicLink`；当前 `.cmd` 方案已足够健壮，暂不需要。
