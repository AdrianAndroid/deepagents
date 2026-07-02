$ErrorActionPreference = "Stop"

$Version = if ($env:DCODE_VERSION) { $env:DCODE_VERSION } else { "0.1.24" }
$BaseUrl = if ($env:DCODE_BASE_URL) { $env:DCODE_BASE_URL } else { "http://8.152.204.58:40000/download/dcode/releases/$Version" }
$Wheel = "deepagents_code-$Version-py3-none-any.whl"
$Python = if ($env:DCODE_PYTHON) { $env:DCODE_PYTHON } else { "3.13" }
$SkipOptional = if ($env:DCODE_SKIP_OPTIONAL) { $env:DCODE_SKIP_OPTIONAL } else { "0" }

function Write-Info($Message) { Write-Host "▸ $Message" -ForegroundColor Cyan }
function Write-Success($Message) { Write-Host "✔ $Message" -ForegroundColor Green }
function Write-Warn($Message) { Write-Host "⚠ $Message" -ForegroundColor Yellow }

try {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Info "uv not found; installing uv..."
        irm https://astral.sh/uv/install.ps1 | iex
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    }

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv was installed but is not on PATH. Add $env:USERPROFILE\.local\bin to PATH and retry."
    }

    $TempDir = Join-Path ([System.IO.Path]::GetTempPath()) "dcode-install"
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null
    $WheelPath = Join-Path $TempDir $Wheel

    Write-Info "Downloading $Wheel from $BaseUrl..."
    Invoke-WebRequest "$BaseUrl/$Wheel" -OutFile $WheelPath

    Write-Info "Installing dcode $Version..."
    uv tool install -U --python $Python $WheelPath

    if ($SkipOptional -ne "1" -and -not (Get-Command rg -ErrorAction SilentlyContinue)) {
        Write-Warn "ripgrep (rg) not found; file search may be slower."
        Write-Warn "Install it with winget install BurntSushi.ripgrep.MSVC."
    }

    if (Get-Command dcode -ErrorAction SilentlyContinue) {
        dcode --version
    } elseif (Get-Command deepagents-code -ErrorAction SilentlyContinue) {
        deepagents-code --version
    } else {
        Write-Warn "dcode command is not on PATH yet. Restart PowerShell or add uv's bin directory to PATH."
    }

    Write-Success "dcode $Version installed successfully."
    Write-Host "Run: dcode"
} finally {
    if ($TempDir -and (Test-Path $TempDir)) {
        Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    }
}
