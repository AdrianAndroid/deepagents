#!/usr/bin/env bash
# Uninstall deepagents-code (dcode).
#
# Usage:
#   curl -fsSL http://8.152.204.58:40080/uninstall.sh | bash
#   bash uninstall.sh
set -euo pipefail

PKG_NAME="deepagents-code"

log()  { printf '\033[1;34m[uninstall]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }

if ! command -v uv >/dev/null 2>&1; then
  warn "uv not found — nothing to uninstall via uv tool"
  exit 0
fi

if uv tool list 2>/dev/null | grep -q "^${PKG_NAME}\b"; then
  log "removing ${PKG_NAME} via uv tool uninstall..."
  uv tool uninstall "${PKG_NAME}"
else
  warn "${PKG_NAME} is not installed as a uv tool"
fi

# Legacy fallback: also try pipx / pip user install, in case someone chose
# those methods manually.
if command -v pipx >/dev/null 2>&1 && pipx list 2>/dev/null | grep -q "${PKG_NAME}"; then
  log "also removing from pipx..."
  pipx uninstall "${PKG_NAME}" || true
fi

log "done."
