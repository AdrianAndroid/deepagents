#!/bin/bash
# ============================================================
# setup-dev-env.sh — 创建 deepagents-code 开发环境
#
# 功能：
#   1. 检查/创建 conda 环境（默认 deepagents / Python 3.12）
#   2. 激活环境
#   3. 安装核心工具：uv、build、twine、hatchling
#   4. 用 uv sync 安装本包（editable）及所有依赖 + test 分组
#      → 自动装齐：pytest、ruff、ty、textual-dev、pytest-cov 等
#
# 用法：
#   ./setup-dev-env.sh
#
# 可覆盖环境变量：
#   ENV_NAME=myenv PYTHON_VER=3.11 ./setup-dev-env.sh
# ============================================================

# 禁止通过 source 执行：source 会污染当前 shell，且脚本中的 exit 会关闭 VS Code 等终端
if [[ -n "${BASH_SOURCE[0]}" ]] && [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "❌ 请直接运行本脚本，不要通过 source 执行: ./$(basename "${BASH_SOURCE[0]}")" >&2
    return 1
fi

set -e

# ========== 自定义配置区 ==========
ENV_NAME="${ENV_NAME:-deepagents}"
PYTHON_VER="${PYTHON_VER:-3.12}"
# ===================================

# 切到脚本所在目录（libs/code）
cd "$(dirname "$0")"

echo "======================================================"
echo "  deepagents-code 开发环境安装"
echo "  conda env : ${ENV_NAME}"
echo "  python    : ${PYTHON_VER}"
echo "  workdir   : $(pwd)"
echo "======================================================"

# 加载 conda 初始化脚本
if ! command -v conda &> /dev/null; then
    echo "❌ 未检测到 conda，请先安装 Miniconda/Anaconda 后重试"
    echo "wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    exit 1
fi
source "$(conda info --base)/etc/profile.d/conda.sh"

# 接受 Anaconda 默认频道的服务条款（ToS），否则新版 conda 创建环境会报 CondaToSNonInteractiveError
if conda tos --help &> /dev/null; then
    echo "==> 接受 conda 默认频道的服务条款（ToS）..."
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true
fi

# 判断环境是否存在，不存在则创建
if ! conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    echo "==> 未检测到 conda 环境 ${ENV_NAME}，创建 Python ${PYTHON_VER} 环境..."
    conda create -n "${ENV_NAME}" python="${PYTHON_VER}" -y
else
    echo "==> conda 环境 ${ENV_NAME} 已存在，跳过创建"
fi

# 激活环境
conda activate "${ENV_NAME}"
echo "==> 当前 Python: $(python --version) @ $(which python)"

# 安装 uv（包管理器）
if ! command -v uv &> /dev/null; then
    echo "==> 未检测到 uv，pip 安装 uv..."
    pip install --upgrade uv
else
    echo "==> uv 已安装：$(uv --version)"
fi

# 使用 uv 安装打包/发布相关工具（放入当前 conda 环境）
echo "==> 安装打包与发布工具：build / twine / hatchling ..."
uv pip install --upgrade build twine hatchling

# 用 uv sync 安装本包（editable）+ 全部依赖 + test 分组
# test 分组会自动装齐 pytest、ruff、ty、textual-dev、pytest-cov 等开发工具
echo "==> uv sync 安装依赖（editable，含 test 分组）..."
uv sync --group test

echo ""
echo "🎉 开发环境准备完成！"
echo ""
echo "已安装的关键工具："
echo "  - uv        $(uv --version 2>/dev/null | awk '{print $2}')"
echo "  - python    $(python --version 2>&1 | awk '{print $2}')"
echo "  - pytest    $(uv run --frozen pytest --version 2>/dev/null | awk '{print $2}' | head -1)"
echo "  - ruff      $(uv run --frozen ruff --version 2>/dev/null | awk '{print $2}')"
echo "  - twine     $(twine --version 2>/dev/null | head -1)"
echo ""
echo "下一步："
echo "  conda activate ${ENV_NAME}"
echo "  zjcode --help             # 运行 CLI"
echo "  make test                 # 跑单元测试"
echo "  make lint                 # 代码检查"
echo "  ./run-publish.sh          # 构建并发布到公开 PyPI"
