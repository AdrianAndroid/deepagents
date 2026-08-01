#!/usr/bin/env bash
# Terminal usage:
#   /Users/zhaojian/code/deepagents/libs/code/run-zjcode-dev.sh
#   ZJCODE_DEV_VENV="$HOME/.local/share/zjcode-dev" /Users/zhaojian/code/deepagents/libs/code/run-zjcode-dev.sh
#
# After installation, run the TUI from any terminal with:
#   zjcode-dev
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ZJCODE_DEV_VENV:-$HOME/.local/share/zjcode-dev}"
BIN_DIR="$HOME/.local/bin"
SHELL_RC="$HOME/.zshrc"

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/\n' >&2
  exit 1
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
  uv venv "$VENV_DIR"
fi

uv pip install --python "$VENV_DIR/bin/python" -e "$SCRIPT_DIR" --upgrade

mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/zjcode" "$BIN_DIR/zjcode-dev"

if ! grep -F 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_RC" >/dev/null 2>&1; then
  printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$SHELL_RC"
fi

printf 'zjcode-dev installed successfully. Restart terminal or run: source %s\n' "$SHELL_RC"
printf 'Then run from any directory with: zjcode-dev\n'
