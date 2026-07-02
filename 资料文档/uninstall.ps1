$ErrorActionPreference = "Stop"

$RemoveData = if ($env:DCODE_REMOVE_DATA) { $env:DCODE_REMOVE_DATA } else { "0" }

function Write-Success($Message) { Write-Host "✔ $Message" -ForegroundColor Green }
function Write-Warn($Message) { Write-Host "⚠ $Message" -ForegroundColor Yellow }

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool uninstall deepagents-code
} else {
    Write-Warn "uv not found. If dcode was installed another way, remove it manually."
}

if ($RemoveData -eq "1") {
    Remove-Item -Recurse -Force "$env:LOCALAPPDATA\deepagents-code" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$env:APPDATA\deepagents-code" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$env:USERPROFILE\.deepagents" -ErrorAction SilentlyContinue
    Write-Success "Removed deepagents-code user data."
} else {
    Write-Warn "User data was kept. Set DCODE_REMOVE_DATA=1 to remove cached/config data."
}

Write-Success "dcode uninstalled."
