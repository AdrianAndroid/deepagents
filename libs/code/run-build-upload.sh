#!/bin/bash
set -e

# ========== 自定义配置区 ==========
ENV_NAME="deepagents"
PYTHON_VER="3.12"
PYPI_REPO_URL="http://8.152.204.58:48080"
PYPI_USER="admin"
PYPI_PWD="admin"
# ===================================

# 加载conda初始化脚本
source "$(conda info --base)/etc/profile.d/conda.sh"

# 判断环境是否存在，不存在则创建
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "未检测到conda环境 ${ENV_NAME}，开始创建 Python ${PYTHON_VER} 环境..."
    conda create -n "${ENV_NAME}" python=${PYTHON_VER} -y
fi

# 激活环境
conda activate "${ENV_NAME}"

# 检测uv，不存在自动安装
if ! command -v uv &> /dev/null; then
    echo "未检测到uv，执行pip安装uv..."
    pip install uv
fi

# 安装上传工具twine
uv pip install twine

# 清理旧dist，全新构建whl+源码包
# 注意：uv build 没有 --clean，需要手动清理 dist/
rm -rf dist
uv build

# 一键上传私有仓库
echo "开始上传包至仓库：${PYPI_REPO_URL}"
twine upload \
    --repository-url "${PYPI_REPO_URL}" \
    --username "${PYPI_USER}" \
    --password "${PYPI_PWD}" \
    dist/*

echo "🎉 构建+上传私有PyPI完成！"
