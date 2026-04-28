# ============================================================================
# START_PHASE_1.ps1
# VorstersNV Cloud Platform 2.0 - Phase 1 Startup Script
# ============================================================================

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     VorstersNV Cloud Platform 2.0 - Phase 1 Execution        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$projectPath = "c:\Users\janss\IdeaProjects\Nieuwe map\Personal_project_VorstersNV"
Set-Location $projectPath

# ============================================================================
# STEP 1: Ensure Docker is running
# ============================================================================
Write-Host "📦 Step 1: Ensuring Docker Desktop is running..." -ForegroundColor Yellow

$maxRetries = 30
$retryCount = 0
$dockerReady = $false

while ($retryCount -lt $maxRetries) {
    try {
        $output = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker is ready!" -ForegroundColor Green
            $dockerReady = $true
            break
        }
    }
    catch {
        # Docker not ready yet
    }
    
    $retryCount++
    Write-Host "   Waiting for Docker... ($retryCount/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $dockerReady) {
    Write-Host "❌ Docker Desktop failed to start. Please start it manually." -ForegroundColor Red
    Write-Host "   → Run: C:\Program Files\Docker\Docker\Docker.exe" -ForegroundColor Yellow
    Exit 1
}

# ============================================================================
# STEP 2: Start Docker Compose services
# ============================================================================
Write-Host "`n🚀 Step 2: Starting Docker Compose services..." -ForegroundColor Yellow
Write-Host "   Services to start:" -ForegroundColor Cyan
Write-Host "   • ollama (AI engine)" -ForegroundColor Gray
Write-Host "   • postgresql (database)" -ForegroundColor Gray
Write-Host "   • redis (cache)" -ForegroundColor Gray
Write-Host "   • webhooks (FastAPI)" -ForegroundColor Gray

docker compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Services started successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start Docker Compose services" -ForegroundColor Red
    Exit 1
}

# ============================================================================
# STEP 3: Wait for services to be healthy
# ============================================================================
Write-Host "`n⏳ Step 3: Waiting for services to be healthy..." -ForegroundColor Yellow

$serviceChecks = @{
    "ollama" = "http://localhost:11434/api/tags"
    "webhooks" = "http://localhost:8000/health"
}

foreach ($service in $serviceChecks.Keys) {
    $url = $serviceChecks[$service]
    $ready = $false
    
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $response = curl.exe -s -o /dev/null -w "%{http_code}" $url 2>&1
            if ($response -eq "200") {
                Write-Host "✅ $service is healthy" -ForegroundColor Green
                $ready = $true
                break
            }
        }
        catch {}
        
        Write-Host "   Checking $service... ($($i+1)/30)" -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
    
    if (-not $ready) {
        Write-Host "⚠️  $service may not be fully ready yet" -ForegroundColor Yellow
    }
}

# ============================================================================
# STEP 4: Show service status
# ============================================================================
Write-Host "`n📊 Step 4: Service Status" -ForegroundColor Yellow
docker compose ps

# ============================================================================
# STEP 5: Display connection info
# ============================================================================
Write-Host "`n🌐 Connection Information:" -ForegroundColor Cyan
Write-Host "   • Ollama AI Engine: http://localhost:11434" -ForegroundColor Green
Write-Host "   • WebHook API: http://localhost:8000" -ForegroundColor Green
Write-Host "   • Health Check: http://localhost:8000/health" -ForegroundColor Green
Write-Host "   • PostgreSQL: localhost:5432" -ForegroundColor Green
Write-Host "   • Redis: localhost:6379" -ForegroundColor Green

# ============================================================================
# STEP 6: Next steps
# ============================================================================
Write-Host "`n📋 Next Steps (Phase 1 Execution):" -ForegroundColor Cyan
Write-Host "   1. Read PHASE_1_STARTUP.md for week-by-week tasks" -ForegroundColor White
Write-Host "   2. Set up your development environment" -ForegroundColor White
Write-Host "   3. Install Python dependencies: pip install -r requirements.txt" -ForegroundColor White
Write-Host "   4. Run tests: pytest tests/ -v" -ForegroundColor White
Write-Host "   5. Start backend development" -ForegroundColor White

Write-Host "`n✅ Phase 1 Environment Ready!" -ForegroundColor Green
Write-Host "   Begin with: PHASE_1_STARTUP.md`n" -ForegroundColor Cyan
