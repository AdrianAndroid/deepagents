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
#   $env:PKG_VERSION       = "0.0.2"   # empty = latest
#   $env:MINICONDA_URL     = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
#   $env:MINICONDA_PREFIX  = "$env:USERPROFILE\Miniconda3"
#   $env:CONDA_ENV_NAME    = "deepagents"
#   $env:PYTHON_VERSION    = "3.11"     # deepagents-code requires >=3.11,<4.0

$ErrorActionPreference = "Stop"

# Windows PowerShell 5.1 defaults to TLS 1.0/1.1 for outbound HTTPS, which
# routinely fails against modern hosts (repo.anaconda.com, astral.sh,
# github.com). Force TLS 1.2 for this session BEFORE any web request.
try {
    [Net.ServicePointManager]::SecurityProtocol = `
        [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

# Invoke-WebRequest with the progress bar in PS 5.1 is ~10x slower on
# large downloads (Miniconda is ~90MB). Silencing progress avoids the
# "hangs forever" perception during bootstrap.
$ProgressPreference = 'SilentlyContinue'

$PypiHost     = if ($env:PYPI_HOST)     { $env:PYPI_HOST }     else { "8.152.204.58:48080" }
$PypiUser     = if ($env:PYPI_USER)     { $env:PYPI_USER }     else { "admin" }
$PypiPassword = if ($env:PYPI_PASSWORD) { $env:PYPI_PASSWORD } else { "admin" }
$PkgName      = "deepagents-code"
$PkgVersion   = $env:PKG_VERSION
$ExtraIndex   = if ($env:EXTRA_INDEX_URL) { $env:EXTRA_INDEX_URL } else { "https://pypi.org/simple/" }

# Conda / Python bootstrap knobs
$MinicondaUrl     = if ($env:MINICONDA_URL)     { $env:MINICONDA_URL }     else { "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe" }
$MinicondaPrefix  = if ($env:MINICONDA_PREFIX)  { $env:MINICONDA_PREFIX }  else { "$env:USERPROFILE\Miniconda3" }
$CondaEnvName     = if ($env:CONDA_ENV_NAME)    { $env:CONDA_ENV_NAME }    else { "deepagents" }
$RequiredPyVer    = if ($env:PYTHON_VERSION)    { $env:PYTHON_VERSION }    else { "3.11" }

$IndexUrl = "http://${PypiUser}:${PypiPassword}@${PypiHost}/simple/"

function Info($msg)  { Write-Host "[install] $msg" -ForegroundColor Cyan }
function Warn($msg)  { Write-Host "[warn] $msg"    -ForegroundColor Yellow }
function Die($msg)   { Write-Host "[error] $msg"   -ForegroundColor Red; exit 1 }

# --- 0. ensure conda + a Python >=3.11 environment ------------------------
# `deepagents-code` requires Python >=3.11,<4.0 (see libs/code/pyproject.toml).
# On Windows we prefer to source that interpreter from conda:
#   - if `conda` is missing, silently install Miniconda3 to $MinicondaPrefix
#   - ensure a conda env named $CondaEnvName exists with python=$RequiredPyVer
#   - hand that env's python.exe to `uv tool install --python` below
# uv itself can also download a managed CPython, but conda is friendlier for
# users who already manage envs that way, and matches the ask to auto-install
# Miniconda when it's absent.

function Add-CondaToPath($prefix) {
    $paths = @($prefix, "$prefix\Scripts", "$prefix\Library\bin", "$prefix\condabin")
    foreach ($p in $paths) {
        if ((Test-Path $p) -and (-not ($env:Path -split ';' | Where-Object { $_ -eq $p }))) {
            $env:Path = "$p;$env:Path"
        }
    }
}

function Get-CondaExe {
    $cmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    if (Test-Path "$MinicondaPrefix\Scripts\conda.exe") { return "$MinicondaPrefix\Scripts\conda.exe" }
    return $null
}

function Install-Miniconda {
    Info "conda not found; downloading Miniconda installer..."
    $installer = Join-Path $env:TEMP "Miniconda3-latest-Windows-x86_64.exe"
    try {
        Invoke-WebRequest -UseBasicParsing -Uri $MinicondaUrl -OutFile $installer
    } catch {
        Die "failed to download Miniconda from ${MinicondaUrl}: $_"
    }
    Info "installing Miniconda silently to $MinicondaPrefix ..."
    # /InstallationType=JustMe /S = silent, per-user; /D must be LAST and
    # unquoted per the Miniconda docs — pass everything as one string so
    # PowerShell doesn't auto-quote a path containing spaces.
    $installArgs = "/InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D=$MinicondaPrefix"
    $proc = Start-Process -FilePath $installer -ArgumentList $installArgs -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Die "Miniconda installer exited with code $($proc.ExitCode)"
    }
    Remove-Item $installer -ErrorAction SilentlyContinue
    Add-CondaToPath $MinicondaPrefix
    if (-not (Get-CondaExe)) {
        Die "Miniconda installed to $MinicondaPrefix but conda.exe not found"
    }
    Info "Miniconda installed."
}

function Ensure-CondaPython {
    $conda = Get-CondaExe
    if (-not $conda) {
        Install-Miniconda
        $conda = Get-CondaExe
    } else {
        # conda already on PATH (or resolvable); make sure our session sees it fully.
        $prefix = Split-Path (Split-Path $conda -Parent) -Parent
        Add-CondaToPath $prefix
    }
    Info ("conda: " + (& $conda --version))

    # Check whether the target env already exists and its python satisfies >=3.11.
    $envPython = "$MinicondaPrefix\envs\$CondaEnvName\python.exe"
    # If conda lives elsewhere (user's pre-existing conda), derive env path from `conda info`.
    if (-not (Test-Path $envPython)) {
        try {
            $envsJson = & $conda env list --json 2>$null | Out-String
            $envs = ($envsJson | ConvertFrom-Json).envs
            foreach ($p in $envs) {
                if ((Split-Path $p -Leaf) -eq $CondaEnvName) {
                    $envPython = Join-Path $p "python.exe"
                    break
                }
            }
        } catch { }
    }

    if (-not (Test-Path $envPython)) {
        Info "creating conda env '$CondaEnvName' with python=$RequiredPyVer ..."
        # --yes + --force: overwrite a broken/half-created env in place.
        & $conda create -y --force -n $CondaEnvName "python=$RequiredPyVer" | Out-Null
        if ($LASTEXITCODE -ne 0) { Die "conda create failed" }
        # Re-resolve env path.
        $envsJson = & $conda env list --json 2>$null | Out-String
        $envs = ($envsJson | ConvertFrom-Json).envs
        foreach ($p in $envs) {
            if ((Split-Path $p -Leaf) -eq $CondaEnvName) {
                $envPython = Join-Path $p "python.exe"
                break
            }
        }
    }

    if (-not (Test-Path $envPython)) {
        Die "cannot locate python.exe for conda env '$CondaEnvName'"
    }

    # Verify version satisfies deepagents-code's requires-python (>=3.11,<4.0).
    $verOutput = (& $envPython -c "import sys;print('{}.{}'.format(sys.version_info[0], sys.version_info[1]))").Trim()
    Info "conda env '$CondaEnvName' python: $verOutput ($envPython)"
    $verParts = $verOutput.Split('.')
    if ([int]$verParts[0] -lt 3 -or ([int]$verParts[0] -eq 3 -and [int]$verParts[1] -lt 11)) {
        Warn "conda env '$CondaEnvName' has python $verOutput; deepagents-code requires >=3.11"
        Info "upgrading env python to $RequiredPyVer ..."
        & $conda install -y -n $CondaEnvName "python=$RequiredPyVer" | Out-Null
        if ($LASTEXITCODE -ne 0) { Die "conda install python=$RequiredPyVer failed" }
    }
    return $envPython
}

$CondaPython = Ensure-CondaPython

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
    --python  $CondaPython `
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

# --- 3. PATH: ensure uv's tool-bin dir is on the user's permanent PATH ----
$UvBin = (uv tool dir --bin 2>$null)
if (-not $UvBin) { $UvBin = "$env:USERPROFILE\.local\bin" }

# Refresh the current session first so we can verify `dcode` below.
if (-not ($env:Path -split ';' | Where-Object { $_ -eq $UvBin })) {
    $env:Path = "$UvBin;$env:Path"
}

# Persist for future sessions by updating the User PATH (never Machine PATH,
# so we don't need admin and don't touch system-wide state).
try {
    $userPath = [Environment]::GetEnvironmentVariable('Path','User')
    if (-not $userPath) { $userPath = "" }
    $userSegs = $userPath -split ';' | Where-Object { $_ -ne "" }
    if ($userSegs -notcontains $UvBin) {
        $newUserPath = if ($userPath) { "$UvBin;$userPath" } else { $UvBin }
        [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
        Info "added $UvBin to your user PATH (new shells will pick it up)"
    }
} catch {
    Warn "could not persist PATH update ($_). Add $UvBin to PATH manually."
}

# --- 4. verify -------------------------------------------------------------
if (Get-Command dcode -ErrorAction SilentlyContinue) {
    Info ("installed: " + (Get-Command dcode).Source)
    Info "run: dcode"
} else {
    Warn "dcode not on PATH yet; open a new PowerShell or update PATH as shown above"
}

Info "done."
