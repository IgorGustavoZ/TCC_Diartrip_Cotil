# scripts/test_all.ps1
# Roda TODOS os testes com um comando.
# Uso:
#   .\scripts\test_all.ps1
#   .\scripts\test_all.ps1 -Integration
#   .\scripts\test_all.ps1 -Coverage

param(
    [switch]$Integration,
    [switch]$Coverage
)

$ErrorActionPreference = "Stop"
$ScriptsDir = $PSScriptRoot
$falhou = [System.Collections.Generic.List[string]]::new()

function Step($msg) {
    Write-Host ""
    Write-Host ("=" * 55) -ForegroundColor DarkGray
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host ("=" * 55) -ForegroundColor DarkGray
}

# Backend
Step "BACKEND -- pytest"
try {
    $bArgs = @()
    if ($Coverage) { $bArgs += "-Coverage" }
    & "$ScriptsDir\test_backend.ps1" @bArgs
    if ($LASTEXITCODE -ne 0) { $falhou.Add("Backend") }
} catch {
    Write-Host "Erro backend: $_" -ForegroundColor Red
    $falhou.Add("Backend")
}

# Flutter unit + widget
Step "FLUTTER -- unit + widget tests"
try {
    $fArgs = @()
    if ($Coverage) { $fArgs += "-Coverage" }
    & "$ScriptsDir\test_flutter.ps1" @fArgs
    if ($LASTEXITCODE -ne 0) { $falhou.Add("Flutter") }
} catch {
    Write-Host "Erro flutter: $_" -ForegroundColor Red
    $falhou.Add("Flutter")
}

# Integration (opcional)
if ($Integration) {
    Step "FLUTTER -- integration tests"
    try {
        & "$ScriptsDir\test_integration.ps1"
        if ($LASTEXITCODE -ne 0) { $falhou.Add("Integration") }
    } catch {
        Write-Host "Erro integration: $_" -ForegroundColor Red
        $falhou.Add("Integration")
    }
}

# Resumo
Write-Host ""
Write-Host ("=" * 55) -ForegroundColor DarkGray
Write-Host "  RESULTADO FINAL" -ForegroundColor White
Write-Host ("=" * 55) -ForegroundColor DarkGray

if ($falhou.Count -eq 0) {
    Write-Host ""
    Write-Host "  OK  Todos os testes passaram!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  FALHA: $($falhou -join ', ')" -ForegroundColor Red
    exit 1
}
