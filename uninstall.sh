#!/usr/bin/env bash
set -euo pipefail

REMOVE_DATA="${DCODE_REMOVE_DATA:-0}"

if [ -t 1 ] || [ "${FORCE_COLOR:-}" = "1" ]; then
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  NC='\033[0m'
else
  GREEN=''
  YELLOW=''
  NC=''
fi

success() { printf "${GREEN}✔${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${NC} %s\n" "$*" >&2; }

if command -v uv >/dev/null 2>&1; then
  uv tool uninstall deepagents-code || true
else
  warn "uv not found. If dcode was installed another way, remove it manually."
fi

if [ "$REMOVE_DATA" = "1" ]; then
  rm -rf \
    "$HOME/.cache/deepagents-code" \
    "$HOME/.config/deepagents-code" \
    "$HOME/.local/share/deepagents-code" \
    "$HOME/.deepagents"
  success "Removed deepagents-code user data."
else
  warn "User data was kept. Set DCODE_REMOVE_DATA=1 to remove cached/config data."
fi

success "dcode uninstalled."
