# Uninstall zjcode - broad-spectrum cleanup, plus legacy deepagents-code shim removal. (Windows PowerShell)
#
# Removes zjcode no matter how it was installed:
#   - uv tool install    (our recommended path)
#   - pipx install
#   - pip install / pip install --user
#   - stray shims in %USERPROFILE%\.local\bin and Python Scripts dirs
# Also cleans up leftover shims from the pre-rebrand `deepagents-code` / `dcode` install.
#
# Usage:
#   irm http://8.152.204.58:40080/uninstall.ps1 | iex
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1
#   # dry-run:
#   $env:DRY_RUN = "1"; powershell -ExecutionPolicy Bypass -File uninstall.ps1

$ErrorActionPreference = "Continue"
$PkgName    = "zjcode"
$LegacyPkgs = @("deepagents-code")
$AllPkgs    = @($PkgName) + $LegacyPkgs
$BinNames   = @(
    "zjcode.exe", "zjcode",
    "dcode.exe", "dcode",
    "deepagents-code.exe", "deepagents-code",
    "deepagents.exe", "deepagents"
)
$DryRun     = ($env:DRY_RUN -eq "1")
$changed    = $false

function Info($msg) { Write-Host "[uninstall] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[warn] $msg"      -ForegroundColor Yellow }
function Dry($msg)  { Write-Host "[dry-run] $msg"   -ForegroundColor Magenta }

function Invoke-Step {
    param([string]$Label, [scriptblock]$Action)
    if ($DryRun) { Dry $Label; return $true }
    Info "> $Label"
    & $Action
    return ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null)
}

# --- 1. uv tool ------------------------------------------------------------
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uvList = (uv tool list 2>$null) | Out-String
    foreach ($pkg in $AllPkgs) {
        if ($uvList -match "(?m)^$pkg\b") {
            Info "found via 'uv tool'; uninstalling $pkg..."
            if (Invoke-Step "uv tool uninstall $pkg" { uv tool uninstall $pkg }) {
                $changed = $true
            }
        } else {
            Info "'uv tool' has no $pkg"
        }
    }
} else {
    Info "uv not installed; skipping uv tool"
}

# --- 2. pipx ---------------------------------------------------------------
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    $pipxList = (pipx list --short 2>$null) | Out-String
    foreach ($pkg in $AllPkgs) {
        if ($pipxList -match "(?m)^$pkg\b") {
            Info "found via 'pipx'; uninstalling $pkg..."
            if (Invoke-Step "pipx uninstall $pkg" { pipx uninstall $pkg }) {
                $changed = $true
            }
        } else {
            Info "'pipx' has no $pkg"
        }
    }
}

# --- 3. pip (every python on PATH) -----------------------------------------
$pythons = @()
foreach ($py in @("python", "python3", "py")) {
    $cmd = Get-Command $py -ErrorAction SilentlyContinue
    if ($cmd -and ($pythons -notcontains $cmd.Source)) {
        $pythons += $cmd.Source
    }
}
foreach ($py in $pythons) {
    foreach ($pkg in $AllPkgs) {
        $showOut = & $py -m pip show $pkg 2>$null
        if ($LASTEXITCODE -eq 0 -and $showOut) {
            Info "found via '$py -m pip'; uninstalling $pkg..."
            if (Invoke-Step "$py -m pip uninstall -y $pkg" { & $py -m pip uninstall -y $pkg }) {
                $changed = $true
            }
        }
    }
}

# --- 4. clean stray shims --------------------------------------------------
$shimDirs = @(
    "$env:USERPROFILE\.local\bin",
    "$env:LOCALAPPDATA\Programs\Python\Scripts",
    "$env:APPDATA\Python\Scripts"
)
# also every Scripts folder next to detected pythons
foreach ($py in $pythons) {
    $scriptsDir = Join-Path (Split-Path $py -Parent) "Scripts"
    if ((Test-Path $scriptsDir) -and ($shimDirs -notcontains $scriptsDir)) {
        $shimDirs += $scriptsDir
    }
}

foreach ($dir in $shimDirs) {
    if (-not (Test-Path $dir)) { continue }
    foreach ($name in $BinNames) {
        $path = Join-Path $dir $name
        if (Test-Path $path) {
            # heuristic: only kill the shim if it references our package
            $head = ""
            try {
                $bytes = [System.IO.File]::ReadAllBytes($path)
                $take = [Math]::Min(2048, $bytes.Length)
                $head = [System.Text.Encoding]::UTF8.GetString($bytes, 0, $take)
            } catch { }
            if ($head -match "$PkgName|deepagents-code|deepagents_code|site-packages" -or $path -like "*.exe") {
                Info "removing shim: $path"
                if (Invoke-Step "Remove-Item $path" { Remove-Item -Force $path }) {
                    $changed = $true
                }
            }
        }
    }
}

# --- 5. summary + residual check ------------------------------------------
if (-not $changed) {
    Warn "no $PkgName (or legacy deepagents-code) installation was detected"
}

Info "post-cleanup check:"
$foundAny = $false
foreach ($name in $BinNames) {
    $c = Get-Command $name -ErrorAction SilentlyContinue
    if ($c) {
        Warn "  $name still resolves to: $($c.Source)"
        $foundAny = $true
    }
}
if (-not $foundAny) { Info "  no zjcode/dcode/deepagents-code binary remains on PATH" }

Info "done."
