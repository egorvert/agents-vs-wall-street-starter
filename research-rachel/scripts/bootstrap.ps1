$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".venv/Scripts/python.exe" -m pip install --upgrade pip
& ".venv/Scripts/python.exe" -m pip install -e ".\apps\api[dev]"
npm install

Write-Host "Setup complete. Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "Then run both apps with: npm run dev"
