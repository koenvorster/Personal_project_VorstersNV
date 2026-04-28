#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start het volledige VorstersNV platform lokaal.

.DESCRIPTION
    1. Controleert WSL + Docker (PostgreSQL, Redis)
    2. Start ontbrekende containers op via WSL
    3. Start FastAPI backend op poort 8000
    4. Start Next.js frontend op poort 3001 (poort 3000 = Grafana)

.NOTES
    Vereisten: WSL2 met Ubuntu + Docker, Node.js 18+, Python 3.12+
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

function Write-Step { param($msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "    ✓ $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "    ⚠ $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "    ✗ $msg" -ForegroundColor Red }

# ─── 1. WSL + Docker check ───────────────────────────────────────────────────
Write-Step "WSL en Docker controleren..."

$wslCheck = wsl --status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "WSL2 is niet beschikbaar. Installeer via: wsl --install"
    exit 1
}
Write-Ok "WSL2 actief"

$dockerCheck = wsl bash -c "docker info --format '{{.ServerVersion}}' 2>/dev/null"
if (-not $dockerCheck) {
    Write-Fail "Docker niet beschikbaar in WSL. Start Docker daemon: wsl -e sudo service docker start"
    exit 1
}
Write-Ok "Docker $dockerCheck in WSL"

# ─── 2. PostgreSQL container ─────────────────────────────────────────────────
Write-Step "PostgreSQL controleren..."

$dbStatus = wsl bash -c "docker inspect --format '{{.State.Status}}' vorstersNV-db 2>/dev/null"
if ($dbStatus -eq "running") {
    Write-Ok "vorstersNV-db draait al"
} else {
    Write-Warn "vorstersNV-db niet actief — starten via docker compose..."
    wsl bash -c "cd /mnt/c/Users/kvo/IdeaProjects/VorstersNV && docker compose up -d database"
    Start-Sleep -Seconds 5
    Write-Ok "PostgreSQL gestart"
}

# ─── 3. Redis container ──────────────────────────────────────────────────────
Write-Step "Redis controleren..."

$redisStatus = wsl bash -c "docker inspect --format '{{.State.Status}}' vorstersNV-redis 2>/dev/null"
if ($redisStatus -eq "running") {
    Write-Ok "vorstersNV-redis draait al"
} else {
    Write-Warn "vorstersNV-redis niet actief — starten..."
    wsl bash -c "cd /mnt/c/Users/kvo/IdeaProjects/VorstersNV && docker compose up -d redis"
    Start-Sleep -Seconds 3
    Write-Ok "Redis gestart"
}

# ─── 4. Port conflict check ──────────────────────────────────────────────────
Write-Step "Poorten controleren..."

$port8000 = netstat -ano | Select-String ":8000 " | Select-String "LISTENING"
if ($port8000) {
    $pid8000 = ($port8000 -split "\s+")[-1]
    $proc = Get-Process -Id $pid8000 -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -ne "python") {
        Write-Warn "Poort 8000 in gebruik door $($proc.ProcessName) (PID $pid8000) — overgeslagen"
    }
}

$port3001 = netstat -ano | Select-String ":3001 " | Select-String "LISTENING"
if ($port3001) {
    $pid3001 = ($port3001 -split "\s+")[-1]
    $proc = Get-Process -Id $pid3001 -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Warn "Poort 3001 in gebruik door $($proc.ProcessName) (PID $pid3001) — stoppen..."
        Stop-Process -Id $pid3001 -Force
        Start-Sleep -Seconds 1
    }
}

Write-Ok "Poorten vrij"

# ─── 5. FastAPI backend ──────────────────────────────────────────────────────
Write-Step "FastAPI starten op http://localhost:8000 ..."

Set-Location $ProjectRoot
$fastapiJob = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "api.main:app", "--reload", "--port", "8000" `
    -WorkingDirectory $ProjectRoot `
    -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 4

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    Write-Ok "FastAPI gezond (uptime: $($health.uptime_seconds)s)"
} catch {
    Write-Warn "FastAPI health check mislukt — controleer het venster"
}

# ─── 6. Next.js frontend ─────────────────────────────────────────────────────
Write-Step "Next.js starten op http://localhost:3001 ..."

Set-Location "$ProjectRoot\frontend"
$nextJob = Start-Process -FilePath "npm" `
    -ArgumentList "run", "dev", "--", "-p", "3001" `
    -WorkingDirectory "$ProjectRoot\frontend" `
    -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 6

# ─── 7. Samenvatting ─────────────────────────────────────────────────────────
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "  VorstersNV Platform — Lokale omgeving actief" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  🌐  Portfolio / Frontend   http://localhost:3001" -ForegroundColor Green
Write-Host "  🚀  FastAPI Backend        http://localhost:8000" -ForegroundColor Green
Write-Host "  📖  API Docs (Swagger)     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  🗄️   PostgreSQL             localhost:5432" -ForegroundColor DarkGray
Write-Host "  🔴  Redis                  localhost:6379" -ForegroundColor DarkGray
Write-Host "  📊  Grafana                http://localhost:3000  (WSL Docker)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Stop met: Stop-Process -Id $($fastapiJob.Id),$($nextJob.Id)" -ForegroundColor DarkGray
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

Set-Location $ProjectRoot
