#!/usr/bin/env bash
set -euo pipefail

VERSION="${DCODE_VERSION:-0.1.24}"
BASE_URL="${DCODE_BASE_URL:-http://8.152.204.58:40000/download/dcode/releases/${VERSION}}"
WHEEL="deepagents_code-${VERSION}-py3-none-any.whl"
PYTHON="${DCODE_PYTHON:-3.13}"
SKIP_OPTIONAL="${DCODE_SKIP_OPTIONAL:-0}"

if [ -t 1 ] || [ "${FORCE_COLOR:-}" = "1" ]; then
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  CYAN='\033[0;36m'
  RED='\033[0;31m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN=''
  YELLOW=''
  CYAN=''
  RED=''
  BOLD=''
  NC=''
fi

info() { printf "${CYAN}▸${NC} %s\n" "$*"; }
success() { printf "${GREEN}✔${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}⚠${NC} %s\n" "$*" >&2; }
error() { printf "${RED}✖${NC} %s\n" "$*" >&2; }

cleanup() {
  code=$?
  if [ "$code" -ne 0 ]; then
    echo "" >&2
    error "dcode installation failed with exit code ${code}."
  fi
}
trap cleanup EXIT

install_uv() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://astral.sh/uv/install.sh | sh
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://astral.sh/uv/install.sh | sh
  else
    error "curl or wget is required to install uv."
    exit 1
  fi
}

if ! command -v uv >/dev/null 2>&1; then
  info "uv not found; installing uv..."
  install_uv
  export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
  error "uv was installed but is not on PATH. Add ~/.local/bin to PATH and retry."
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"; cleanup' EXIT

info "Downloading ${WHEEL} from ${BASE_URL}..."
if command -v curl >/dev/null 2>&1; then
  curl -fL "${BASE_URL}/${WHEEL}" -o "${tmp}/${WHEEL}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${tmp}/${WHEEL}" "${BASE_URL}/${WHEEL}"
else
  error "curl or wget is required to download dcode."
  exit 1
fi

info "Installing dcode ${VERSION}..."
uv tool install -U --python "$PYTHON" "${tmp}/${WHEEL}"

if [ "$SKIP_OPTIONAL" != "1" ] && ! command -v rg >/dev/null 2>&1; then
  warn "ripgrep (rg) not found; file search may be slower."
  warn "Install it with your package manager, e.g. brew install ripgrep or apt install ripgrep."
fi

if command -v dcode >/dev/null 2>&1; then
  dcode --version || true
elif command -v deepagents-code >/dev/null 2>&1; then
  deepagents-code --version || true
else
  warn "dcode command is not on PATH yet. Restart your shell or add ~/.local/bin to PATH."
fi

success "dcode ${VERSION} installed successfully."
printf "Run: ${BOLD}dcode${NC}\n"
