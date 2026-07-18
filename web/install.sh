#!/usr/bin/env bash
# Install zjcode from the private PyPI server.
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
#   PKG_VERSION=            # e.g. 0.0.1; empty = latest
set -euo pipefail

PYPI_HOST="${PYPI_HOST:-8.152.204.58:48080}"
PYPI_USER="${PYPI_USER:-admin}"
PYPI_PASSWORD="${PYPI_PASSWORD:-admin}"
PKG_NAME="zjcode"
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

# --- 2. detect existing install and resolve target version ---------------
# `zjcode` 目前只在私有源发布，公共 PyPI 上没有同名包，所以理论上不会拿到无关
# 包 —— 但如果哪天有人在公共 PyPI 抢注 `zjcode`，这段"锁死到本地存在的确切
# 版本"的策略仍然是我们唯一可靠的护栏。

# Helper: query private PyPI simple index and return highest version.
resolve_private_version() {
  local html versions
  html="$(curl -fsS "http://${PYPI_USER}:${PYPI_PASSWORD}@${PYPI_HOST}/simple/${PKG_NAME}/" 2>/dev/null || true)"
  [[ -z "${html}" ]] && return 1
  # Filenames look like `zjcode-0.0.1-py3-none-any.whl` or `.tar.gz`.
  # Extract the X.Y.Z version — we intentionally accept only pure
  # PEP 440 basic versions to keep the parser simple; extend if we ever
  # publish pre-releases to the private index.
  versions="$(printf '%s' "${html}" \
    | grep -oE 'zjcode-[0-9]+\.[0-9]+\.[0-9]+' \
    | sed -E 's/^zjcode-//' \
    | sort -V \
    | uniq)"
  [[ -z "${versions}" ]] && return 1
  printf '%s' "${versions}" | tail -n 1
}

if [[ -z "${PKG_VERSION}" ]]; then
  log "resolving latest ${PKG_NAME} version from private index ${PYPI_HOST}..."
  RESOLVED_VER="$(resolve_private_version || true)"
  if [[ -z "${RESOLVED_VER}" ]]; then
    die "cannot list ${PKG_NAME} on private index ${PYPI_HOST}; refusing to fall back to public PyPI"
  fi
  PKG_VERSION="${RESOLVED_VER}"
  log "resolved latest private version: ${PKG_VERSION}"
fi

SPEC="${PKG_NAME}==${PKG_VERSION}"

# `uv tool list` prints entries like:  zjcode v0.0.1
CURRENT_VER="$(uv tool list 2>/dev/null | awk -v pkg="${PKG_NAME}" '$1==pkg{print $2}')"

if [[ -n "${CURRENT_VER}" ]]; then
  log "detected ${PKG_NAME} ${CURRENT_VER}; installing ${SPEC}..."
else
  log "installing ${SPEC} from ${PYPI_HOST}"
fi

# We pass BOTH:
#   --index-url        : private PyPI (primary source of truth)
#   --extra-index-url  : public PyPI  (needed for transitive deps only)
#   --index-strategy unsafe-best-match
#
# Combined with the EXACT version pin resolved above, uv will only accept
# a `zjcode` wheel from the private index — the pin, not the strategy, is
# what enforces safety.
uv tool install "${SPEC}" \
  --force \
  --index-url  "${INDEX_URL}" \
  --extra-index-url "${EXTRA_INDEX_URL}" \
  --index-strategy unsafe-best-match \
  --prerelease=allow

NEW_VER="$(uv tool list 2>/dev/null | awk -v pkg="${PKG_NAME}" '$1==pkg{print $2}')"

# Safety check: private-source versions are always 0.0.x. If uv reported a
# higher version, the private-source guarantee failed; bail out loudly so
# the user knows they got the wrong package.
NEW_VER_NUM="${NEW_VER#v}"
case "${NEW_VER_NUM}" in
  0.0.*) : ;;  # ok, private-source build
  "" )   warn "could not confirm installed version" ;;
  *)     die "installed ${PKG_NAME} ${NEW_VER}, but expected a 0.0.x private-source build. Something pulled from public PyPI. Aborting." ;;
esac

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
