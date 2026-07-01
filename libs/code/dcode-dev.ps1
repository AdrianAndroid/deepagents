$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = if ($env:DCODE_DEV_VENV) { $env:DCODE_DEV_VENV } else { Join-Path $env:LOCALAPPDATA "dcode-dev" }
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Dcode = Join-Path $VenvDir "Scripts\dcode.exe"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

if (-not (Test-Path $Python)) {
    uv venv $VenvDir
}

uv pip install --python $Python -e $ScriptDir --upgrade
& $Dcode @args
exit $LASTEXITCODE
