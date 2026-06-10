# AI-Augmented Vulnerability Scanner - Docker Startup Checklist

## Phase 1: Docker Startup Validation (Do this in a NEW terminal while docker-compose up is running)

### Check 1: Verify Postgres is running
```powershell
# Try to connect to Postgres
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT 1;"
```

### Check 2: Verify Redis is running
```powershell
# Try to connect to Redis
docker-compose exec redis redis-cli ping
```

### Check 3: Verify Ollama is running
```powershell
# Try to get Ollama status
curl -s http://localhost:11434/api/tags | ConvertFrom-Json | ConvertTo-Json
```

### Check 4: Verify Migrations completed
```powershell
# Check if migrations service finished successfully
docker-compose logs migrations | Select-Object -Last 20
```

### Check 5: Verify Backend is running
```powershell
# Test the root endpoint
curl http://localhost:8000/
```

## Phase 2: Test Database & Scan Flow

### Test 1: Create a scan
```powershell
$headers = @{"Content-Type" = "application/json"}
$body = @{
    target_scope = "127.0.0.1/32"
    profile = "normal"
    authorized = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" `
    -Method POST `
    -Headers $headers `
    -Body $body

Write-Output "Scan created: $($response.id)"
$scanId = $response.id
```

### Test 2: Check scan status (wait 10-30 seconds then run)
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId" -Method GET | ConvertTo-Json
```

### Test 3: Check database directly
```powershell
# Query scans table
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM scans;"

# Query findings
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM findings;"

# Query audit logs
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM audit_logs;"
```

## Phase 3: Common Issues & Fixes

### Issue: "Ollama model not found"
**Fix:** Ollama needs to pull mistral:7b. Check logs:
```powershell
docker-compose logs ollama | Select-Object -Last 50
```

### Issue: "Database connection failed"
**Fix:** Check migrations service:
```powershell
docker-compose logs migrations
```

### Issue: "Celery worker not processing tasks"
**Fix:** Check worker logs:
```powershell
docker-compose logs worker | Select-Object -Last 50
```

### Issue: "Port 8000 already in use"
**Fix:** Kill existing processes:
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Phase 4: Next Steps
Once all checks pass:
1. Implement JWT authentication
2. Add WebSocket for real-time scan progress
3. Build ChromaDB RAG pipeline for CVE context
4. Create React dashboard
