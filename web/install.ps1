# Install zjcode from the private PyPI server. (Windows PowerShell)
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
#   $env:PYTHON_VERSION    = "3.11"     # zjcode requires >=3.11,<4.0

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
$PkgName      = "zjcode"
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
# `zjcode` requires Python >=3.11,<4.0 (see libs/code/pyproject.toml).
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

    # Verify version satisfies zjcode's requires-python (>=3.11,<4.0).
    $verOutput = (& $envPython -c "import sys;print('{}.{}'.format(sys.version_info[0], sys.version_info[1]))").Trim()
    Info "conda env '$CondaEnvName' python: $verOutput ($envPython)"
    $verParts = $verOutput.Split('.')
    if ([int]$verParts[0] -lt 3 -or ([int]$verParts[0] -eq 3 -and [int]$verParts[1] -lt 11)) {
        Warn "conda env '$CondaEnvName' has python $verOutput; zjcode requires >=3.11"
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
# `zjcode` 目前只在私有源发布，公共 PyPI 上没有同名包 —— 但如果哪天有人在
# 公共 PyPI 抢注 `zjcode`，"锁死到本地存在的确切版本"仍然是唯一可靠护栏。

function Resolve-PrivateVersion {
    $indexUrl = "http://${PypiUser}:${PypiPassword}@${PypiHost}/simple/${PkgName}/"
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri $indexUrl -ErrorAction Stop
        $html = $resp.Content
    } catch {
        return $null
    }
    # Filenames look like `zjcode-0.0.1-py3-none-any.whl`.
    $matches = [regex]::Matches($html, 'zjcode-([0-9]+\.[0-9]+\.[0-9]+)')
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
        Die "cannot list $PkgName on private index $PypiHost; refusing to fall back to public PyPI"
    }
    Info "resolved latest private version: $PkgVersion"
}

$Spec = "$PkgName==$PkgVersion"

# `uv tool list` prints entries like:  zjcode v0.0.1
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
# `zjcode` 只有私有源有，公共 PyPI 目前没有同名包，因此这里的策略主要是
# 为了让公共 PyPI 能解出依赖树里的其它包，而私有源自己解出 `zjcode` 本体。
# 保留 exact pin，作为将来公共 PyPI 若被抢注时的护栏。
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

# Refresh the current session first so we can verify `zjcode` below.
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
if (Get-Command zjcode -ErrorAction SilentlyContinue) {
    Info ("installed: " + (Get-Command zjcode).Source)
    Info "run: zjcode"
} else {
    Warn "zjcode not on PATH yet; open a new PowerShell or update PATH as shown above"
}

Info "done."
