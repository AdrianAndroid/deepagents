# Create Windows Dcode Dev Script

- Time: 2026-07-01T14:26:53+08:00
- Project: deepagents

## Prompt

再生成一个windows11下可运行的脚本<environment_details>
Current time: 2026-07-01T14:26:53+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/dcode-dev.sh
Visible files:
  libs/code/dcode-dev.sh
Open tabs:
  libs/code/dcode-dev.sh
</environment_details>

## AI Response

已创建：

`libs/code/dcode-dev.ps1`

Windows 11 PowerShell 使用：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\libs\code\dcode-dev.ps1
```

脚本会自动创建 `%LOCALAPPDATA%\dcode-dev` 虚拟环境、editable 安装/更新当前 `libs/code`，然后启动 `dcode`。
