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

# --- 2. detect existing install and resolve target version ---------------
# IMPORTANT: we do NOT rely on uv's index-strategy to force the private
# source. The public PyPI ships an unrelated `deepagents-code` package at
# higher version numbers (0.1.x); left to its own devices uv will pick
# that one over our private 0.0.x builds.
#
# The only reliable fix is to pin an exact version that we KNOW only
# exists on the private PyPI. We do this by scraping the private simple
# index and picking the highest version found there, unless the user
# supplied $env:PKG_VERSION explicitly.

function Resolve-PrivateVersion {
    $indexUrl = "http://${PypiUser}:${PypiPassword}@${PypiHost}/simple/${PkgName}/"
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $indexUrl -ErrorAction Stop
        $html = $resp.Content
    } catch {
        return $null
    }
    # Filenames look like `deepagents_code-0.0.3-py3-none-any.whl`.
    $matches = [regex]::Matches($html, 'deepagents[_-]code-([0-9]+\.[0-9]+\.[0-9]+)')
    if ($matches.Count -eq 0) { return $null }
    $versions = @{}
    foreach ($m in $matches) { $versions[$m.Groups[1].Value] = $true }
    # Sort by [Version] so "0.0.10" > "0.0.2".
    $sorted = $versions.Keys | Sort-Object { [Version]$_ }
    return $sorted[-1]
}

if (-not $PkgVersion) {
    Info "resolving latest $PkgName version from private index $PypiHost..."
    $PkgVersion = Resolve-PrivateVersion
    if (-not $PkgVersion) {
        Die "cannot list $PkgName on private index $PypiHost; refusing to fall back to public PyPI (would install unrelated 0.1.x package)"
    }
    Info "resolved latest private version: $PkgVersion"
}

$Spec = "$PkgName==$PkgVersion"

# `uv tool list` prints entries like:  deepagents-code v0.0.5
$CurrentVer = $null
try {
    $listOutput = uv tool list 2>$null
    foreach ($line in $listOutput) {
        $parts = ($line -split '\s+', 2)
        if ($parts.Length -ge 2 -and $parts[0] -eq $PkgName) {
            $CurrentVer = $parts[1].Trim()
            break
        }
    }
} catch { }

if ($CurrentVer) {
    Info "detected $PkgName $CurrentVer; installing $Spec..."
} else {
    Info "installing $Spec from $PypiHost"
}

# We pass BOTH:
#   --index-url        : private PyPI (primary source of truth)
#   --extra-index-url  : public PyPI  (needed for transitive deps only)
#   --index-strategy unsafe-best-match
#
# Why unsafe-best-match here is actually SAFE:
#
#   uv's default strategy is "first-index": once it finds `deepagents-code`
#   in ANY index (including --extra-index-url), it locks onto that index
#   and refuses to look at others. Since public PyPI ALSO publishes a
#   package literally named `deepagents-code` (langchain-ai upstream,
#   currently 0.1.x), uv gets locked onto the public one and never checks
#   our private index. Even a pinned `==0.0.3` then fails with:
#     "there is no version of deepagents-code==0.0.3"
#   because uv only searched public PyPI, which has no 0.0.3.
#
#   The fix: combine unsafe-best-match (search all indexes) with an EXACT
#   version pin that only exists on the private index. Public PyPI has
#   no 0.0.x publish, so `==<private-version>` cannot resolve to the
#   public copy. The pin, not the strategy, is what enforces safety.
uv tool install $Spec `
    --force `
    --index-url  $IndexUrl `
    --extra-index-url $ExtraIndex `
    --index-strategy unsafe-best-match `
    --prerelease=allow

if ($LASTEXITCODE -ne 0) { Die "uv tool install failed" }

$NewVer = $null
try {
    $listOutput = uv tool list 2>$null
    foreach ($line in $listOutput) {
        $parts = ($line -split '\s+', 2)
        if ($parts.Length -ge 2 -and $parts[0] -eq $PkgName) {
            $NewVer = $parts[1].Trim()
            break
        }
    }
} catch { }

# Safety check: private-source versions are always 0.0.x. If uv reported
# a higher version, the private-source guarantee failed; bail out loudly.
if ($NewVer) {
    $verNum = $NewVer.TrimStart('v')
    if ($verNum -notmatch '^0\.0\.') {
        Die "installed $PkgName $NewVer, but expected a 0.0.x private-source build. Something pulled from public PyPI. Aborting."
    }
}

if ($CurrentVer -and $NewVer) {
    if ($CurrentVer -eq $NewVer) {
        Info "$PkgName already at $NewVer (no change)"
    } else {
        Info "$PkgName upgraded: $CurrentVer -> $NewVer"
    }
} elseif ($NewVer) {
    Info "$PkgName installed: $NewVer"
}

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
