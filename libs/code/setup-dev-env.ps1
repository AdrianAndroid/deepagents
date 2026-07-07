# ============================================================
# setup-dev-env.ps1 — 创建 deepagents-code 开发环境 (Windows)
#
# 功能：
#   1. 检查/创建 conda 环境（默认 deepagents / Python 3.12）
#   2. 激活环境
#   3. 安装核心工具：uv、build、twine、hatchling
#   4. 用 uv sync 安装本包（editable）及所有依赖 + test 分组
#      → 自动装齐：pytest、ruff、ty、textual-dev、pytest-cov 等
#
# 用法（PowerShell）：
#   .\setup-dev-env.ps1
#
# 可覆盖环境变量：
#   $env:ENV_NAME="myenv"; $env:PYTHON_VER="3.11"; .\setup-dev-env.ps1
# ===========================================================

$ErrorActionPreference = "Stop"

# ========== 自定义配置区 ==========
$ENV_NAME = if ($env:ENV_NAME) { $env:ENV_NAME } else { "deepagents" }
$PYTHON_VER = if ($env:PYTHON_VER) { $env:PYTHON_VER } else { "3.12" }
# ===================================

# 切到脚本所在目录（libs/code）
Set-Location $PSScriptRoot

Write-Host "======================================================"
Write-Host "  deepagents-code 开发环境安装"
Write-Host "  conda env : $ENV_NAME"
Write-Host "  python    : $PYTHON_VER"
Write-Host "  workdir   : $(Get-Location)"
Write-Host "======================================================"

# 加载 conda 初始化脚本
$condaExe = $null
$condaFromPath = $false
if ($env:CONDA_EXE -and (Test-Path $env:CONDA_EXE)) {
    $condaExe = $env:CONDA_EXE
} elseif (Get-Command conda -ErrorAction SilentlyContinue) {
    $condaExe = "conda"
    $condaFromPath = $true
} else {
    $candidatePaths = @(
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe"
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe"
        "$env:LOCALAPPDATA\anaconda3\Scripts\conda.exe"
        "$env:LOCALAPPDATA\miniconda3\Scripts\conda.exe"
        "$env:ProgramData\anaconda3\Scripts\conda.exe"
        "$env:ProgramData\miniconda3\Scripts\conda.exe"
        "C:\tools\anaconda3\Scripts\conda.exe"
        "C:\tools\miniconda3\Scripts\conda.exe"
    )
    foreach ($p in $candidatePaths) {
        if (Test-Path $p) {
            $condaExe = $p
            break
        }
    }
}

if (-not $condaExe) {
    Write-Host "未检测到 conda，请先安装 Miniconda/Anaconda 后重试" -ForegroundColor Red
    exit 1
}

# 计算 conda 安装根目录
$condaBase = (& $condaExe info --base | Out-String).Trim()
if (-not $condaBase) {
    Write-Host "无法获取 conda 安装根目录" -ForegroundColor Red
    exit 1
}

# 如果当前 shell 中还没有 conda 命令，source PowerShell hook
if (-not $condaFromPath) {
    $condaHook = Join-Path $condaBase "shell\condabin\conda-hook.ps1"
    if (-not (Test-Path $condaHook)) {
        # 兼容部分旧版/特殊安装
        $condaHook = Join-Path $condaBase "etc\profile.d\conda.ps1"
    }
    if (-not (Test-Path $condaHook)) {
        Write-Host "无法定位 conda PowerShell 初始化脚本 (conda-hook.ps1 / conda.ps1)，请检查 conda 安装" -ForegroundColor Red
        exit 1
    }
    . $condaHook
}

# 再次确认 conda 可用
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "conda 初始化失败，无法继续" -ForegroundColor Red
    exit 1
}

# 判断环境是否存在，不存在则创建
$envExists = (& conda env list) | ForEach-Object { ($_ -split '\s+')[0] } | Where-Object { $_ -eq $ENV_NAME }
if (-not $envExists) {
    Write-Host "==> 未检测到 conda 环境 $ENV_NAME，创建 Python $PYTHON_VER 环境..."
    & conda create -n $ENV_NAME python=$PYTHON_VER -y
} else {
    Write-Host "==> conda 环境 $ENV_NAME 已存在，跳过创建"
}

# 激活环境
& conda activate $ENV_NAME
Write-Host "==> 当前 Python: $(& python --version) @ $(& where.exe python)"

# 安装 uv（包管理器）
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "==> 未检测到 uv，pip 安装 uv..."
    & pip install --upgrade uv
} else {
    Write-Host "==> uv 已安装: $(& uv --version)"
}

# 使用 uv 安装打包/发布相关工具（放入当前 conda 环境）
Write-Host "==> 安装打包与发布工具：build / twine / hatchling ..."
& uv pip install --upgrade build twine hatchling

# 用 uv sync 安装本包（editable）+ 全部依赖 + test 分组
# test 分组会自动装齐 pytest、ruff、ty、textual-dev、pytest-cov 等开发工具
Write-Host "==> uv sync 安装依赖（editable，含 test 分组）..."
& uv sync --group test

Write-Host ""
Write-Host "开发环境准备完成！" -ForegroundColor Green
Write-Host ""

Write-Host "已安装的关键工具："
Write-Host "  - uv        $(& uv --version 2>$null)"
Write-Host "  - python    $(& python --version 2>&1)"
Write-Host "  - pytest    $(& uv run --frozen pytest --version 2>$null | Select-Object -First 1)"
Write-Host "  - ruff      $(& uv run --frozen ruff --version 2>$null)"
Write-Host "  - twine     $(& twine --version 2>$null | Select-Object -First 1)"
Write-Host ""

Write-Host "下一步："
Write-Host "  conda activate $ENV_NAME"
Write-Host "  dcode --help              # 运行 CLI"
Write-Host "  make test                 # 跑单元测试"
Write-Host "  make lint                 # 代码检查"
Write-Host "  .\run-build-upload.ps1     # 构建并上传到私有 PyPI"
