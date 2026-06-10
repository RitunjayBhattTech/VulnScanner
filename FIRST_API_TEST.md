# Quick Test: First Scan API Call

Once docker-compose finishes and you see "Backend running on http://0.0.0.0:8000", run this in PowerShell:

```powershell
# 1. Create a scan for localhost (safe, won't actually scan anything dangerous)
$headers = @{"Content-Type" = "application/json"}
$body = @{
    target_scope = "127.0.0.1/32"
    profile = "normal"
    authorized = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" `
    -Method POST `
    -Headers $headers `
    -Body $body `
    -ErrorAction Stop

Write-Output "✅ Scan created successfully!"
Write-Output "Scan ID: $($response.id)"
Write-Output "Status: $($response.status)"
Write-Output "Target: $($response.target_scope)"

# Save the scan ID for next step
$scanId = $response.id
```

## 2. Wait 10-15 seconds, then check scan status

```powershell
# Get scan by ID
$scan = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId" `
    -Method GET `
    -ErrorAction Stop

Write-Output "Scan Status: $($scan.status)"
# Expected: "running" → "completed" after 30-60 seconds
```

## 3. List all scans

```powershell
$scans = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/" `
    -Method GET `
    -ErrorAction Stop

Write-Output "All scans:"
$scans | ConvertTo-Json -Depth 3
```

## 4. Check findings

```powershell
$findings = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId/findings" `
    -Method GET `
    -ErrorAction Stop

Write-Output "Findings ($($findings.Count) total):"
$findings | ForEach-Object {
    Write-Output "  Host: $($_.host):$($_.port) | Service: $($_.service) | Severity: $($_.ai_severity) | CVSS: $($_.ai_cvss_score)"
    if ($_.ai_false_positive_reasoning) {
        Write-Output "    FP Reasoning: $($_.ai_false_positive_reasoning)"
    }
    if ($_.ai_exploitation_notes) {
        Write-Output "    Exploitation: $($_.ai_exploitation_notes)"
    }
}
```

## 5. Check attack chains

```powershell
$chains = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId/chains" `
    -Method GET `
    -ErrorAction Stop

Write-Output "Attack Chains ($($chains.Count) total):"
$chains | ForEach-Object {
    Write-Output "  Description: $($_.chain_description)"
    Write-Output "  Severity: $($_.severity) | Likelihood: $($_.likelihood)"
    if ($_.mitre_technique_id) {
        Write-Output "  MITRE: $($_.mitre_technique_id)"
    }
}
```

## 6. Check database directly

```powershell
# Query scans table
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM scans;"

# Query findings with new AI columns
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT host, port, service, ai_severity, ai_cvss_score, ai_false_positive_reasoning FROM findings WHERE scan_id = $scanId;"

# Query attack chains
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM attack_chains WHERE scan_id = $scanId;"

# Query audit logs
docker-compose exec postgres psql -U scanner -d scanner -c "SELECT * FROM audit_logs;"
```

## Expected Results
- Scan will find some open ports on localhost (SSH on 22, etc. if running)
- Ollama will analyze them and assign CVSS scores, severity, false positive reasoning
- Attack chains will be identified if multiple related findings exist
- Results stored in Postgres with structured AI analysis
- All logged in audit_logs table