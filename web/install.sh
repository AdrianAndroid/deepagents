#!/usr/bin/env bash
# Install deepagents-code (dcode) from the private PyPI server.
#
# Usage:
#   curl -fsSL http://8.152.204.58:40080/install.sh | bash
#   # or download first, then run:
#   bash install.sh
#
# Env overrides:
#   PYPI_HOST=8.152.204.58:48080
#   PYPI_USER=admin
#   PYPI_PASSWORD=admin
#   PKG_VERSION=            # e.g. 0.0.2; empty = latest
set -euo pipefail

PYPI_HOST="${PYPI_HOST:-8.152.204.58:48080}"
PYPI_USER="${PYPI_USER:-admin}"
PYPI_PASSWORD="${PYPI_PASSWORD:-admin}"
PKG_NAME="deepagents-code"
PKG_VERSION="${PKG_VERSION:-}"

INDEX_URL="http://${PYPI_USER}:${PYPI_PASSWORD}@${PYPI_HOST}/simple/"
# Public providers still needed for transitive deps.
EXTRA_INDEX_URL="${EXTRA_INDEX_URL:-https://pypi.org/simple/}"

log()  { printf '\033[1;34m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

# --- 1. ensure uv is installed --------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  log "uv not found, installing via astral.sh installer..."
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    die "need curl or wget to bootstrap uv"
  fi
  # shellcheck disable=SC1091
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  command -v uv >/dev/null 2>&1 || die "uv installed but not on PATH; open a new shell and re-run"
fi
log "uv: $(uv --version)"

# --- 2. install deepagents-code as a uv tool ------------------------------
SPEC="${PKG_NAME}"
[[ -n "${PKG_VERSION}" ]] && SPEC="${PKG_NAME}==${PKG_VERSION}"

log "installing ${SPEC} from ${PYPI_HOST}"
uv tool install "${SPEC}" \
  --force \
  --index-url  "${INDEX_URL}" \
  --extra-index-url "${EXTRA_INDEX_URL}" \
  --index-strategy unsafe-best-match

# --- 3. PATH check ---------------------------------------------------------
UV_BIN="$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
if [[ ":$PATH:" != *":$UV_BIN:"* ]]; then
  warn "${UV_BIN} is not in PATH. Add it with:"
  printf '  echo '\''export PATH="%s:$PATH"'\'' >> ~/.zshrc && source ~/.zshrc\n' "${UV_BIN}"
fi

# --- 4. verify -------------------------------------------------------------
if command -v dcode >/dev/null 2>&1; then
  log "installed: $(command -v dcode)"
  log "run: dcode"
else
  warn "dcode not on PATH yet; open a new terminal or update PATH as shown above"
fi

log "done."
