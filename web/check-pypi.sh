#!/usr/bin/env bash
# Probe a private PyPI source for deepagents-code and report which APIs it
# supports: the Warehouse JSON API (used by dcode's built-in update check) and
# the PEP 503 Simple Index (used by uv/pip to install).
#
# Usage:
#   bash check-pypi.sh
#   PKG_NAME=deepagents PYPI_HOST=1.2.3.4:8080 bash check-pypi.sh
#
# Env overrides (defaults mirror web/install.sh):
#   PYPI_HOST=8.152.204.58:48080
#   PYPI_USER=admin
#   PYPI_PASSWORD=admin
#   PYPI_SCHEME=http
#   PKG_NAME=deepagents-code
set -euo pipefail

PYPI_HOST="${PYPI_HOST:-8.152.204.58:48080}"
PYPI_USER="${PYPI_USER:-admin}"
PYPI_PASSWORD="${PYPI_PASSWORD:-admin}"
PYPI_SCHEME="${PYPI_SCHEME:-http}"
PKG_NAME="${PKG_NAME:-deepagents-code}"
TIMEOUT="${TIMEOUT:-8}"

BASE="${PYPI_SCHEME}://${PYPI_USER}:${PYPI_PASSWORD}@${PYPI_HOST}"
JSON_URL="${BASE}/pypi/${PKG_NAME}/json"
SIMPLE_URL="${BASE}/simple/${PKG_NAME}/"

log()  { printf '\033[1;34m[check]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[ ok ]\033[0m %s\n' "$*"; }
bad()  { printf '\033[1;31m[fail]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

command -v curl >/dev/null 2>&1 || { bad "curl not found"; exit 1; }
PY="$(command -v python3 || command -v python || true)"

json_api_ok=0
simple_ok=0

# --- 1. Warehouse JSON API (dcode update_check.py needs this) --------------
log "probing JSON API: ${PYPI_SCHEME}://***@${PYPI_HOST}/pypi/${PKG_NAME}/json"
code="$(curl -s -m "${TIMEOUT}" -o /tmp/_pypi_json.$$ -w '%{http_code}' "${JSON_URL}" || echo 000)"
if [[ "${code}" == "200" ]] && [[ -n "${PY}" ]] \
   && "${PY}" - <<'PYEOF' /tmp/_pypi_json.$$ 2>/dev/null
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
info = d.get("info")
if not isinstance(info, dict) or not isinstance(info.get("version"), str):
    raise SystemExit(1)
rel = list(d.get("releases", {}))
print("    info.version =", info["version"])
print("    releases[:5] =", rel[:5])
PYEOF
then
  json_api_ok=1
  ok "JSON API supported — dcode's built-in update check can use this source"
else
  bad "JSON API unavailable (HTTP ${code}) — dcode update check would 404 here"
fi
rm -f /tmp/_pypi_json.$$

echo

# --- 2. PEP 503 Simple Index (uv/pip install uses this) --------------------
log "probing Simple Index: ${PYPI_SCHEME}://***@${PYPI_HOST}/simple/${PKG_NAME}/"
code="$(curl -s -m "${TIMEOUT}" -o /tmp/_pypi_simple.$$ -w '%{http_code}' "${SIMPLE_URL}" || echo 000)"
if [[ "${code}" == "200" ]]; then
  simple_ok=1
  ok "Simple Index reachable (HTTP 200) — uv/pip can install from this source"
  if [[ -n "${PY}" ]]; then
    "${PY}" - <<'PYEOF' /tmp/_pypi_simple.$$ 2>/dev/null || true
import re, sys
html = open(sys.argv[1], encoding="utf-8", errors="replace").read()
files = re.findall(r'>([^<]+\.(?:whl|tar\.gz|zip))<', html)
if files:
    print("    available files[:10]:")
    for f in files[:10]:
        print("      -", f)
PYEOF
  fi
else
  bad "Simple Index unreachable (HTTP ${code})"
fi
rm -f /tmp/_pypi_simple.$$

echo
# --- verdict ---------------------------------------------------------------
if [[ "${json_api_ok}" == "1" ]]; then
  ok "VERDICT: source is JSON-API compatible. You may point PYPI_URL at:"
  echo "         ${PYPI_SCHEME}://${PYPI_HOST}/pypi/${PKG_NAME}/json"
elif [[ "${simple_ok}" == "1" ]]; then
  warn "VERDICT: Simple-Index-only source (likely pypiserver). It supports"
  warn "         install but NOT dcode's JSON-API update check. Recommended:"
  warn "         disable auto-update with DEEPAGENTS_CODE_AUTO_UPDATE=0 and"
  warn "         install/upgrade via uv tool install --index-url ${SIMPLE_URL/${PYPI_USER}:${PYPI_PASSWORD}@/}"
else
  bad "VERDICT: source unreachable on both endpoints — check host/credentials."
fi
