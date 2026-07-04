#!/usr/bin/env bash
# 将当前 libs/code 项目临时部署为全局 `dcode` 命令 (可编辑安装)
#
# 用法:
#   ./dcode-deploy-global.sh             # 安装/更新
#   ./dcode-deploy-global.sh --uninstall # 卸载
#
# 安装后可在任意目录执行:
#   dcode
#
# 说明:
# - 使用 `uv tool install --editable`,源码改动立即生效,无需重装
# - 二进制会被 uv 放到 `~/.local/bin`,请确认该目录在 PATH 中
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="deepagents-code"

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv 未安装,请先安装: https://docs.astral.sh/uv/getting-started/installation/\n' >&2
  exit 1
fi

if [[ "${1:-}" == "--uninstall" ]]; then
  uv tool uninstall "$PACKAGE_NAME"
  printf '已卸载全局 dcode\n'
  exit 0
fi

uv tool install --editable "$PROJECT_DIR" --force

# 确保 uv tool 的 bin 目录在 PATH 中
UV_BIN="$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
if [[ ":$PATH:" != *":$UV_BIN:"* ]]; then
  printf '\n提示: %s 不在 PATH 中,可执行以下命令添加(zsh):\n' "$UV_BIN"
  printf '  echo '\''export PATH="%s:$PATH"'\'' >> ~/.zshrc && source ~/.zshrc\n' "$UV_BIN"
fi

printf '\n完成: 现在可以在任意目录运行 `dcode` (可编辑模式,源码改动即时生效)\n'
printf '卸载: %s --uninstall\n' "$0"
