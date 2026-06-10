# Complete Execution Runbook

## Prerequisites
- Docker Desktop installed and running
- PowerShell (Windows) or bash (Linux/Mac)
- Ports 8000, 5173, 11434, 5432, 6379 free

---

## Step 1: Start Everything

```bash
# From Project03 directory
docker compose up --build -d
```

**What happens:**
- `postgres` — database starts (healthcheck: pg_isready)
- `redis` — cache starts (healthcheck: redis-cli ping)
- `ollama` — LLM server starts, healthchecked via `/api/tags`
- `migrations` — runs `alembic upgrade head` (creates both migration 001 + 002 tables)
- `backend` — FastAPI starts AFTER postgres+redis+ollama+migrations are ready
- `worker` — Celery starts AFTER postgres+redis+migrations
- `frontend` — React build + nginx serves on port 5173

**First-time setup** takes 2-5 minutes (Ollama must download the `mistral:7b` model).

---

## Step 2: Verify All Services Are Running

Open a **new** terminal (keep the docker one running):

```powershell
# 1. Check all containers are "running" or "completed"
docker ps

# Expected output: 6 containers (postgres, redis, ollama, migrations, backend, worker, frontend)
```

```powershell
# 2. Check Postgres
docker compose exec postgres psql -U scanner -d scanner -c "SELECT 'Postgres OK' AS status;"
# Expected: "Postgres OK"
```

```powershell
# 3. Check Redis
docker compose exec redis redis-cli ping
# Expected: "PONG"
```

```powershell
# 4. Check Ollama
curl -s http://localhost:11434/api/tags | python -c "import sys,json; data=json.load(sys.stdin); print(f'Ollama OK - {len(data.get(\"models\",[]))} models')"
# Expected: "Ollama OK - 1 models" (mistral:7b should be pulled)
# If 0 models, run: docker compose exec ollama ollama pull mistral:7b
```

```powershell
# 5. Check Backend API
curl http://localhost:8000/
# Expected: {"service":"ai-augmented-vuln-scanner","version":"ai-augmented-vuln-scanner","status":"ready"}
```

```powershell
# 6. Check Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/
# Expected: 200
```

```powershell
# 7. Check Migrations ran (should show 4 tables)
docker compose exec postgres psql -U scanner -d scanner -c "\dt"
# Expected: attack_chains, audit_logs, false_positive_feedback, findings, scans, alembic_version
```

---

## Step 3: Launch Your First Scan

### Option A: Via PowerShell

```powershell
$headers = @{"Content-Type" = "application/json"}
$body = @{
    target_scope = "127.0.0.1/32"
    profile = "normal"
    authorized = $true
} | ConvertTo-Json

$scan = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" `
    -Method POST `
    -Headers $headers `
    -Body $body

Write-Output "✅ Scan created! ID: $($scan.id) | Status: $($scan.status)"
$scanId = $scan.id
```

### Option B: Via curl

```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Content-Type: application/json" \
  -d '{"target_scope":"127.0.0.1/32","profile":"normal","authorized":true}'
```

---

## Step 4: Monitor Scan Progress

### Watch the worker process findings:

```powershell
# In a new terminal — tail the worker logs
docker compose logs -f worker
```

You'll see logs like:
```
Starting scan job 1 for target 127.0.0.1/32
Nmap scan completed with X findings
AI analysis completed: X enriched findings, Y attack chains
Persisted X findings and Y attack chains for scan 1
Scan job 1 completed successfully with X findings
```

### Check status via API:

```powershell
# After 10-30 seconds, check if complete
$status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId" -Method GET
Write-Output "Status: $($status.status)"
```

---

## Step 5: View Results

### A) Via Dashboard (http://localhost:5173)

1. Open http://localhost:5173
2. Click on your scan row (Scan #1)
3. You'll see:
   - **Severity distribution** cards (critical/high/medium/low/info counts)
   - **Findings tab** — table with:
     - Host, Port, Service
     - Severity badge (color-coded)
     - CVSS score bar (visual gauge)
     - False Positive reasoning column
     - Exploitation notes column
   - **Attack Chains tab** — if the AI found multi-step chains:
     - Chain description
     - Severity + Likelihood badges
     - MITRE ATT&CK ID
     - Hosts involved in the chain

### B) Via API

```powershell
# List all scans
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" -Method GET | ConvertTo-Json

