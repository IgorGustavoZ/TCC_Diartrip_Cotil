# scripts/test_flutter.ps1
# Roda unit + widget tests do Flutter.
# Uso:
#   .\scripts\test_flutter.ps1
#   .\scripts\test_flutter.ps1 -Coverage
#   .\scripts\test_flutter.ps1 -Chrome

param(
    [switch]$Coverage,
    [switch]$Chrome
)

$ErrorActionPreference = "Stop"
$FlutterDir = Join-Path $PSScriptRoot "..\diartrip_flutter"

Write-Host ""
Write-Host "=== Diartrip -- Flutter Tests ===" -ForegroundColor Cyan
Set-Location $FlutterDir

Write-Host "flutter pub get..." -ForegroundColor Yellow
flutter pub get | Out-Null

Write-Host "Gerando mocks (build_runner)..." -ForegroundColor Yellow
dart run build_runner build --delete-conflicting-outputs 2>&1 | Out-Null

$flutter_args = [System.Collections.Generic.List[string]]::new()
$flutter_args.Add("test")
$flutter_args.Add("test/")

if ($Chrome) {
    $flutter_args.Add("--platform")
    $flutter_args.Add("chrome")
    Write-Host "Plataforma: Chrome" -ForegroundColor Yellow
}

if ($Coverage) {
    $flutter_args.Add("--coverage")
    Write-Host "Cobertura habilitada -> diartrip_flutter/coverage/lcov.info" -ForegroundColor Yellow
}

flutter @flutter_args

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "OK  Todos os testes Flutter passaram!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "FALHA  Testes Flutter falharam." -ForegroundColor Red
    exit 1
}
