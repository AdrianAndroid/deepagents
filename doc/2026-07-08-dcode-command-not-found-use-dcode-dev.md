# 2026-07-08 dcode 命令找不到 —— 应使用 dcode-dev

## 现象

```
PS> dcode
dcode : 无法将"dcode"项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

## 原因

用户跑的是 `run-dcode-dev.ps1` 部署脚本，装出来的全局命令名是 **`dcode-dev`**，不是 `dcode`。这是脚本刻意做的区分，避免和正式发布版 `dcode`（`pipx install deepagents-code`）在 PATH 里冲突。

验证：
- `%LOCALAPPDATA%\dcode-dev\Scripts\dcode.exe` 存在（venv 内真身）
- `%USERPROFILE%\.local\bin\dcode-dev.cmd` 存在（PATH 里的 shim）
- 但没有 `dcode.cmd`，所以 `dcode` 命令找不到

## 结论

直接用 `dcode-dev`：

```powershell
dcode-dev
dcode-dev --help
```

## 备选方案（未采用）

- 在 `%USERPROFILE%\.local\bin` 再生成一个 `dcode.cmd` 转发到 venv 里的 `dcode.exe`，让 `dcode` 也可用（推荐给同时需要两个命名的场景）
- 把 `%LOCALAPPDATA%\dcode-dev\Scripts` 加进用户 PATH（不推荐：会同时暴露 venv 里的 python.exe、pip.exe 等所有脚本）

用户选择：直接用 `dcode-dev`，不改脚本。
