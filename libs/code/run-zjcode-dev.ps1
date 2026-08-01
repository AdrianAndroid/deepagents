# ============================================================
# run-zjcode-dev.ps1 - Windows 一键部署 zjcode-dev（全局可用）
#
# 对应 macOS/Linux 版 run-zjcode-dev.sh：
#   1. 检查 uv
#   2. 在 %LOCALAPPDATA%\zjcode-dev（或 $env:ZJCODE_DEV_VENV）创建独立 venv
#   3. 以 editable 模式安装当前包
#   4. 在 %USERPROFILE%\.local\bin 生成 zjcode-dev.cmd 转发器
#   5. 把该目录写入用户 PATH（持久化）
#
# 用法（PowerShell）：
#   .\run-zjcode-dev.ps1
#
# 可覆盖环境变量：
#   $env:ZJCODE_DEV_VENV = "D:\envs\zjcode-dev"; .\run-zjcode-dev.ps1
#
# 安装完成后，重开一个终端，任意目录直接运行：
#   zjcode-dev
# ============================================================

$ErrorActionPreference = "Stop"

# ---- 基础路径 ----
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir   = if ($env:ZJCODE_DEV_VENV) { $env:ZJCODE_DEV_VENV } else { Join-Path $env:LOCALAPPDATA "zjcode-dev" }
$Python    = Join-Path $VenvDir "Scripts\python.exe"
$ZjcodeExe = Join-Path $VenvDir "Scripts\zjcode.exe"
$BinDir    = Join-Path $env:USERPROFILE ".local\bin"
$ShimPath  = Join-Path $BinDir "zjcode-dev.cmd"

Write-Host "======================================================"
Write-Host "  zjcode-dev 全局安装 (Windows)"
Write-Host "  source    : $ScriptDir"
Write-Host "  venv      : $VenvDir"
Write-Host "  bin dir   : $BinDir"
Write-Host "======================================================"

# ---- 1. 检查 uv ----
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[X] 未检测到 uv，请先安装：https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Red
    exit 1
}
Write-Host "==> uv: $(& uv --version)"

# ---- 2. 创建 venv ----
if (-not (Test-Path $Python)) {
    Write-Host "==> 创建 venv：$VenvDir"
    & uv venv $VenvDir
} else {
    Write-Host "==> 已存在 venv，跳过创建"
}

# ---- 3. editable 安装当前包 ----
# 使用清华 TUNA PyPI 镜像，规避 pypi.org TLS 握手失败问题
$IndexUrl = if ($env:UV_INDEX_URL) { $env:UV_INDEX_URL } else { "https://pypi.tuna.tsinghua.edu.cn/simple" }
Write-Host "==> uv pip install -e $ScriptDir --upgrade  (index: $IndexUrl)"
& uv pip install --python $Python --index-url $IndexUrl -e $ScriptDir --upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] uv pip install 失败 (exit $LASTEXITCODE)，请检查网络或镜像 $IndexUrl" -ForegroundColor Red
    exit $LASTEXITCODE
}

if (-not (Test-Path $ZjcodeExe)) {
    Write-Host "[X] 安装后未找到 $ZjcodeExe，安装失败" -ForegroundColor Red
    exit 1
}

# ---- 4. 生成 zjcode-dev.cmd shim ----
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

# 用 .cmd 转发到 venv 里的 zjcode.exe，避免依赖符号链接权限
$shimContent = "@echo off`r`n""$ZjcodeExe"" %*`r`n"
Set-Content -Path $ShimPath -Value $shimContent -Encoding ASCII -NoNewline
Write-Host "==> 生成 shim：$ShimPath"

# ---- 5. 将 BinDir 追加到 User PATH（持久化） ----
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) { $userPath = "" }
$pathEntries = $userPath.Split(';') | Where-Object { $_ -ne "" }
$alreadyOnPath = $pathEntries | Where-Object { $_.TrimEnd('\') -ieq $BinDir.TrimEnd('\') }

if (-not $alreadyOnPath) {
    $newPath = if ($userPath.TrimEnd(';') -eq "") { $BinDir } else { $userPath.TrimEnd(';') + ";" + $BinDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "==> 已写入用户 PATH：$BinDir"
    $pathUpdated = $true
} else {
    Write-Host "==> 用户 PATH 已包含 $BinDir，跳过"
    $pathUpdated = $false
}

# 当前会话立即可用
if (-not ($env:Path.Split(';') | Where-Object { $_.TrimEnd('\') -ieq $BinDir.TrimEnd('\') })) {
    $env:Path = "$env:Path;$BinDir"
}

Write-Host ""
Write-Host "[OK] zjcode-dev 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "验证："
Write-Host "  zjcode-dev --help"
Write-Host ""
if ($pathUpdated) {
    Write-Host "注意：PATH 变更对新开的终端生效。当前 PowerShell 会话已临时注入，可直接运行 zjcode-dev。" -ForegroundColor Yellow
}
