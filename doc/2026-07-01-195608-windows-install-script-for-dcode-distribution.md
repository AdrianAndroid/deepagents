# Windows Install Script For Dcode Distribution

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T19:56:08+08:00
- Project: deepagents

## Prompt

要是windows呢?

## AI Response

Windows 建议额外提供 `install.ps1`，用户用 PowerShell 安装。

示例：

```powershell
$ErrorActionPreference = "Stop"

$Version = if ($env:DCODE_VERSION) { $env:DCODE_VERSION } else { "0.1.24" }
$BaseUrl = if ($env:DCODE_BASE_URL) { $env:DCODE_BASE_URL } else { "https://你的下载域名/dcode/releases/$Version" }
$Wheel = "deepagents_code-$Version-py3-none-any.whl"
$Python = if ($env:DCODE_PYTHON) { $env:DCODE_PYTHON } else { "3.13" }

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

$TempDir = New-Item -ItemType Directory -Force -Path ([System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "dcode-install"))
$WheelPath = Join-Path $TempDir $Wheel

Invoke-WebRequest "$BaseUrl/$Wheel" -OutFile $WheelPath
uv tool install -U --python $Python $WheelPath

dcode --version
Write-Host "dcode $Version installed successfully"
```

用户安装命令：

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://你的下载域名/dcode/latest/install.ps1 | iex"
```

下载站目录建议：

```text
dcode/latest/install.sh
dcode/latest/install.ps1
dcode/latest/deepagents_code-0.1.24-py3-none-any.whl
```
