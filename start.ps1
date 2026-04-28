# Chord Progression Recommender — One-Click Launcher
# Usage: powershell -ExecutionPolicy Bypass -File start.ps1

$ErrorActionPreference = "Continue"
$root = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Chord Progression Recommender" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ---- Check data files ----
$styleIndex = "$root\backend\data\style_index.json"

if (-not (Test-Path $styleIndex)) {
    Write-Host "[X] Data not found: style_index.json" -ForegroundColor Red
    Write-Host "    Run these commands first:" -ForegroundColor Yellow
    Write-Host "      cd backend" -ForegroundColor Yellow
    Write-Host "      .\.venv\Scripts\python.exe scripts\download_data.py" -ForegroundColor Yellow
    Write-Host "      .\.venv\Scripts\python.exe scripts\build_matrices.py" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# ---- Utility functions ----
function Test-PortInUse($port) {
    $result = netstat -ano 2>$null | Select-String ":$port "
    return ($null -ne $result)
}

function Find-FreePort($startPort) {
    $port = $startPort
    while (Test-PortInUse $port) {
        Write-Host "      Port $port in use, trying $($port + 1)..." -ForegroundColor Yellow
        $port++
        if ($port -gt $startPort + 100) {
            Write-Host "[X] No free port found in range $startPort-$($startPort + 100)" -ForegroundColor Red
            throw "No free ports in range"
        }
    }
    return $port
}

# ---- Allocate ports ----
$backendPort  = Find-FreePort 8000
$frontendPort = Find-FreePort 5173

if ($backendPort -ne 8000) {
    Write-Host "      Backend will use port: $backendPort" -ForegroundColor Yellow
}
if ($frontendPort -ne 5173) {
    Write-Host "      Frontend will use port: $frontendPort" -ForegroundColor Yellow
}

# ---- Start backend ----
Write-Host "[1/2] Starting backend (http://localhost:$backendPort)..." -ForegroundColor Green
$python = "$root\backend\.venv\Scripts\python.exe"

$backendProc = Start-Process `
    -FilePath $python `
    -ArgumentList "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "$backendPort" `
    -WorkingDirectory "$root\backend" `
    -WindowStyle Minimized `
    -PassThru

# Wait for backend to be ready
Write-Host "      Waiting for backend..." -NoNewline
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $checkUrl = "http://127.0.0.1:$backendPort/api/v1/styles"
        $null = Invoke-WebRequest -Uri $checkUrl -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        Write-Host " ready!" -ForegroundColor Green
        $ready = $true
        break
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
}

if (-not $ready) {
    Write-Host ""
    Write-Host "[X] Backend failed to start within 30s." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# ---- Start frontend ----
Write-Host "[2/2] Starting frontend (http://localhost:$frontendPort)..." -ForegroundColor Green
$frontendProc = Start-Process `
    -FilePath "cmd" `
    -ArgumentList "/c", "cd /d `"$root\frontend`" && npx vite --host 127.0.0.1 --port $frontendPort" `
    -WindowStyle Minimized `
    -PassThru

Start-Sleep -Seconds 2
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Backend  : http://localhost:$backendPort/docs" -ForegroundColor White
Write-Host "  Frontend : http://localhost:$frontendPort" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press any key to stop all services..." -ForegroundColor Gray

# Open browser
Start-Process "http://localhost:$frontendPort"

# Wait for user input
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# ---- Cleanup ----
Write-Host ""
Write-Host "Stopping services..." -ForegroundColor Yellow
if ($backendProc)  { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
if ($frontendProc) { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue }
Write-Host "Done." -ForegroundColor Green
