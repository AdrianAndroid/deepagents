$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = if ($env:ZJCODE_DEV_VENV) { $env:ZJCODE_DEV_VENV } else { Join-Path $env:LOCALAPPDATA "zjcode-dev" }
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Zjcode = Join-Path $VenvDir "Scripts\zjcode.exe"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

if (-not (Test-Path $Python)) {
    uv venv $VenvDir
}

# 使用清华 TUNA PyPI 镜像，规避 pypi.org TLS 握手失败问题
$IndexUrl = if ($env:UV_INDEX_URL) { $env:UV_INDEX_URL } else { "https://pypi.tuna.tsinghua.edu.cn/simple" }

uv pip install --python $Python --index-url $IndexUrl -e $ScriptDir --upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Error "uv pip install 失败 (exit $LASTEXITCODE)，请检查网络或镜像 $IndexUrl"
    exit $LASTEXITCODE
}

if (-not (Test-Path $Zjcode)) {
    Write-Error "安装后未找到 $Zjcode，安装失败"
    exit 1
}

& $Zjcode @args
exit $LASTEXITCODE
