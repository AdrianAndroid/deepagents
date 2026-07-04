# Uninstall deepagents-code (dcode). (Windows PowerShell)
#
# Usage:
#   irm http://8.152.204.58:40080/uninstall.ps1 | iex
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1

$ErrorActionPreference = "Continue"
$PkgName = "deepagents-code"

function Info($msg) { Write-Host "[uninstall] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[warn] $msg"      -ForegroundColor Yellow }

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Warn "uv not found - nothing to uninstall via uv tool"
    exit 0
}

$installed = (uv tool list 2>$null) -match "^$PkgName\b"
if ($installed) {
    Info "removing $PkgName via uv tool uninstall..."
    uv tool uninstall $PkgName
} else {
    Warn "$PkgName is not installed as a uv tool"
}

Info "done."
