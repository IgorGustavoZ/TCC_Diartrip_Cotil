# scripts/test_backend.ps1
# Roda toda a suite do backend com um comando.
# Uso:
#   .\scripts\test_backend.ps1
#   .\scripts\test_backend.ps1 -Coverage
#   .\scripts\test_backend.ps1 -Filter "auth"

param(
    [switch]$Coverage,
    [string]$Filter = ""
)

$ErrorActionPreference = "Stop"
$BackendDir = Join-Path $PSScriptRoot "..\backend"

Write-Host ""
Write-Host "=== Diartrip -- Backend Tests ===" -ForegroundColor Cyan
Set-Location $BackendDir

# Verifica se pytest esta instalado
$pytestOk = $true
try { python -c "import pytest" 2>$null } catch { $pytestOk = $false }
if (-not $pytestOk) {
    Write-Host "Instalando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt | Out-Null
}

# Monta lista de argumentos
$pytest_args = [System.Collections.Generic.List[string]]::new()

if ($Filter) {
    $pytest_args.Add("-k")
    $pytest_args.Add($Filter)
}

if ($Coverage) {
    pip install pytest-cov 2>$null | Out-Null
    $pytest_args.Add("--cov=.")
    $pytest_args.Add("--cov-omit=tests/*,conftest.py")
    $pytest_args.Add("--cov-report=html:htmlcov")
    $pytest_args.Add("--cov-report=term-missing")
    Write-Host "Cobertura habilitada -> backend/htmlcov/index.html" -ForegroundColor Yellow
}

# Roda os testes
pytest @pytest_args

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK  Todos os testes passaram!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "FALHA  Testes falharam." -ForegroundColor Red
    exit 1
}
