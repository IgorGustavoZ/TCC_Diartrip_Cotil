# scripts/test_integration.ps1
# Sobe o backend automaticamente, cria o usuario de teste e roda
# os integration tests do Flutter. Tudo com um comando.
# Uso:
#   .\scripts\test_integration.ps1
#   .\scripts\test_integration.ps1 -Chrome
#   .\scripts\test_integration.ps1 -Device windows

param(
    [switch]$Chrome,
    [string]$Device = ""
)

$ErrorActionPreference = "Stop"
$RootDir    = Join-Path $PSScriptRoot ".."
$BackendDir = Join-Path $RootDir "backend"
$FlutterDir = Join-Path $RootDir "diartrip_flutter"

Write-Host ""
Write-Host "=== Diartrip -- Integration Tests ===" -ForegroundColor Cyan

# 1. Verifica se backend ja esta rodando
$backendJaRodando = $false
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" `
        -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($resp.StatusCode -eq 200) { $backendJaRodando = $true }
} catch {}

$backendProcess = $null

if ($backendJaRodando) {
    Write-Host "OK  Backend ja esta rodando em http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "Subindo backend FastAPI..." -ForegroundColor Yellow
    $backendProcess = Start-Process -FilePath "python" `
        -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000" `
        -WorkingDirectory $BackendDir `
        -PassThru -WindowStyle Hidden

    # Aguarda ate 20s
    $tentativas = 0
    $pronto = $false
    while ($tentativas -lt 20 -and -not $pronto) {
        Start-Sleep -Seconds 1
        $tentativas++
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" `
                -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($r.StatusCode -eq 200) { $pronto = $true }
        } catch {}
    }

    if (-not $pronto) {
        Write-Host "FALHA  Backend nao respondeu em 20 segundos." -ForegroundColor Red
        if ($null -ne $backendProcess) {
            Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        }
        exit 1
    }
    Write-Host "OK  Backend pronto!" -ForegroundColor Green
}

# 2. Cria usuario de teste (o setUpAll do app_test.dart tambem faz isso,
#    mas garantimos aqui para evitar race condition)
Write-Host "Garantindo usuario de teste..." -ForegroundColor Yellow
try {
    $body    = '{"nome":"Integration Tester","email":"integration@diartrip.test","senha":"Teste1234"}'
    $headers = @{ "Content-Type" = "application/json" }
    Invoke-RestMethod -Uri "http://127.0.0.1:8000/usuarios" `
        -Method POST -Body $body -Headers $headers -ErrorAction SilentlyContinue | Out-Null
    Write-Host "  Usuario criado." -ForegroundColor Green
} catch {
    Write-Host "  Usuario ja existe (ok, continuando)." -ForegroundColor Yellow
}

# 3. Roda integration tests
Set-Location $FlutterDir
flutter pub get | Out-Null

$flutter_args = [System.Collections.Generic.List[string]]::new()
$flutter_args.Add("test")
$flutter_args.Add("integration_test/app_test.dart")

if ($Chrome) {
    $flutter_args.Add("--platform")
    $flutter_args.Add("chrome")
    Write-Host "Plataforma: Chrome" -ForegroundColor Yellow
} elseif ($Device) {
    $flutter_args.Add("-d")
    $flutter_args.Add($Device)
    Write-Host "Dispositivo: $Device" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Rodando integration tests..." -ForegroundColor Cyan
flutter @flutter_args
$exitCode = $LASTEXITCODE

# 4. Para o backend se foi iniciado por este script
if ($null -ne $backendProcess) {
    Write-Host ""
    Write-Host "Parando backend..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
}

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "OK  Integration tests passaram!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "FALHA  Integration tests falharam." -ForegroundColor Red
    exit 1
}
