#!/usr/bin/env bash
# Install zjcode from the public PyPI.
#
# Usage:
#   curl -fsSL <site>/install.sh | bash
#   # or download first, then run:
#   bash install.sh
#
# Env overrides:
#   PKG_VERSION=            # e.g. 0.0.2; empty = latest
#   INDEX_URL=              # override PyPI index (rarely needed)
#
# Notes:
#   - `zjcode` currently depends on `deepagents==0.7.0a7` (a pre-release),
#     so we pass `--prerelease=allow` to let uv accept it.
set -euo pipefail

PKG_NAME="zjcode"
PKG_VERSION="${PKG_VERSION:-}"
INDEX_URL="${INDEX_URL:-https://pypi.org/simple/}"

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

# --- 2. detect existing install -------------------------------------------
# `uv tool list` prints entries like:  zjcode v0.0.2
CURRENT_VER="$(uv tool list 2>/dev/null | awk -v pkg="${PKG_NAME}" '$1==pkg{print $2}')"

if [[ -n "${PKG_VERSION}" ]]; then
  SPEC="${PKG_NAME}==${PKG_VERSION}"
else
  SPEC="${PKG_NAME}"
fi

if [[ -n "${CURRENT_VER}" ]]; then
  if [[ -z "${PKG_VERSION}" ]]; then
    log "detected ${PKG_NAME} ${CURRENT_VER}; upgrading to latest..."
  else
    log "detected ${PKG_NAME} ${CURRENT_VER}; reinstalling ${SPEC}..."
  fi
else
  log "installing ${SPEC} from ${INDEX_URL}"
fi

# --prerelease=allow is required because zjcode depends on
# `deepagents==0.7.0a7` which is an alpha pre-release. Without this flag uv
# refuses to consider pre-releases for transitive deps.
# --force covers both first-install and upgrade in one code path.
uv tool install "${SPEC}" \
  --force \
  --index-url "${INDEX_URL}" \
  --prerelease=allow

NEW_VER="$(uv tool list 2>/dev/null | awk -v pkg="${PKG_NAME}" '$1==pkg{print $2}')"

if [[ -n "${CURRENT_VER}" && -n "${NEW_VER}" ]]; then
  if [[ "${CURRENT_VER}" == "${NEW_VER}" ]]; then
    log "${PKG_NAME} already at ${NEW_VER} (no change)"
  else
    log "${PKG_NAME} upgraded: ${CURRENT_VER} -> ${NEW_VER}"
  fi
elif [[ -n "${NEW_VER}" ]]; then
  log "${PKG_NAME} installed: ${NEW_VER}"
fi

# --- 3. PATH check ---------------------------------------------------------
UV_BIN="$(uv tool dir --bin 2>/dev/null || echo "$HOME/.local/bin")"
if [[ ":$PATH:" != *":$UV_BIN:"* ]]; then
  warn "${UV_BIN} is not in PATH. Add it with:"
  printf '  echo '\''export PATH="%s:$PATH"'\'' >> ~/.zshrc && source ~/.zshrc\n' "${UV_BIN}"
fi

# --- 4. verify -------------------------------------------------------------
if command -v zjcode >/dev/null 2>&1; then
  log "installed: $(command -v zjcode)"
  log "run: zjcode"
else
  warn "zjcode not on PATH yet; open a new terminal or update PATH as shown above"
fi

log "done."
