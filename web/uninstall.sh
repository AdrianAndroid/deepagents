#!/usr/bin/env bash
# Uninstall deepagents-code (dcode) — broad-spectrum cleanup.
#
# Removes deepagents-code no matter how it was installed:
#   - uv tool install    (our recommended path)
#   - pipx install
#   - pip install / pip install --user  (public PyPI copy)
#   - stray shims in ~/.local/bin, ~/.cargo/bin, /usr/local/bin
#
# Usage:
#   curl -fsSL http://8.152.204.58:40080/uninstall.sh | bash
#   bash uninstall.sh
#   # dry-run (only show what would happen):
#   DRY_RUN=1 bash uninstall.sh
set -uo pipefail

PKG_NAME="deepagents-code"
BIN_NAMES=("dcode" "deepagents-code" "deepagents")
DRY_RUN="${DRY_RUN:-0}"

log()  { printf '\033[1;34m[uninstall]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
run()  {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '\033[1;35m[dry-run]\033[0m %s\n' "$*"
  else
    log "\$ $*"
    "$@" || return $?
  fi
}

changed=0

# --- 1. uv tool ------------------------------------------------------------
if command -v uv >/dev/null 2>&1; then
  if uv tool list 2>/dev/null | awk '{print $1}' | grep -qx "${PKG_NAME}"; then
    log "found via 'uv tool'; uninstalling..."
    run uv tool uninstall "${PKG_NAME}" && changed=1
  else
    log "'uv tool' has no ${PKG_NAME}"
  fi
else
  log "uv not installed; skipping uv tool"
fi

# --- 2. pipx ---------------------------------------------------------------
if command -v pipx >/dev/null 2>&1; then
  if pipx list --short 2>/dev/null | awk '{print $1}' | grep -qx "${PKG_NAME}"; then
    log "found via 'pipx'; uninstalling..."
    run pipx uninstall "${PKG_NAME}" && changed=1
  else
    log "'pipx' has no ${PKG_NAME}"
  fi
fi

# --- 3. pip (system / --user / every python on PATH) -----------------------
# The public PyPI copy is often installed via a plain `pip install`, so we
# have to try every python interpreter we can find and every scope.
pythons=()
for py in python3 python python3.13 python3.12 python3.11 python3.10 python3.9; do
  if command -v "$py" >/dev/null 2>&1; then
    resolved="$(command -v "$py")"
    # dedupe
    seen=0
    for p in "${pythons[@]:-}"; do [[ "$p" == "$resolved" ]] && seen=1 && break; done
    [[ $seen -eq 0 ]] && pythons+=("$resolved")
  fi
done

for py in "${pythons[@]:-}"; do
  # both --user scope and default scope
  for scope in "" "--user"; do
    if "$py" -m pip show "${PKG_NAME}" >/dev/null 2>&1; then
      log "found via '$py -m pip ${scope:-<default>}'; uninstalling..."
      # shellcheck disable=SC2086
      run "$py" -m pip uninstall -y $scope "${PKG_NAME}" && changed=1
    fi
  done
done

# --- 4. clean stray shims --------------------------------------------------
# Some installers drop a `dcode` script into ~/.local/bin (or similar)
# that outlives the actual package uninstall.
declare -a shim_dirs=(
  "$HOME/.local/bin"
  "$HOME/.cargo/bin"
  "/usr/local/bin"
  "/opt/homebrew/bin"
)
for dir in "${shim_dirs[@]}"; do
  [[ -d "$dir" ]] || continue
  for name in "${BIN_NAMES[@]}"; do
    path="$dir/$name"
    if [[ -e "$path" || -L "$path" ]]; then
      # be conservative: only delete if it looks like a Python entry-point
      # shim (references site-packages / the package name), OR if the shim
      # is now broken.
      if [[ -L "$path" ]] && ! [[ -e "$path" ]]; then
        log "removing broken symlink: $path"
        run rm -f "$path" && changed=1
      elif head -c 2048 "$path" 2>/dev/null | grep -q -E "${PKG_NAME}|deepagents_code|site-packages"; then
        log "removing shim: $path"
        run rm -f "$path" && changed=1
      fi
    fi
  done
done

# --- 5. summary + residual check ------------------------------------------
if [[ $changed -eq 0 ]]; then
  warn "no ${PKG_NAME} installation was detected"
fi

log "post-cleanup check:"
found_any=0
for name in "${BIN_NAMES[@]}"; do
  if command -v "$name" >/dev/null 2>&1; then
    warn "  ${name} still resolves to: $(command -v "$name")"
    # `command -v -a` isn't portable (macOS bash 3.2); use `type -a` instead.
    all="$(type -a "$name" 2>/dev/null | awk '{print $NF}' | awk '!seen[$0]++' | tr '\n' ' ' | sed 's/ $//')"
    [[ -n "$all" ]] && warn "  (all matches: ${all})"
    found_any=1
  fi
done
[[ $found_any -eq 0 ]] && log "  no dcode/deepagents-code binary remains on PATH"

log "done."
