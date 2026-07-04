# Install deepagents-code (dcode) from the private PyPI server. (Windows PowerShell)
#
# Usage:
#   irm http://8.152.204.58:40080/install.ps1 | iex
#   # or download first:
#   powershell -ExecutionPolicy Bypass -File install.ps1
#
# Env overrides (set before running):
#   $env:PYPI_HOST     = "8.152.204.58:48080"
#   $env:PYPI_USER     = "admin"
#   $env:PYPI_PASSWORD = "admin"
#   $env:PKG_VERSION   = "0.0.2"   # empty = latest

$ErrorActionPreference = "Stop"

$PypiHost     = if ($env:PYPI_HOST)     { $env:PYPI_HOST }     else { "8.152.204.58:48080" }
$PypiUser     = if ($env:PYPI_USER)     { $env:PYPI_USER }     else { "admin" }
$PypiPassword = if ($env:PYPI_PASSWORD) { $env:PYPI_PASSWORD } else { "admin" }
$PkgName      = "deepagents-code"
$PkgVersion   = $env:PKG_VERSION
$ExtraIndex   = if ($env:EXTRA_INDEX_URL) { $env:EXTRA_INDEX_URL } else { "https://pypi.org/simple/" }

$IndexUrl = "http://${PypiUser}:${PypiPassword}@${PypiHost}/simple/"

function Info($msg)  { Write-Host "[install] $msg" -ForegroundColor Cyan }
function Warn($msg)  { Write-Host "[warn] $msg"    -ForegroundColor Yellow }
function Die($msg)   { Write-Host "[error] $msg"   -ForegroundColor Red; exit 1 }

# --- 1. ensure uv is installed --------------------------------------------
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Info "uv not found, installing via astral.sh installer..."
    try {
        powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    } catch {
        Die "failed to install uv: $_"
    }
    # uv installer adds itself to PATH for new shells; add for current session too.
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Die "uv installed but not on PATH; open a new PowerShell and re-run"
    }
}
Info ("uv: " + (uv --version))

# --- 2. install deepagents-code as a uv tool ------------------------------
$Spec = $PkgName
if ($PkgVersion) { $Spec = "$PkgName==$PkgVersion" }

Info "installing $Spec from $PypiHost"
uv tool install $Spec `
    --force `
    --index-url  $IndexUrl `
    --extra-index-url $ExtraIndex `
    --index-strategy unsafe-best-match

if ($LASTEXITCODE -ne 0) { Die "uv tool install failed" }

# --- 3. PATH check ---------------------------------------------------------
$UvBin = (uv tool dir --bin 2>$null)
if (-not $UvBin) { $UvBin = "$env:USERPROFILE\.local\bin" }
if (-not ($env:Path -split ';' | Where-Object { $_ -eq $UvBin })) {
    Warn "$UvBin is not in PATH. Add it permanently with:"
    Write-Host "  [Environment]::SetEnvironmentVariable('Path', `"$UvBin;`" + [Environment]::GetEnvironmentVariable('Path','User'), 'User')"
}

# --- 4. verify -------------------------------------------------------------
if (Get-Command dcode -ErrorAction SilentlyContinue) {
    Info ("installed: " + (Get-Command dcode).Source)
    Info "run: dcode"
} else {
    Warn "dcode not on PATH yet; open a new PowerShell or update PATH as shown above"
}

Info "done."