# Get findings
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId/findings" -Method GET | ConvertTo-Json -Depth 3

# Get attack chains
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId/chains" -Method GET | ConvertTo-Json -Depth 3
```

### C) Via Database

```powershell
# All scans
docker compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM scans;"

# Findings with AI analysis
docker compose exec postgres psql -U scanner -d scanner -c "SELECT host, port, service, ai_severity, ai_cvss_score, LEFT(ai_false_positive_reasoning, 80) AS fp_reasoning FROM findings;"

# Attack chains
docker compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM attack_chains;"

# Audit trail
docker compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM audit_logs;"
```

---

## Step 6: Test the Full API Surface

```powershell
# List scans (with pagination)
Invoke-RestMethod "http://localhost:8000/api/v1/scans/?skip=0&limit=10"

# Get single scan
Invoke-RestMethod "http://localhost:8000/api/v1/scans/1"

# Get findings (paginated)
Invoke-RestMethod "http://localhost:8000/api/v1/scans/1/findings?skip=0&limit=100"

# Get attack chains
Invoke-RestMethod "http://localhost:8000/api/v1/scans/1/chains"
```

---

## Step 7: Verification Checklist

| Check | Expected | How |
|-------|----------|-----|
| Docker containers running | 7 containers | `docker ps` |
| Backend health | `{"status":"ready"}` | `curl http://localhost:8000/` |
| Dashboard loads | HTTP 200 | Browser to http://localhost:5173 |
| Scan creates | HTTP 202 + scan ID | POST /api/v1/scans/ |
| Scan completes | Status "completed" | GET /api/v1/scans/{id} |
| Findings have AI data | Severity + CVSS + FP reasoning | Dashboard or API |
| Attack chains exist | At least 0 chains | Dashboard Chains tab |
| Audit log | scan_started → scan_completed | DB query |
| Frontend shows all data | Scan row clickable → detail page | Browser navigation |

---

## Common Issues & Fixes

### "Ollama model not found"
```powershell
# Pull model manually
docker compose exec ollama ollama pull mistral:7b
# Then restart backend + worker
docker compose restart backend worker
```

### "Celery worker not processing"
```powershell
docker compose logs worker
# If you see connection errors, restart redis
docker compose restart redis worker
```

### "Port already in use"
```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :5173
# Kill the PID
taskkill /PID <PID> /F
```

### "Migrations failed"
```powershell
docker compose logs migrations
# If error, check postgres is healthy:
docker compose exec postgres pg_isready -U scanner
```

### "Frontend shows blank page"
```powershell
# Check nginx logs
docker compose logs frontend
# Try rebuilding
docker compose build frontend
docker compose up -d frontend
```

---

## End-to-End Quick Test (Single Script)

Save as `test.ps1` and run:

```powershell
Write-Output "=== 1. Check backend ==="
curl http://localhost:8000/

Write-Output "`n=== 2. Create scan ==="
$scan = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"target_scope":"127.0.0.1/32","profile":"normal","authorized":true}'
Write-Output "Scan ID: $($scan.id) Status: $($scan.status)"

Write-Output "`n=== 3. Wait 15 seconds ==="
Start-Sleep -Seconds 15

Write-Output "`n=== 4. Check scan status ==="
$status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$($scan.id)"
Write-Output "Status: $($status.status)"

Write-Output "`n=== 5. Get findings ==="
$findings = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$($scan.id)/findings"
Write-Output "Found $($findings.Count) findings"
$findings | ForEach-Object { Write-Output "  $($_.host):$($_.port) $($_.service) | Severity: $($_.ai_severity) CVSS: $($_.ai_cvss_score)" }

Write-Output "`n=== 6. Get attack chains ==="
$chains = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$($scan.id)/chains"
Write-Output "Found $($chains.Count) attack chains"
$chains | ForEach-Object { Write-Output "  $($_.chain_description) [Severity: $($_.severity) | MITRE: $($_.mitre_technique_id)]" }

Write-Output "`n=== 7. Dashboard ==="
Write-Output "Open http://localhost:5173 in your browser"